#!/usr/bin/python
import jbus

class TestService(jbus.service.Object):
    def __init__(self):
        jbus.service.Object.__init__(self, "test-service2", True)

    @jbus.service.method
    def test(self):
        raise Exception("DBUS wouldn't handle this")
        return "DBUS can suck two dicks"

test = TestService()
test.run_wait()

