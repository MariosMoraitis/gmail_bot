from dotenv import load_dotenv
load_dotenv()

import os
import json
import time
import traceback
from purger import connect, purge_sender, record_run

EMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
APP_PASSWORD = os.environ["APP_PASSWORD"]
PURGE_DAYS = int(os.environ.get("PURGE_DAYS", '5'))
CHECK_INTERVAL_SECONDS = int(os.environ.get("CHECK_INTERVAL_HOURS", "24")) * 3600
TARGETS_PATH = os.path.join(os.path.dirname(__file__), 'config', "targets.json")

def load_targets():

    with open(TARGETS_PATH, 'r') as f:
        return json.load(f)

def run_once():

    targets = load_targets()
    all_deleted = []

    conn = connect(EMAIL_ADDRESS, APP_PASSWORD)
    try:
        for sender in targets:
            deleted = purge_sender(conn, sender, older_than_days=PURGE_DAYS)
            all_deleted.extend(deleted)
    finally:
        conn.logout()

    return all_deleted

def main_loop():

    while True:
        try:
            deleted = run_once()
            record_run(deleted, error=None)
            print(f"Purge run complete. {len(deleted)} message(s) deleted.", flush=True)

        except Exception as e:
            traceback.print_exc()
            record_run([], error=e)

        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == '__main__':
    main_loop()
