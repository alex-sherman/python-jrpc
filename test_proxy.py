#!/usr/bin/python
import jbus
try:
    test = jbus.service.Proxy("test-service")
    print test.test()
    del test
except Exception as e:
    print e
try:
    test = jbus.service.Proxy("test-service2")
    print test.test()
    del test
except Exception as e:
    print e

