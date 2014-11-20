#!/usr/bin/python
import jbus

class TestService(jbus.service.Object):
    def __init__(self):
        jbus.service.Object.__init__(self, "test-service", True)

    @jbus.service.method
    def test(self):
        return "DBUS can suck a dick"

test = TestService()
test.run_wait()
