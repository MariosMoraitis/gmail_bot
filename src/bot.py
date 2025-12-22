"""
bot.py

Simple Gmail automation helpers:
- Connects to Gmail via IMAP
- Logs activity to `log.txt`
- Writes connection status to `status.json`
- Deletes old emails from senders listed in `senders.json`
"""

import os
import imaplib
import email
import json
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

# Environment variables (load via .env in Docker compose)
EMAIL = os.getenv("EMAIL")
APP_PASSWORD = os.getenv("PASSWORD")

# Files used by the bot
from .paths import return_senders_file, return_status_file

STATUS_FILE = return_status_file()
LOG_FILE = "log.txt"
SENDERS_FILE = return_senders_file()


def log(message: str) -> None:
    """Append a timestamped message to the log file and stdout."""
    ts = datetime.now(timezone.utc).isoformat()
    line = f"{ts} - {message}"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        # best-effort logging; don't crash the bot because logging failed
        pass
    # print(line)


def update_status(connected: bool) -> None:
    """Write a small JSON file with connection status and a timestamp."""
    try:
        payload = {"connected": bool(connected), "timestamp": datetime.now(timezone.utc).isoformat()}
        with open(STATUS_FILE, "w") as f:
            json.dump(payload, f)
    except Exception as e:
        # Non-fatal: log to stdout
        print(f"update_status failed: {e}")


def login():
    """Establish an IMAP SSL connection and return the IMAP object or None."""
    if not EMAIL or not APP_PASSWORD:
        log("Missing EMAIL or PASSWORD environment variables")
        update_status(False)
        return None
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL, APP_PASSWORD)
        mail.select("inbox")
        update_status(True)
        log("Connected to Gmail")
        return mail
    except Exception as e:
        update_status(False)
        log(f"Failed to connect: {e}")
        return None


def run_delete_old_emails() -> None:
    """
    Delete emails from senders listed in `senders.json` that are older
    than the configured threshold (5 days by default).
    """
    log("=== Delete old emails scan started ===")

    try:
        with open(SENDERS_FILE) as f:
            senders = json.load(f).get("to_be_deleted", [])
    except FileNotFoundError:
        log("senders.json not found")
        return
    except Exception as e:
        log(f"Failed to read senders.json: {e}")
        return

    if not senders:
        log("No senders configured for deletion")
        return

    mail = login()
    if not mail:
        # login() already logs and updates status
        return

    # Make cutoff timezone-aware to match parsed email dates
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=5)
    deleted_count = 0

    try:
        # Search per-sender to limit results
        for sender in senders:
            # IMAP search: FROM "sender"
            typ, data = mail.search(None, f'(FROM "{sender}")')
            if typ != "OK":
                continue
            message_ids = data[0].split()
            for num in message_ids:
                # Fetch full message to read Date header
                typ, msg_data = mail.fetch(num, "(RFC822)")
                if typ != "OK" or not msg_data or not msg_data[0]:
                    continue
                msg = email.message_from_bytes(msg_data[0][1])
                raw_date = msg.get("Date")
                if not raw_date:
                    continue
                try:
                    msg_date = parsedate_to_datetime(raw_date)
                except Exception:
                    # If parsing fails skip this message
                    continue

                # parsedate_to_datetime returns aware or naive; ensure aware UTC
                if msg_date.tzinfo is None:
                    msg_date = msg_date.replace(tzinfo=timezone.utc)
                else:
                    msg_date = msg_date.astimezone(timezone.utc)

                if msg_date < cutoff_date:
                    # Mark for deletion
                    mail.store(num, "+FLAGS", "\\Deleted")
                    deleted_count += 1
                    log(f"Deleted: {sender} - {msg_date.isoformat()}")

        # Permanently remove messages marked \Deleted
        mail.expunge()
        log(f"Delete scan completed! Removed {deleted_count} old emails.")
    except Exception as e:
        log(f"ERROR during deletion: {e}")
    finally:
        try:
            mail.logout()
        except Exception:
            pass
        update_status(True)

def clear_log_file():
    """
    This function will be run from the scheduler, in order to keep the log file clear
    """
    with open(LOG_FILE, 'r+') as f:
        f.seek(0)
        f.truncate()
        f.write(f"Cleared the log file at {datetime.now()}\n")