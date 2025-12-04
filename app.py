"""
app.py

Flask dashboard for viewing bot logs and connection status.
"""

import json
from datetime import datetime
from flask import Flask, render_template

app = Flask(__name__)

LOG_FILE = "log.txt"
STATUS_FILE = "status.json"


def safe_read_file(path: str):
    """Return file contents or None if not available or in-use."""
    try:
        with open(path, "r", errors="ignore") as f:
            return f.read()
    except FileNotFoundError:
        return None
    except Exception:
        return None


@app.route("/")
def home():
    """Render the dashboard showing logs and connection status."""
    log_content = safe_read_file(LOG_FILE)
    if log_content:
        logs = log_content.strip().splitlines()
    else:
        logs = ["No logs yet."]

    # Default status shown when status.json does not exist
    status = {"connected": False, "timestamp": "Never"}
    st_json = safe_read_file(STATUS_FILE)
    if st_json:
        try:
            status = json.loads(st_json)
        except Exception:
            # keep default on parse failure
            pass

    # Try to format timestamp for display
    try:
        ts = status.get("timestamp")
        if ts:
            status["timestamp"] = datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        # leave raw timestamp if formatting fails
        pass

    return render_template("index.html", logs=logs, status=status)


if __name__ == "__main__":
    # Development server. When running in production use gunicorn.
    app.run(host="0.0.0.0", port=5000)
