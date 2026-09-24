from app.database import Base, SessionLocal, engine
from app.models import Monitor
from app.monitor import check_monitor

Base.metadata.create_all(bind=engine)

db=SessionLocal()
monitor = Monitor(
    name="Trial",
    url="https://example.com",
    interval_seconds=60,
    active=True
)

db.add(monitor)
db.commit()
db.refresh(monitor)
print(f"Created monitor with ID: {monitor.id}")
db.close()
check_monitor(monitor.id)