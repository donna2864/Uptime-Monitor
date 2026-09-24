from apscheduler.schedulers.background import BackgroundScheduler
from app.database import SessionLocal
from app.models import Monitor
from app.monitor import check_monitor

scheduler = BackgroundScheduler()

def check_due_monitors():
    db = SessionLocal()
    try:
        monitors = (
            db.query(Monitor).filter(Monitor.active == True).all()
        )

        for monitor in monitors:
            check_monitor(monitor.id)

    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(
        check_due_monitors,
        "interval",
        seconds=30,
        id="uptime_monitor_job",
        replace_existing = True
    )
    scheduler.start()

    print("Scheduler started.")
    print("Monitoring active urls every 30 seconds")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()

        print("Scheduler Stopped.")
