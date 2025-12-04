import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "config")

def return_senders_file():
    return os.path.join(CONFIG_DIR, "senders.json")

def return_status_file():
    return os.path.join(CONFIG_DIR, "status.json")