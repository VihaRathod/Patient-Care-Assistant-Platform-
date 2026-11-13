
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from database.connection import SessionLocal

from models.notification import Notification

from services.patient_management_client import (
    get_upcoming_appointments
)

from services.email_service import (
    send_appointment_reminder
)


APP_TIMEZONE = ZoneInfo("Asia/Kolkata")


def process_appointment_reminder(
    db: Session,
    appointment: dict
):

    appointment_id = appointment["appointment_id"]

    # Check whether this reminder already exists
    existing_notification = (
        db.query(Notification)
        .filter(
            Notification.appointment_id == appointment_id,
            Notification.notification_type
            == "APPOINTMENT_REMINDER"
        )
        .first()
    )

    if existing_notification:

        # Do not send an already successful reminder
        if existing_notification.status == "SENT":
            return "SKIPPED"

        # Do not process an existing pending notification
        if existing_notification.status == "PENDING":
            return "SKIPPED"

        # Retry previously failed notifications
        notification = existing_notification

        notification.status = "PENDING"
        notification.error_message = None

    else:

        notification = Notification(
            patient_id=appointment["patient_id"],
            appointment_id=appointment_id,
            notification_type="APPOINTMENT_REMINDER",
            recipient_email=appointment["patient_email"],
            status="PENDING"
        )

        db.add(notification)

    # Save notification before sending
    db.commit()
    db.refresh(notification)

    try:

        appointment_datetime = datetime.fromisoformat(
            appointment["start_datetime"]
        )

        formatted_datetime = appointment_datetime.strftime(
            "%d %B %Y, %I:%M %p"
        )

        send_appointment_reminder(
            recipient_email=appointment["patient_email"],
            patient_name=appointment["patient_name"],
            provider_name=appointment["provider_name"],
            appointment_type=appointment["appointment_type"],
            appointment_datetime=formatted_datetime
        )

        notification.status = "SENT"
        notification.sent_at = datetime.now(APP_TIMEZONE)
        notification.error_message = None

        db.commit()

        print(
            f"Reminder sent for appointment {appointment_id}"
        )

        return "SENT"

    except Exception as error:

        db.rollback()

        # Re-fetch after rollback
        notification = (
            db.query(Notification)
            .filter(
                Notification.appointment_id == appointment_id,
                Notification.notification_type
                == "APPOINTMENT_REMINDER"
            )
            .first()
        )

        if notification:

            notification.status = "FAILED"
            notification.error_message = str(error)[:2000]

            db.commit()

        print(
            f"Reminder failed for appointment "
            f"{appointment_id}: {error}"
        )

        return "FAILED"


def run_appointment_reminders():

    print("Starting appointment reminder job...")

    db = SessionLocal()

    try:

        appointments = get_upcoming_appointments()

        print(
            f"Found {len(appointments)} upcoming appointments"
        )

        results = {
            "SENT": 0,
            "FAILED": 0,
            "SKIPPED": 0
        }

        for appointment in appointments:

            result = process_appointment_reminder(
                db,
                appointment
            )

            results[result] += 1

        print("Appointment reminder job completed")
        print(f"Results: {results}")

        return results

    except Exception as error:

        db.rollback()

        print(
            f"Appointment reminder job failed: {error}"
        )

    finally:

        db.close()
