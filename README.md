Python-JRPC
===========

A Python remote procedure call framework that uses JSON RPC v2.0

Install using pip:

```
pip install python-jrpc
```

# Socket Based Usage

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

# Web Based (Flask) Usage

A recent addition to Python JRPC offers Flask integration.
Using this feature, client side Javascript can easily call webservice API methods.

## Flask App
```python
from jrpc.web import *
import jrpc.service
from flask import Flask, render_template

app = Flask(__name__)

class WebService(JRPCBlueprint):
    def __init__(self):
        JRPCBlueprint.__init__(self, "service", __name__, url_prefix="/api")

    @jrpc.service.method(path = "/echo/<name>")
    def echo(self, text, prefix = "Hello from", name = ""):
        return {"subject": prefix + " " + name, "message": text}

app.register_blueprint(WebService())

@app.route('/')
def index():
    return render_template("index.html")
app.run(host='0.0.0.0', port=8080, debug=True)
```

## Index.html Javascript

```javascript
jrpc("/api").done(function(api) {
    api.echo({name: "Python JRPC", text: "Now with more Flask"}).done(function(result) {
        $("#result").text(JSON.stringify(result));
    });
});
```

## Result
```json
{"subject":"Hello from Python JRPC", "message":"Now with more Flask"}
```

# Why Use It?

Python-JRPC takes all of the boiler-plate code out of your network applications.
Forget reading through socket documentation and developing your own message formats.
All you need to do is write your Python server/client logic and let Python-JRPC handle the networking for you.
Here's what you get:

- Remote method call with JSON serializable parameters/return values
- Synchronization/thread safety in servers/clients
- Remote exception passing (When calling a remote method in a client, exceptions thrown by the server code will be thrown locally!)
- Simplified Flask applications, client side Javascript can easily call webservice API methods
