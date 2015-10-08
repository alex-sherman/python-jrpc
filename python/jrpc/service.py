import threading
import socket
import logging
import time
import exception
import json
import message
import inspect

class jrpc_object(object):
    def __init__(self, instance = None):
        self.instance = instance

class method(jrpc_object):
    def __init__(self, remote_func):
        jrpc_object.__init__(self)
        self.remote_func = remote_func
        self.instance = None
    def __call__(self, *args, **kwargs):
        if self.instance == None: raise exception.JRPCError("Method instance not set before being called")
        return self.remote_func(self.instance, *args, **kwargs)

class rpc_property(property, jrpc_object):
    def __init__(self, getter):
        property.__init__(self, getter)
        jrpc_object.__init__(self)

class RemoteObject(jrpc_object):
    def __init__(self):
        jrpc_object.__init__(self, self)
        self.jrpc_objects = {member[0] : member[1] for member in inspect.getmembers(self.__class__) if
        isinstance(member[1], jrpc_object)}
        for jrpc_method in self.jrpc_objects.values():
            jrpc_method.instance = self

    def get_method(self, path):
        if path[0] not in self.jrpc_objects:
            return None
        output = self.jrpc_objects[path[0]]
        if len(path) == 1:
            if not isinstance(output, method):
                return None
            return output
        return output.get_method(path[1:])


class SocketObject(threading.Thread, RemoteObject):
    def __init__(self, port, host = '', debug = False, timeout = 1, reuseaddr = True):
        threading.Thread.__init__(self)
        RemoteObject.__init__(self)
        self.lock = threading.Lock()
        self._log = logging.Logger(debug)
        self.running = False
        self.registered = False
        self.port = port
        self.host = host
        self.reuseaddr = reuseaddr
        socket.setdefaulttimeout(timeout)
        self.responders = []

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
        if self.reuseaddr:
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.host, self.port))
        self.port = self.s.getsockname()[1]              
        self.s.listen(1)
        self._log.info("Service listening on port {0}".format(self.port))

    def run(self):
        while self.running:
            try:
                conn, addr = self.s.accept()
                self._log.info("Got connection from {0}".format(addr))
                responder = ServiceResponder(self, conn, addr, self._log)
                responder.start()
                self.responders.append(responder)
            except socket.timeout:
                continue
            except Exception as e:
                self._log.error("An error occured: {0}".format(e))
                self.close()
            
    def close(self):
        for responder in self.responders:
            responder.close()
        for name in self.jrpc_objects:
            service = self.jrpc_objects[name]
            if isinstance(service, SocketObject):
                service.close()
        if not self.running: return
        self.running = False
        if self.s != None:
            self._log.info("Closing socket")
            self.s.close()
            del self.s

class ServiceResponder(threading.Thread):
    def __init__(self, service_obj, socket, addr, log):
        threading.Thread.__init__(self)
        self.service_obj = service_obj
        self.socket = socket
        self.addr = addr
        self._log = log
        self.running = True
    def run(self):
        recvd = ""
        while self.running:
            try:
                msg = message.deserialize(self.socket)
                if type(msg) is message.Request:
                    response = message.Response(msg.id)
                    method_target = self.service_obj.get_method(msg.method.split('.'))
                    if method_target != None:
                        self.service_obj.lock.acquire()
                        try:
                            response.result = method_target(*msg.params[0], **msg.params[1])
                            self._log.info("{0} called \"{1}\" returning {2}".format(self.addr, msg.method, json.dumps(response.result)))
                        except Exception as e:
                            self._log.info("An exception occured while calling {0}: {1}".format(msg.method, e))
                            response.error = exception.exception_to_error(e)
                        finally:
                            self.service_obj.lock.release()
                    else:
                        response.error = {"code": -32601, "message": "No such method {0}".format(msg.method)}
                    
                    response.serialize(self.socket)
                else:
                    self._log.info("Got a message of uknown type")
            except socket.timeout:
                continue
            except Exception as e:
                self._log.info("Client socket exception: {0}".format(e))
                break
        self.close()

    def close(self):
        if not self.running: return
        self.running = False
        if self.socket != None:
            self._log.info("Client disconnected {0}".format(self.addr))
            self.socket.close()
            del self.socket

    def __del__(self):
        self.close()
        del self

class CallBack(object):
    def __init__(self, procedure_name, proxy):
        self.proxy = proxy
        self.procedure_name = procedure_name
    def __getattr__(self, name):
        return CallBack(self.procedure_name + "." + name, self.proxy)
    def __call__(self, *args, **kwargs):
        return self.proxy.rpc(self.procedure_name, args, kwargs)

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

    def rpc(self, remote_procedure, args, kwargs):
        self.lock.acquire()
        try:
            msg = message.Request(self.next_id, remote_procedure)
            self.next_id += 1
            msg.params = [args, kwargs]

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
        if "socket" in self.__dict__ and self.socket != None:
            self.socket.close()
        self.socket = None
        
    def __del__(self):
        self.close()
        del self
        
    def __getattr__(self, name):
        return CallBack(name, self)
