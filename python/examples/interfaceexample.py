#!/usr/bin/python
import jrpc
import json
from jrpc.interface import STRING, NUMBER

class RGBCOLOR(jrpc.interface.InterfaceType):
    r = NUMBER(0, 255)
    g = NUMBER(0, 255)
    b = NUMBER(0, 255)

class DUALCOLOR(jrpc.interface.InterfaceType):
    color1 = RGBCOLOR()
    color1.resolution = 20
    color2 = RGBCOLOR()
    weight = NUMBER(0, 1)

@jrpc.interface.InterfaceObject
class SubInterface(jrpc.service.RemoteObject):

    @jrpc.interface.method(DUALCOLOR())
    @jrpc.service.method
    def colorLerp(self, colors):
        return "Subinterface: " + msg

@jrpc.interface.InterfaceObject
class SimpleService(jrpc.service.SocketObject):
    sub = SubInterface()

    @jrpc.interface.method(STRING())
    @jrpc.service.method
    def echo(self, msg):
        return msg

    @jrpc.interface.method(RGBCOLOR(), NUMBER(0, 10))
    @jrpc.service.method
    def blink(self, color, count):
        pass

if __name__ == "__main__":
    server = SimpleService(50001, debug = True)

    #print json.dumps(server.GetInterface(), indent = 4)
    print server.color
    server.run_wait()
