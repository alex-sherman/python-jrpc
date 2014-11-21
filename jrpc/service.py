import threading
import socket
import logging
import time
import exception
import json
import message
import inspect
from nameservice import NameServiceResponder

class method(object):
    def __init__(self, remote_func):
        self.remote_func = remote_func
        self.instance = None
    def __call__(self, args):
        if self.instance == None: raise exception.MethodException("Method instance not set before being called")
        return self.remote_func(self.instance, *args)

class SocketObject(threading.Thread):
    remote_functions = []
    def __init__(self, port, debug = False):
        threading.Thread.__init__(self)
        self.log = logging.Logger(debug)
        self.running = True
        self.registered = False
        self.port = port
        socket.setdefaulttimeout(1)
        self.responders = []
        self.jbus_methods = {member[0] : member[1] for member in inspect.getmembers(self.__class__) if type(member[1]) is method}
        for jbus_method in self.jbus_methods.values():
            jbus_method.instance = self

    def run_wait(self):
        self.start()
        try:
            while self.running:
                time.sleep(1)
        except:
            self.close()

    def pre_run(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('', self.port))
        self.port = self.s.getsockname()[1]              
        self.s.listen(1)
        self.log.info("Service listening on port {0}".format(self.port))

    def run(self):
        self.pre_run()
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

class Object(SocketObject):
    def __init__(self, service_name, debug = False):
        SocketObject.__init__(self, 0, debug)
        
        self.service_name = service_name
        self.name_service_thread = None
    def pre_run(self):
        SocketObject.pre_run(self)
        self.name_service_thread = NameServiceResponder(self, self.log)
        self.name_service_thread.start()

    def close(self):
        if self.name_service_thread != None:
            nst = self.name_service_thread
            self.name_service_thread = None
            nst.close()
        SocketObject.close(self)
        

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
                        try:
                            response.result = self.service_obj.jbus_methods[msg.method](msg.params)
                        except Exception as e:
                            self.log.info("An exception occured while calling {0}: {1}".format(msg.method, e))
                            response.error = exception.exception_to_error(e)
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
    def __init__(self, port, socktype = socket.SOCK_STREAM):
        socket.setdefaulttimeout(1)
        self.socket = None
        self.next_id = 1
        try:
            self.socket = socket.socket(socket.AF_INET, socktype)
            self.socket.connect(('localhost', port))
        except Exception as e:
            raise exception.JRPCError("Failed to connected to service", e)

    def rpc(self, remote_procedure, args):
        msg = message.Request(self.next_id, remote_procedure)
        self.next_id += 1
        msg.params = args
        msg.serialize(self.socket)
        response = message.deserialize(self.socket)
        if not type(response) is message.Response:
            raise exception.JRPCError("Received a message of uknown type")
        if response.id != msg.id: raise exception.JRPCError(0, "Got a response for a different request ID")
        if hasattr(response, "result"):
            return response.result
        elif hasattr(response, "error"):
            raise exception.JRPCError.from_error(response.error)
        raise Exception("Deserialization failure!!")

    def close(self):
        if self.socket != None:
            self.socket.close()
        self.socket = None
        
    def __del__(self):
        self.close()
        del self
        
    def __getattr__(self, name):
        return CallBack(name, self)

class Proxy(SocketProxy):
    def __init__(self, service_name):
        socket.setdefaulttimeout(1)
        self.service_name = service_name
        self.socket = None
        
        daemon_proxy = SocketProxy(50007, socket.SOCK_DGRAM)
        try:
            self.service_port = daemon_proxy.get_service(service_name)
        except socket.error:
            raise exception.JRPCError("Service {0} isn't running".format(service_name))
        except socket.timeout:
            raise exception.JRPCError("Service {0} timed out".format(service_name))
        except Exception as e:
            raise e
        finally:
            daemon_proxy.close()
        SocketProxy.__init__(self, self.service_port)
        
        
