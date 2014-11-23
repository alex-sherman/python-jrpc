#!/usr/bin/python
import jrpc

class SimpleService(jrpc.service.SocketObject):
    @jrpc.service.method
    def echo(self, msg):
        return msg

server = SimpleService(50001, debug = True) #Include the listening port
server.run_wait()
