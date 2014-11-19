#!/usr/bin/python
import jbus

class TestService(jbus.service.Object):
    def __init__(self):
        jbus.service.Object.__init__(self, "testservice", True)

test = TestService()
test.run_wait()

