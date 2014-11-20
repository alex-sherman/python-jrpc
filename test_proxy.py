#!/usr/bin/python
import jbus

test = jbus.service.Proxy("test-service2")
print test.test()
