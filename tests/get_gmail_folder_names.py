from dotenv import load_dotenv
load_dotenv()
import os, imaplib

conn = imaplib.IMAP4_SSL('imap.gmail.com')
conn.login(os.environ['GMAIL_ADDRESS'], os.environ['APP_PASSWORD'])
status, folders = conn.list()

for f in folders:
    print(f.decode())

conn.logout()