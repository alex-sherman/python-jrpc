from jrpc.web import *
from jrpc.service import method
from flask import Flask, render_template, url_for

class WebService(JRPCBlueprint):
    def __init__(self):
        JRPCBlueprint.__init__(self, "service", __name__, url_prefix="/api", template_folder="templates", static_folder="static")

    @method(path = "/echo/<text>/<faff>")
    def echo(self, faff, text):
        return text + faff

app = Flask(__name__, template_folder="templates")
app.register_blueprint(WebService())

@app.route('/')
def index():
    return render_template("index.html")
app.run(host='0.0.0.0', port=8080, debug=True)