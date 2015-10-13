import threading
import socket
import logging
import time
import exception
import json
import message
import inspect
import types
import reflection
from reflection import RPCType

def method(*args):
    if(len(args) > 0 and isinstance(args[0], types.FunctionType)):
        args[0].jrpc_method = True
        argSpec = inspect.getargspec(args[0])
        defaults = len(argSpec[3]) if argSpec[3] != None else 0
        argNames = argSpec[0][1:]
        argTypes = args[1:] if len(args) > 1 else []
        argCount = len(argNames)
        while len(argTypes) < len(argNames):
            argTypes.append(reflection.UNKNOWN())
        #Mark any parameters with defaults as optional
        if defaults > 0:
            for optionalArg in argTypes[-defaults:]:
                optionalArg.optional = True
        args[0].arguments = zip(argNames, argTypes)
        return args[0]
    return lambda func: method(func, *args)

class rpc_property(property):
    def __init__(self, getter):
        property.__init__(self, getter)
        jrpc_object.__init__(self)

class RemoteObject(object):
    def _get_methods(self):
        return dict([method for method in inspect.getmembers(self) if hasattr(method[1], "jrpc_method") and method[1].jrpc_method])
    def _get_objects(self):
        return dict([obj for obj in inspect.getmembers(self) if isinstance(obj[1], RemoteObject)])

    def get_method(self, path):
        methods = self._get_methods()
        if path[0] in methods:
            return methods[path[0]]
        objects = self._get_objects()
        if len(path) > 1 and path[0] in objects:
            return objects.get_method(path[1:])
        return None

    @method
    def Reflect(self, types = {}):
        """Reflect returns optional information about
        the remote object's endpoints. The author may not
        specify any reflection information, in which case,
        this will return mostly empty. If specified, this
        method will return custom types, method signatures
        and sub object reflection information
        """
        types = dict(types)
        selfTypes = {}
        methods = {}
        for name, method in self._get_methods().iteritems():
            methods[name] = RPCType.ToDict(method.arguments)
            selfTypes.update(RPCType.ToTypeDef(method.arguments, types))
        interfaces = dict([(name, obj.Reflect(types)) for name, obj in self._get_objects().iteritems()])
        return {
            "types": selfTypes,
            "methods": methods,
            "interfaces": interfaces
        }

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
