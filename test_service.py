#!/usr/bin/python
import jrpc

class TestService(jrpc.service.Object):
    def __init__(self):
        jrpc.service.Object.__init__(self, "test-service", True)

    @jrpc.service.method
    def test(self):
        return "DBUS can suck a dick"

test = TestService()
test.run_wait()
