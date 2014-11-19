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

class Object(threading.Thread):
    remote_functions = []
    def __init__(self, service_name, debug = False):
        threading.Thread.__init__(self)
        self.log = logging.Logger(debug)
        self.running = True
        self.service_name = service_name
        self.daemon_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.registered = False
        self.port = 0
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

    def register(self):
        try:
            daemon_proxy = SocketProxy(50007)
            daemon_proxy.register_service(self.service_name, self.port)
            self.registered = True
        except:
            self.registered = False
        if self.registered:
            self.log.info("Registered service {0} with daemon".format(self.service_name))
        else:
            self.log.error("Failed to register service {0} with daemon".format(self.service_name))
        return self.registered

    def run(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('', self.port))
        self.port = self.s.getsockname()[1]              
        self.s.listen(1)
        self.log.info("Service listening on port {0}".format(self.port))
        while self.running:
            try:
                if not self.registered:
                    self.register()
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
                msg = message.Message()
                if not msg.deserialize(self.socket):
                    self.log.info("Message deserialization failed")
                    continue
                else:
                    response = message.Message({})
                    if msg.obj["procedure"] in self.service_obj.jbus_methods:
                        try:
                            response.obj["data"] = self.service_obj.jbus_methods[msg.obj["procedure"]](msg.obj["args"])
                            response.obj["status"] = 200
                        except Exception as e:
                            response.obj["status"] = 500
                            response.obj["data"] = (str(type(e)), e.message)
                    else:
                        response.obj["status"] = 404
                    
                    response.serialize(self.socket)
            except socket.timeout:
                continue
            except exception.MessageException:
                break
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

class CallBack(object):
    def __init__(self, procedure_name, proxy):
        self.proxy = proxy
        self.procedure_name = procedure_name
    def __call__(self, *args):
        return self.proxy.rpc(self.procedure_name, args)

class SocketProxy(object):
    def __init__(self, port):
        socket.setdefaulttimeout(1)
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(('localhost', port))
        except Exception as e:
            raise exception.ServiceException("Failed to connected to service", e)

    def rpc(self, remote_procedure, args):
        msg = message.Message({"procedure": remote_procedure, "args": args})
        msg.serialize(self.socket)
        response = message.Message()
        response.deserialize(self.socket)
        status = response.obj["status"]
        if status == 200:
            return response.obj["data"]
        if status == 404:
            raise exception.ServiceException("No such method {0}".format(remote_procedure), AttributeError)
        if status == 500:
            raise exception.ServiceException("An exception occured of type {0} with message: {1}"
                                             .format(response.obj["data"][0], response.obj["data"][1]), Exception)
        return response.obj["data"]

    def close(self):
        self.socket.close()

    def __del__(self):
        self.close()
        del self.socket
        
    def __getattr__(self, name):
        return CallBack(name, self)

class Proxy(SocketProxy):
    def __init__(self, service_name):
        self.service_name = service_name
        daemon_proxy = SocketProxy(50007)
        try:
            self.service_port = daemon_proxy.get_service(service_name)
        except Exception as e:
            daemon_proxy.close()
            raise e
        daemon_proxy.close()
        SocketProxy.__init__(self, self.service_port)
        
        
