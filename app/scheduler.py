from apscheduler.schedulers.background import BackgroundScheduler
from app.database import SessionLocal
from app.models import Monitor
from app.monitor import check_monitor

scheduler = BackgroundScheduler()

def schedule_monitor(monitor_id: int, interval_seconds: int):
    job_id = f"monitor_{monitor_id}"

    scheduler.add_job(
        check_monitor,
        "interval",
        seconds=interval_seconds,
        args=[monitor_id],
        id=job_id,
        replace_existing = True
    )
    print(f"Schedule monitor {monitor_id} every {interval_seconds} seconds")

def remove_monitor_job(monitor_id:int):
    job_id = f"monitor_{monitor_id}"
    try:
        scheduler.remove_job(job_id)
        print(f"Removed scheduler job for monitor {monitor_id}")
    except Exception:
        print(f"No scheduler job found for monitor {monitor_id}")

def load_monitors():
    db = SessionLocal()
    try:
        monitors=(
            db.query(Monitor)
            .filter(Monitor.active == True).all()
        )
        for monitor in monitors:
            schedule_monitor(monitor.id, monitor.interval_seconds)

    finally:
        db.close()

def start_scheduler():
    load_monitors()
    scheduler.start()
    print("Scheduler started.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()

        print("Scheduler Stopped.")
