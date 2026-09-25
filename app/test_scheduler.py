from app.scheduler import scheduler, schedule_monitor, remove_monitor_job


def test_schedule_monitor():

    monitor_id = 9999

    schedule_monitor(monitor_id, 10)

    job = scheduler.get_job(f"monitor_{monitor_id}")

    assert job is not None
    assert job.id == f"monitor_{monitor_id}"

    remove_monitor_job(monitor_id)


def test_remove_monitor_job():

    monitor_id = 9998

    schedule_monitor(monitor_id, 10)

    assert scheduler.get_job(f"monitor_{monitor_id}") is not None

    remove_monitor_job(monitor_id)

    assert scheduler.get_job(f"monitor_{monitor_id}") is None