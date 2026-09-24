import time
from app.scheduler import start_scheduler, stop_scheduler

try:
    start_scheduler()
    print("Schheduler is running.")
    print("Waiting for checks..")

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n Stopping Scheduler")
    stop_scheduler()