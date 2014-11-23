#!/usr/bin/python
import jrpc

class EchoService(jrpc.service.SocketObject):
    @jrpc.service.method
    def echo(self, msg):
        return msg

test = EchoService(50009, debug = True)
test.run_wait()
