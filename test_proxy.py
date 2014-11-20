#!/usr/bin/python
import jrpc
try:
    test = None
    test = jrpc.service.Proxy("test-service")
    print test.test()
    test.herp()
except Exception as e:
    print e
finally:
    del test
try:
    test = None
    test = jrpc.service.Proxy("test-service2")
    print test.test()
except Exception as e:
    print e
finally:
    del test

