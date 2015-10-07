#!/usr/bin/python
import jrpc

class ExceptionService(jrpc.service.SocketObject):
    @jrpc.service.method
    def echo(self, msg):
        raise ZeroDivisionError("This will get thrown on the client if it calls this method")

if __name__ == "__main__":
    test = ExceptionService(50001, debug = True)
    test.run_wait()
