#!/usr/bin/python
import jrpc

class TestService(jrpc.service.Object):
    def __init__(self):
        jrpc.service.Object.__init__(self, "test-service2", True)

    @jrpc.service.method
    def test(self):
        raise Exception("DBUS wouldn't handle this")
        return "DBUS can suck two dicks"

test = TestService()
test.run_wait()

