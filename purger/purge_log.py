import json
import os
from datetime import datetime, timezone
from threading import Lock

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "purge_log.json")
_lock = Lock()

def _load():

    if not os.path.exists(LOG_PATH):
        return {"last_run": None, "last_stasus": "never_run", "last_error": None, "entries": []}

    with open(LOG_PATH, 'r') as f:
        return json.load(f)

def _save(data):

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def record_run(deleted_entries, error=None):

    with _lock:
        data = _load()
        data["last_run"] = datetime.now(timezone.utc).isoformat()
        data["last_status"] = 'error' if error else 'ok'
        data["last_error"] = str(error) if error else None

        for entry in deleted_entries:
            entry['deleted_at'] = datetime.now(timezone.utc).isoformat()
            data["entries"].append(entry)

        data["entries"] = data["entries"][-500:] # cap so the file doesn't grow forever
        _save(data)

    return data

def get_status():
    with _lock:
        return _load()
