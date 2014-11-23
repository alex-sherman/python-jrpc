#!/usr/bin/python
import jrpc

class TestService(jrpc.service.SocketObject):
    @jrpc.service.method
    def test(self):
        raise ZeroDivisionError("This will get thrown on the client if it calls this method")

test = TestService(50008, debug = True)
test.run_wait()
