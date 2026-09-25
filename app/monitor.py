import time 
import httpx
from app.alert import send_webhook
from app.database import SessionLocal
from app.models import CheckResult, Monitor, Incident

def check_monitor(monitor_id: int):
    db = SessionLocal()
    try:
        monitor = db.get(Monitor, monitor_id)
        
        if not monitor:
            print(f"Monitor {monitor_id} not found")
            return
        
        if not monitor.active:
            db.close()
            return
        
        start_time = time.perf_counter()
        try:
            response = httpx.get(
                monitor.url,
                timeout=10.0,
                follow_redirects=True
            )
            response_time_ms = (time.perf_counter()-start_time) * 1000
            is_up = 200 <= response.status_code < 400
            result = CheckResult(
                monitor_id = monitor.id,
                status_code=response.status_code,
                response_time_ms = round(response_time_ms,2),
                is_up=is_up,
                error_message=None
            )
            print(f"[CHECK]:{monitor.name} | " 
                  f"Status: {response.status_code} | "
                  f"Time: {response_time_ms:.2f} ms | "
                  f"UP: {is_up}")

        except httpx.RequestError as error:
            response_time_ms = (time.perf_counter() - start_time)*1000
            result = CheckResult(
                monitor_id = monitor.id,
                status_code=None,
                response_time_ms=round(response_time_ms,2),
                is_up = False,
                error_message=str(error)
            )
            print(f"[CHECK]:{monitor.name} | " 
                  f"Status: DOWN | "
                  f"Time: {response_time_ms:.2f} ms | "
                  f"Error: {error}")

        db.add(result)
        db.commit()

        recent_results = (
            db.query(CheckResult).filter(CheckResult.monitor_id==monitor_id)
            .order_by(CheckResult.checked_at.desc()).limit(3).all()
        )
        open_incident = (
            db.query(Incident)
            .filter(Incident.monitor_id==monitor_id,
                    Incident.resolved_at.is_(None)).first()
        )
        if len(recent_results) == 3 and all(not check.is_up for check in recent_results):
            if not open_incident:
                incident = Incident(
                    monitor_id=monitor_id,
                    reason="Monitor failed 3 consecutive checks"
                )
                db.add(incident)
                db.commit()

                print(f"[INCIDENT] {monitor.name} is DOWN for 3 consecutive checks")

                send_webhook(
                    f"ALERT {monitor.name} is DOWN, \n The monitor failed 3 consecutive checks"
                )

        elif result.is_up and open_incident:
            open_incident.resolved_at = result.checked_at
            db.commit()
            print(f"[RECOVERY] {monitor.name} is back UP")
            send_webhook(
                f"RECOVERY {monitor.name} is back UP. \n the incident has been resolved"
            )

    finally:
        db.close()