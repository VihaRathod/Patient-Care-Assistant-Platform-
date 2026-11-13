
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler

from config.settings import settings

from jobs.appointment_reminders import (
    run_appointment_reminders
)


scheduler = BackgroundScheduler(
    timezone=ZoneInfo("Asia/Kolkata")
)


def start_scheduler():

    if scheduler.running:
        return

    scheduler.add_job(
        run_appointment_reminders,
        trigger="interval",
        minutes=settings.SCHEDULER_INTERVAL_MINUTES,
        id="appointment_reminders",
        name="Appointment Reminder Job",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
        next_run_time=datetime.now(
            ZoneInfo("Asia/Kolkata")
        )
    )

    scheduler.start()

    print("Notification scheduler started")


def stop_scheduler():

    if scheduler.running:

        scheduler.shutdown(wait=True)

        print("Notification scheduler stopped")
