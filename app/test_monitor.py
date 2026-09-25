from unittest.mock import patch
from app.database import SessionLocal
from app.models import Monitor, CheckResult, Incident
from app.monitor import check_monitor

def test_successful_monitor_check():
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
    monitor_id=monitor.id
    db.close()
    check_monitor(monitor.id)

    db = SessionLocal()
    result = (
        db.query(CheckResult)
        .filter(CheckResult.monitor_id == monitor_id)
        .order_by(CheckResult.id.desc())
        .first()
    )

    assert result is not None
    assert result.is_up is True
    assert result.status_code == 200
    assert result.response_time_ms is not None

    db.close()

def test_failed_monitor_check():

    db = SessionLocal()

    monitor = Monitor(
        name="Failed Test Monitor",
        url="http://127.0.0.1:9999",
        interval_seconds=60,
        active=True
    )

    db.add(monitor)
    db.commit()
    db.refresh(monitor)

    monitor_id = monitor.id

    db.close()

    # Run the actual monitoring function
    check_monitor(monitor_id)

    # Check what was stored in the database
    db = SessionLocal()

    result = (
        db.query(CheckResult)
        .filter(CheckResult.monitor_id == monitor_id)
        .order_by(CheckResult.id.desc())
        .first()
    )

    assert result is not None
    assert result.is_up is False
    assert result.status_code is None
    assert result.response_time_ms is not None
    assert result.error_message is not None

    db.close()

def test_inactive_monitor_is_not_checked():

    db = SessionLocal()

    monitor = Monitor(
        name="Inactive Test Monitor",
        url="https://example.com",
        interval_seconds=60,
        active=False
    )

    db.add(monitor)
    db.commit()
    db.refresh(monitor)

    monitor_id = monitor.id

    db.close()

    # Run the monitoring function
    check_monitor(monitor_id)

    # Check the database
    db = SessionLocal()

    result = (
        db.query(CheckResult)
        .filter(CheckResult.monitor_id == monitor_id)
        .order_by(CheckResult.id.desc())
        .first()
    )

    assert result is None

    db.close()

def test_multiple_monitor_checks_create_multiple_results():

    db = SessionLocal()

    monitor = Monitor(
        name="Multiple Checks Monitor",
        url="https://example.com",
        interval_seconds=60,
        active=True
    )

    db.add(monitor)
    db.commit()
    db.refresh(monitor)

    monitor_id = monitor.id

    db.close()

    # Run the monitor twice
    check_monitor(monitor_id)
    check_monitor(monitor_id)

    # Check the database
    db = SessionLocal()

    results = (
        db.query(CheckResult)
        .filter(CheckResult.monitor_id == monitor_id)
        .all()
    )

    assert len(results) == 2

    for result in results:
        assert result.is_up is True
        assert result.status_code == 200
        assert result.response_time_ms is not None

    db.close()

def test_multiple_failed_checks_create_multiple_results():

    db = SessionLocal()

    monitor = Monitor(
        name="Multiple Failed Checks Monitor",
        url="http://127.0.0.1:9999",
        interval_seconds=60,
        active=True
    )

    db.add(monitor)
    db.commit()
    db.refresh(monitor)

    monitor_id = monitor.id

    db.close()

    # Run the failed monitor twice
    check_monitor(monitor_id)
    check_monitor(monitor_id)

    # Check the database
    db = SessionLocal()

    results = (
        db.query(CheckResult)
        .filter(CheckResult.monitor_id == monitor_id)
        .all()
    )

    assert len(results) == 2

    for result in results:
        assert result.is_up is False
        assert result.status_code is None
        assert result.response_time_ms is not None
        assert result.error_message is not None

    db.close()

def test_three_consecutive_failures_create_incident():

    db = SessionLocal()

    monitor = Monitor(
        name="Incident Test Monitor",
        url="http://127.0.0.1:9999",
        interval_seconds=60,
        active=True
    )

    db.add(monitor)
    db.commit()
    db.refresh(monitor)

    monitor_id = monitor.id

    db.close()

    with patch("app.monitor.send_webhook") as mock_webhook:

        check_monitor(monitor_id)
        check_monitor(monitor_id)
        check_monitor(monitor_id)

        db = SessionLocal()

        incident = (
            db.query(Incident)
            .filter(
                Incident.monitor_id == monitor_id,
                Incident.resolved_at.is_(None)
            )
            .first()
        )

        assert incident is not None
        assert incident.reason == "Monitor failed 3 consecutive checks"

        mock_webhook.assert_called_once()

        db.close()

def test_monitor_recovery_resolves_incident():

    db = SessionLocal()

    monitor = Monitor(
        name="Recovery Test Monitor",
        url="http://127.0.0.1:9999",
        interval_seconds=60,
        active=True
    )

    db.add(monitor)
    db.commit()
    db.refresh(monitor)

    monitor_id = monitor.id

    db.close()

    with patch("app.monitor.send_webhook") as mock_webhook:

        # Create 3 consecutive failures
        check_monitor(monitor_id)
        check_monitor(monitor_id)
        check_monitor(monitor_id)

        db = SessionLocal()

        incident = (
            db.query(Incident)
            .filter(
                Incident.monitor_id == monitor_id,
                Incident.resolved_at.is_(None)
            )
            .first()
        )

        assert incident is not None

        db.close()

        # Change the monitor URL to a working endpoint
        db = SessionLocal()

        monitor = db.get(Monitor, monitor_id)
        monitor.url = "https://example.com"

        db.commit()
        db.close()

        # Run another check — this should recover
        check_monitor(monitor_id)

        db = SessionLocal()

        incident = (
            db.query(Incident)
            .filter(Incident.monitor_id == monitor_id)
            .first()
        )

        assert incident is not None
        assert incident.resolved_at is not None

        # 1st webhook = DOWN alert
        # 2nd webhook = RECOVERY alert
        assert mock_webhook.call_count == 2

        db.close()