import os
import imaplib
import email
import json
from datetime import datetime, timedelta, timezone
# from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime

EMAIL = os.getenv("EMAIL")
APP_PASSWORD = os.getenv("PASSWORD")
STATUS_FILE = "status.json"

def log(message):
    with open("log.txt", "a") as f:
        f.write(message + "\n")
    print(message)

def update_status(connected):
    """Update connection status to a JSON file"""
    try:
        with open(STATUS_FILE, "w") as f:
            json.dump({
                "connected": connected,
                "timestamp": datetime.now().isoformat()
            }, f)
    except Exception as e:
        print(f"Failed to update status: {e}")

# def run_unsubscribe_scan():
#     log("=== New scan started ===")

#     try:
#         mail = login()
#         if not mail:
#             log("Couldn't connect to GMAIL")
#             return

#         _, search_data = mail.search(None, '(BODY "unsubscribe")')
#         message_ids = search_data[0].split()
#         log(f"Found {len(message_ids)} potential newsletter emails")

#         for num in message_ids:
#             _, data = mail.fetch(num, "(RFC822)")
#             msg = email.message_from_bytes(data[0][1])

#             html_content = ""

#             if msg.is_multipart():
#                 for part in msg.walk():
#                     if part.get_content_type() == "text/html":
#                         html_content = part.get_payload(decode=True)
#             else:
#                 if msg.get_content_type() == "text/html":
#                     html_content = msg.get_payload(decode=True)

#             if html_content:
#                 soup = BeautifulSoup(html_content, "html.parser")
#                 link = soup.find("a", string=lambda s: s and "unsubscribe" in s.lower())

#                 if link:
#                     log(f"Found unsubscribe link: {link['href']}")
#                 else:
#                     log("No link found in this email")

#         mail.logout()
#         log("Scan completed successfully!\n")

#     except Exception as e:
#         update_status(False)
#         log(f"ERROR: {str(e)}\n")

def run_delete_old_emails():
    log("=== Delete old emails scan started ===")

    try:
        with open("senders.json") as f:
            senders = json.load(f).get("to_be_deleted", [])
        
        if not senders:
            log("No senders configured for deletion")
            return

        # Normalize lowercase for comparison
        # senders = [s.lower() for s in senders]

        mail = login()
        if not mail:
            log("Couldn't connect to GMAIL")
            return
        

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=5)
        deleted_count = 0

        # Fetch ALL emails (or last 30 days with SINCE)
        _, search_data = mail.search(None, "ALL")
        all_ids = search_data[0].split()

        log(f"Scanning {len(all_ids)} emails...")

        for num in all_ids:
            # Fetch headers only
            _, data = mail.fetch(num, "(BODY[HEADER.FIELDS (FROM DATE)])")
            msg = email.message_from_bytes(data[0][1])

            raw_from = msg.get("From", "").lower()
            
            # 1) Match sender manually
            if not any(s in raw_from for s in senders):
                continue  # not a sender we care about
            
            # 2) Parse date
            try:
                raw_date = msg.get("Date")
                msg_date = parsedate_to_datetime(raw_date)
            except Exception:
                log(f"Skipping email (bad date): from={raw_from}")
                continue

            # 3) Delete if too old
            if msg_date < cutoff_date:
                mail.store(num, "+FLAGS", "\\Deleted")
                deleted_count += 1
                log(f"Deleted: {raw_from} - {msg_date}")

        mail.expunge()
        mail.logout()
        log(f"Delete scan completed! Removed {deleted_count} old emails.\n")

    except Exception as e:
        update_status(False)
        log(f"ERROR: {str(e)}\n")


    except Exception as e:
        update_status(False)
        log(f"ERROR: {str(e)}\n")

def login():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL, APP_PASSWORD)
    mail.select("inbox")
    update_status(True)
    log("Connected to Gmail")
    return mail