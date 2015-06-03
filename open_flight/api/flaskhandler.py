import flask
from oslo_log import log

app = flask.Flask(__name__)

LOG = log.getLogger(__name__)


@app.route("/")
def hello():
    return flask.jsonify({"msg": "HELLO"})
