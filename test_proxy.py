#!/usr/bin/python
import jbus

test = jbus.service.Proxy("test-service")
print test.test()
