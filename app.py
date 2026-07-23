from flask import Flask, render_template, jsonify
from purger import get_status

app = Flask(__name__)

@app.route('/')
def index():

    status = get_status()
    return render_template("index.html", status=status)

@app.route("/api/status")
def api_status():
    return jsonify(get_status())

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5005, debug=False)