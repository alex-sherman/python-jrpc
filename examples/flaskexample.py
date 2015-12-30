from jrpc.web import *
from jrpc.service import method
from flask import Flask

class WebService(JRPCBlueprint):
    def __init__(self):
        JRPCBlueprint.__init__(self, "service", __name__)

    @method(path = "/echo/<text>")
    def echo(self, text):
        return text


app = Flask(__name__)
app.register_blueprint(WebService())
app.run(host='0.0.0.0', port=8080, debug=True)