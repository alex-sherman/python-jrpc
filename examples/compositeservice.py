#!/usr/bin/python
import jrpc
import simpleservice, exceptionservice

class CompositeService(jrpc.service.SocketObject):
    def __init__(self, port = 50003, debug = True):
        jrpc.service.SocketObject.__init__(self, port, debug = debug)
        self.simple = simpleservice.SimpleService(0, debug)
        self.exception = exceptionservice.ExceptionService(0, debug)

if __name__ == "__main__":
    server = CompositeService() #Include the listening port
    server.run_wait()