#!/usr/bin/python
import jrpc

class TestService(jrpc.service.SocketObject):
    def __init__(self):
        jrpc.service.SocketObject.__init__(self, 50008, True)

    @jrpc.service.method
    def test(self):
        raise ZeroDivisionError("DBUS wouldn't handle this")
        return "DBUS can suck two dicks"

test = TestService()
test.run_wait()

