from fastapi import FastAPI, HTTPException
from app.database import Base, SessionLocal, engine
from app.models import Monitor, CheckResult, Incident
from app.schemas import MonitorCreate, MonitorResponse, CheckResultResponse, MonitorStatusResponse

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title = "Uptime Monitor API",
    description = "A lightweight service for monitoring APIs and websites.",
    version = "1.0.0"
)

@app.get("/")
def root():
    return {"message":"Uptime Monitor API is running"}

@app.post("/monitors", response_model=MonitorResponse)
def create_monitor(monitor_data: MonitorCreate):
    db = SessionLocal()
    try:
        monitor = Monitor(
            name=monitor_data.name,
            url=str(monitor_data.url),
            interval_seconds=monitor_data.interval_seconds,
            active=True
        )

        db.add(monitor)
        db.commit()
        db.refresh(monitor)

        return monitor
    finally:
        db.close()

@app.get("/monitors", response_model=list[MonitorResponse])
def get_monitors():
    db = SessionLocal()
    try:
        monitors = db.query(Monitor).all()
        return monitors
    finally:
        db.close()

@app.get("/monitors/{monitor_id}", response_model=MonitorResponse)
def get_monitor(monitor_id:int):
    db = SessionLocal()
    try:
        monitor = db.get(Monitor, monitor_id)

        if not monitor:
            raise HTTPException(
                status_code=404, detail="Monitor not found"
            )
        return monitor

    finally:
        db.close()

@app.get("/monitors/{monitor_id}/history", response_model=list[CheckResultResponse])
def get_monitor_history(monitor_id: int):
    db = SessionLocal()
    try:
        monitor = db.get(Monitor, monitor_id)
        if not monitor:
            raise HTTPException(status_code=404, detail="Monitor not found")
        results=(
            db.query(CheckResult)
            .filter(CheckResult.monitor_id == monitor_id)
            .order_by(CheckResult.checked_at.desc())
            .all()
        )
        return results
    finally:
        db.close()

@app.get("/monitors/{monitor_id}/status", response_model=MonitorStatusResponse)
def get_monitor_status(monitor_id:int):
    db = SessionLocal()
    try:
        monitor = db.get(Monitor, monitor_id)
        if not monitor:
            raise HTTPException(status_code=404, detail="Monitor not found")
        results =(
            db.query(CheckResult)
            .filter(CheckResult.monitor_id==monitor_id)
            .order_by(CheckResult.checked_at.desc())
            .all()
        )

        if not results:
            return {
                "monitor_id":monitor.id,
                "name" : monitor.name,
                "url" : monitor.url,
                "current_status": "Unknown",
                "uptime_percentage":0.0,
                "average_response_time_ms":None,
                "total_checks":0,
                "failed_checks":0
            }

        total_checks = len(results)
        failed_checks = sum(
            1 for result in results 
            if not result.is_up)

        successful_checks = total_checks - failed_checks

        uptime_percentage = (successful_checks/total_checks) * 100

        response_times = [
            result.response_time_ms
            for result in results
            if result.response_time_ms is not None
        ]

        average_response_time = (
            sum(response_times)/len(response_times)
            if response_times
            else None
        )

        current_status = (
            "UP" if results[0].is_up else "DOWN"
        )

        return {
                "monitor_id":monitor.id,
                "name" : monitor.name,
                "url" : monitor.url,
                "current_status": current_status,
                "uptime_percentage":round(uptime_percentage,2),
                "average_response_time_ms":round(average_response_time,2) if average_response_time is not None else None,
                "total_checks":total_checks,
                "failed_checks":failed_checks
            }

    finally: 
        db.close()


@app.delete("/monitors/{monitor_id}")
def delete_monitor(monitor_id:int):
    db = SessionLocal()
    try:
        monitor = db.get(Monitor, monitor_id)
        if not monitor:
            raise HTTPException(
                status_code=404, detail="monitor id not found"
            )
        db.delete(monitor)
        db.commit()
        return{
            "message":"Monitor deleted successfully"
        }
    finally:
        db.close()

@app.get("/monitors/{monitor_id}/incidents")
def get_monitor_incidents(monitor_id:int):
    db = SessionLocal()
    try:
        monitor = db.get(Monitor, monitor_id)
        if not monitor:
            raise HTTPException(status_code=404, detail="Monitor {monitor_id} not found")

        incidents = (
            db.query(Incident)
            .filter(Incident.monitor_id == monitor_id)
            .order_by(Incident.started_at.desc())
            .all()
        )

        return [
            {
                "id":incident.id,
                "monitor_id":incident.monitor_id,
                "started_at":incident.started_at,
                "resolved_at":incident.resolved_at,
                "reason": incident.reason
            }
            for incident in incidents
        ]
    finally:
        db.close()