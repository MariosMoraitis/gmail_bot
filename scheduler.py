import schedule
import time
from bot import run_delete_old_emails

# Run unsubscribe scan every week
# schedule.every().week.do(run_unsubscribe_scan)

# Run delete old emails every day
schedule.every().day.do(run_delete_old_emails)

# For testing - run every minute:
# schedule.every(1).minutes.do(run_delete_old_emails)

print("Scheduler Started...")
while True:
    schedule.run_pending()
    time.sleep(10)
