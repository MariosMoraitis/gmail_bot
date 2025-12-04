"""
scheduler.py

Simple scheduler wrapper using the `schedule` library. It imports the
task(s) from `bot.py` and runs them on the configured schedule.
"""

import schedule
import time
from bot import run_delete_old_emails

# Schedule the delete task (adjust in the file for different frequency)
schedule.every().day.do(run_delete_old_emails)

# For instant testing run at the terminal:
# sudo docker exec -it gmail_automation-gmail_scheduler-1 python3 -c from bot import run_delete_old_emails; run_delete_old_emails()

if __name__ == "__main__":
    print("Scheduler Started...")
    while True:
        schedule.run_pending()
        time.sleep(10)
