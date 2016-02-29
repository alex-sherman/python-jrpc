from jrpc.web import *
from jrpc.service import method
from jrpc.reflection import *
from flask import Flask

class SubService(RemoteObject):
    @method(STRING(), path = "faff/<text>")
    def faff(self, text):
        return text[::-1]

class WebService(JRPCBlueprint):
    def __init__(self):
        self.faff = SubService()
        JRPCBlueprint.__init__(self, "service", __name__)

    @method(STRING(), path = "echo/<text>")
    def echo(self, text):
        return text


app = Flask(__name__)
app.register_blueprint(WebService())
app.run(host='0.0.0.0', port=8080, debug=True)