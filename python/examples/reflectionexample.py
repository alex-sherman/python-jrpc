#!/usr/bin/python
import jrpc
import json
from jrpc.reflection import STRING, NUMBER

class RGBCOLOR(jrpc.reflection.RPCType):
    r = NUMBER(0, 255)
    g = NUMBER(0, 255)
    b = NUMBER(0, 255)

class DUALCOLOR(jrpc.reflection.RPCType):
    color1 = RGBCOLOR()
    color1.resolution = 20
    color2 = RGBCOLOR()
    weight = NUMBER(0, 1)

class SubInterface(jrpc.service.RemoteObject):

    @jrpc.service.method(DUALCOLOR())
    def colorLerp(self, color):
        return "Subinterface: " + msg

class SimpleService(jrpc.service.SocketObject):
    def __init__(self, *args, **kwargs):
        jrpc.service.SocketObject.__init__(self, *args, **kwargs)
        self.sub = SubInterface()

    @jrpc.service.method(STRING())
    def echo(self, msg):
        return msg

    @jrpc.service.method(RGBCOLOR(), NUMBER(0, 10))
    def blink(self, color, count):
        pass

if __name__ == "__main__":
    server = SimpleService(50001, debug = True)

    print json.dumps(server.Reflect(), indent = 4)
