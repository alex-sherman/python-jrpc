#!/usr/bin/python
import jrpc

server = None
server = jrpc.service.SocketProxy(50001) #The server's listening port
print server.echo("Hello World!")
