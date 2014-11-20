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
    test = jrpc.service.SocketProxy(50008)
    print test.test()
except ArithmeticError as e:
    print "Fancy exceptions"
except Exception as e:
    print type(e), e
finally:
    del test

