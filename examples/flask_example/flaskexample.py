from jrpc.web import *
import jrpc.service
from flask import Flask, render_template

app = Flask(__name__)

class WebService(JRPCBlueprint):
    @jrpc.service.method(path = "/echo/<name>")
    def echo(self, text, prefix = "Hello from", name = ""):
        return {"subject": prefix + " " + name, "message": text}

app.register_blueprint(WebService("service", __name__, url_prefix="/api"))

@app.route('/')
def index():
    return render_template("index.html")
app.run(host='0.0.0.0', port=8080, debug=True)