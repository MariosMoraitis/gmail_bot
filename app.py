from flask import Flask, render_template
import json
import os
from datetime import datetime

app = Flask(__name__)

LOG_FILE = "log.txt"
STATUS_FILE = "status.json"


def safe_read_file(path):
    """Read a file safely even if another process is writing to it."""
    try:
        with open(path, "r", errors="ignore") as f:
            return f.read()
    except FileNotFoundError:
        return None
    except Exception:
        return None


@app.route("/")
def home():
    # Read log file safely
    log_content = safe_read_file(LOG_FILE)
    if log_content:
        logs = log_content.splitlines()
        logs.reverse()  # newest first
    else:
        logs = ["No logs yet."]

    # Read status.json safely
    status = {
        "connected": False,
        "timestamp": "No status recorded"
    }

    st_json = safe_read_file(STATUS_FILE)
    if st_json:
        try:
            status = json.loads(st_json)
        except json.JSONDecodeError:
            status = {
                "connected": False,
                "timestamp": "Corrupted status file"
            }

    # Format timestamp nicely
    try:
        if "timestamp" in status:
            dt = datetime.fromisoformat(status["timestamp"])
            status["timestamp"] = dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        pass

    return render_template("index.html", logs=logs, status=status)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
