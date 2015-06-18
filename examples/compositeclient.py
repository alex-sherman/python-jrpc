#!/usr/bin/python
import jrpc

server = None
server = jrpc.service.SocketProxy(50003) #The server's listening port
print server.simple.echo("Hello World!")
print server.exception.echo("Hello World!")