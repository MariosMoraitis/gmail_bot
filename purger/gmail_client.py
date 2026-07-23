import imaplib
import email

import socket
socket.setdefaulttimeout(15)

IMAP_HOST = "imap.gmail.com"
TRASH_FOLDER = '"[Gmail]/&A5oDrAO0A78Dwg- &A7EDwAO,A8EDwQO5A7wDvAOsA8QDyQO9-"'
ALL_MAIL_FOLDER = '"[Gmail]/&A4wDuwOx- &A8QDsQ- &A7wDtwO9A80DvAOxA8QDsQ-"'


def connect(email_address, app_password):
    conn = imaplib.IMAP4_SSL(IMAP_HOST)
    conn.login(email_address, app_password)
    return conn


def find_old_messages(conn, sender, older_than_days, source_folder):
    status, _ = conn.select(source_folder)
    if status != 'OK':
        print(f"WARNING: could not select {source_folder}")
        return []

    gmail_query = f'from:{sender} older_than:{older_than_days}d -is:starred -is:important'
    status, data = conn.uid('SEARCH', 'X-GM-RAW', f'"{gmail_query}"')
    if status != 'OK' or not data[0]:
        return []
    return data[0].split()


def get_header_field(conn, uid, field):
    status, data = conn.uid('FETCH', uid, f"(BODY.PEEK[HEADER.FIELDS ({field})])")
    if status != 'OK' or not data or not data[0]:
        return None

    header = data[0][1].decode(errors="ignore")
    msg = email.message_from_string(header)
    return msg.get(field)


def perm_delete(conn, uid, source_folder):
    status, _ = conn.select(source_folder)
    if status != 'OK':
        print(f"WARNING: could not re-select {source_folder}")
        return False

    message_id = get_header_field(conn, uid, "Message-ID")

    status, _ = conn.uid('COPY', uid, TRASH_FOLDER)
    if status != 'OK':
        print(f"WARNING: could not copy uid {uid} to {TRASH_FOLDER}")
        return False

    status, _ = conn.uid('STORE', uid, '+FLAGS', '\\Deleted')
    if status != 'OK':
        print(f"WARNING: could not flag uid {uid} deleted in {source_folder}")
        return False

    conn.expunge()

    if not message_id:
        return False

    status, _ = conn.select(TRASH_FOLDER)
    if status != 'OK':
        print(f"WARNING: could not select {TRASH_FOLDER}")
        return False

    status, data = conn.uid('SEARCH', None, f'(HEADER Message-ID "{message_id}")')
    if status == 'OK' and data[0]:
        trash_uid = data[0].split()[0]
        conn.uid('STORE', trash_uid, '+FLAGS', '\\Deleted')
        conn.expunge()
        return True

    return False


def purge_sender(conn, sender, older_than_days=5, on_delete=None):
    deleted = []
    uids = find_old_messages(conn, sender, older_than_days, ALL_MAIL_FOLDER)
    for uid in uids:
        status, _ = conn.select(ALL_MAIL_FOLDER)
        if status != 'OK':
            continue
        subject = get_header_field(conn, uid, "Subject") or "(no subject)"
        if perm_delete(conn, uid, ALL_MAIL_FOLDER):
            entry = {"from": sender, "subject": subject}
            deleted.append(entry)
            if on_delete:
                on_delete(entry)

    return deleted
