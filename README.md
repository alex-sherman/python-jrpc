Python-JRPC
===========

A Python remote procedure call framework that uses JSON RPC v2.0

Install using pip:

```
pip install python-jrpc
```

# Usage

Python-JRPC allows programmers to create powerful client/server programs with very little code.
Here's an example of a server and client:

## Server

```python
import jrpc

class SimpleService(jrpc.service.SocketObject):
    @jrpc.service.method
    def echo(self, msg):
        return msg

server = SimpleService(50001) #Include the listening port
server.run_wait()
```

## Client

```python
import jrpc

server = None
server = jrpc.service.SocketProxy(50001) #The server's listening port
print server.echo("Hello World!")
```

# Why Use It?

Python-JRPC takes all of the boiler-plate code out of your network applications.
Forget reading through socket documentation and developing your own message formats.
All you need to do is write your Python server/client logic and let Python-JRPC handle the networking for you.
Here's what you get:

- Remote method call with JSON serializable parameters/return values
- Synchronization/thread safety in servers/clients
- Remote exception passing (When calling a remote method in a client, exceptions thrown by the server code will be thrown locally!)
