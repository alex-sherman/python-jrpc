#!/usr/bin/python
import jrpc
try:
    test = None
    test = jrpc.service.SocketProxy(50009)
    print test.echo("Hello World!")
except Exception as e:
    print type(e), e
finally:
    del test
try:
    test = None
    test = jrpc.service.SocketProxy(50008)
    print test.test()
except Exception as e:
    print type(e), e
finally:
    del test
