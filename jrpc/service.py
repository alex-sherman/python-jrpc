import threading
import socket
import logging
import time
import exception
import json
import message
import inspect

class method(object):
    def __init__(self, remote_func):
        self.remote_func = remote_func
        self.instance = None
    def __call__(self, args):
        if self.instance == None: raise exception.MethodException("Method instance not set before being called")
        return self.remote_func(self.instance, *args)

class SocketObject(threading.Thread):
    remote_functions = []
    def __init__(self, port, host = '', debug = False, timeout = 1):
        threading.Thread.__init__(self)
        self.lock = threading.Lock()
        self.log = logging.Logger(debug)
        self.running = False
        self.registered = False
        self.port = port
        self.host = host
        socket.setdefaulttimeout(timeout)
        self.responders = []
        self.jbus_methods = {member[0] : member[1] for member in inspect.getmembers(self.__class__) if type(member[1]) is method}
        for jbus_method in self.jbus_methods.values():
            jbus_method.instance = self

    def run_wait(self):
        try:
            self.pre_run()
            self.running = True
            self.start()
            while self.running:
                time.sleep(1)
        finally:
            self.close()

    def pre_run(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((self.host, self.port))
        self.port = self.s.getsockname()[1]              
        self.s.listen(1)
        self.log.info("Service listening on port {0}".format(self.port))

    def run(self):
        while self.running:
            try:
                conn, addr = self.s.accept()
                self.log.info("Got connection from {0}".format(addr))
                responder = ServiceResponder(self, conn, addr, self.log)
                responder.start()
                self.responders.append(responder)
            except socket.timeout:
                continue
            except Exception as e:
                self.log.error("An error occured: {0}".format(e))
                self.close()
            
    def close(self):
        for responder in self.responders:
            responder.close()
        if not self.running: return
        self.running = False
        if self.s != None:
            self.log.info("Closing socket")
            self.s.close()
            del self.s

class ServiceResponder(threading.Thread):
    def __init__(self, service_obj, socket, addr, log):
        threading.Thread.__init__(self)
        self.service_obj = service_obj
        self.socket = socket
        self.addr = addr
        self.log = log
        self.running = True
    def run(self):
        recvd = ""
        while self.running:
            try:
                msg = message.deserialize(self.socket)
                if type(msg) is message.Request:
                    response = message.Response(msg.id)
                    if msg.method in self.service_obj.jbus_methods:
                        self.service_obj.lock.acquire()
                        try:
                            response.result = self.service_obj.jbus_methods[msg.method](msg.params)
                            self.log.info("{0} called \"{1}\" returning {2}".format(self.addr, msg.method, json.dumps(response.result)))
                        except Exception as e:
                            self.log.info("An exception occured while calling {0}: {1}".format(msg.method, e))
                            response.error = exception.exception_to_error(e)
                        finally:
                            self.service_obj.lock.release()
                    else:
                        response.error = {"code": -32601, "message": "No such method {0}".format(msg.method)}
                    
                    response.serialize(self.socket)
                else:
                    self.log.info("Got a message of uknown type")
            except socket.timeout:
                continue
            except Exception as e:
                self.log.info("Client socket exception: {0}".format(e))
                break
        self.close()

    def close(self):
        if not self.running: return
        self.running = False
        if self.socket != None:
            self.log.info("Client disconnected {0}".format(self.addr))
            self.socket.close()
            del self.socket

    def __del__(self):
        self.close()
        del self

class CallBack(object):
    def __init__(self, procedure_name, proxy):
        self.proxy = proxy
        self.procedure_name = procedure_name
    def __call__(self, *args):
        return self.proxy.rpc(self.procedure_name, args)

class SocketProxy(object):
    def __init__(self, port, host = 'localhost', socktype = socket.SOCK_STREAM, timeout = 1):
        socket.setdefaulttimeout(timeout)
        self.socket = None
        self.next_id = 1
        self.lock = threading.Lock()
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socktype)
        try:
            self.socket.connect((host, port))
        except socket.error as e:
            if e.args[0] != 111:
                raise exception.JRPCError("An error occured", e)

    def rpc(self, remote_procedure, args):
        self.lock.acquire()
        try:
            msg = message.Request(self.next_id, remote_procedure)
            self.next_id += 1
            msg.params = args

            # Attempt sending and connection if neccessary
            try:
                msg.serialize(self.socket)
            except socket.error as e:
                # Connection error, try to connect and send
                if e.args[0] == 32:
                    try:
                        self.socket.connect((self.host, self.port))
                        msg.serialize(self.socket)
                    except socket.error as e:
                        raise exception.JRPCError("Unable to connect to remote service", e)
                else: raise e

            response = message.deserialize(self.socket)
            if not type(response) is message.Response:
                raise exception.JRPCError("Received a message of uknown type")
            if response.id != msg.id: raise exception.JRPCError(0, "Got a response for a different request ID")
            if hasattr(response, "result"):
                return response.result
            elif hasattr(response, "error"):
                raise exception.JRPCError.from_error(response.error)
            raise Exception("Deserialization failure!!")
        finally:
            self.lock.release()

    def close(self):
        if self.socket != None:
            self.socket.close()
        self.socket = None
        
    def __del__(self):
        self.close()
        del self
        
    def __getattr__(self, name):
        return CallBack(name, self)
