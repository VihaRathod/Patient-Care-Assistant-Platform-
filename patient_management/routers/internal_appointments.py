
from config.settings import settings
import secrets

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload

from database.connection import get_db

from models.appointment import (
    Appointment,
    AppointmentStatus
)

from models.patient import Patient

from schemas.internal_notification import (
    UpcomingAppointmentReminder
)


router = APIRouter(
    prefix="/internal/appointments",
    tags=["Internal Service Communication"]
)


APP_TIMEZONE = ZoneInfo("Asia/Kolkata")


def verify_internal_token(
    x_internal_service_token: str = Header(...)
):
    expected_token = settings.internal_service_token

    if not expected_token:
        raise HTTPException(
            status_code=503,
            detail="Internal service authentication is not configured"
        )

    if not secrets.compare_digest(
        x_internal_service_token,
        expected_token
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid internal service token"
        )


@router.get(
    "/upcoming-reminders",
    response_model=list[UpcomingAppointmentReminder],
    dependencies=[Depends(verify_internal_token)]
)
def get_upcoming_appointment_reminders(
    db: Session = Depends(get_db)
):

    now = datetime.now(APP_TIMEZONE)

    reminder_hours = settings.reminder_hours_before

    # Allow a 30-minute window so that a scheduler
    # running every 15 minutes does not miss appointments.
    window_start = now + timedelta(
        hours=reminder_hours,
        minutes=-15
    )

    window_end = now + timedelta(
        hours=reminder_hours,
        minutes=15
    )

    appointments = (
        db.query(Appointment)
        .options(
            joinedload(Appointment.patient)
            .joinedload(Patient.user),

            joinedload(Appointment.provider)
        )
        .filter(
            Appointment.start_datetime >= window_start,
            Appointment.start_datetime <= window_end,

            Appointment.status.in_([
                AppointmentStatus.SCHEDULED,
                AppointmentStatus.CONFIRMED
            ])
        )
        .order_by(Appointment.start_datetime.asc())
        .all()
    )

    results = []

    for appointment in appointments:

        patient = appointment.patient
        provider = appointment.provider

        if not patient or not patient.user:
            continue

        if not patient.user.email:
            continue

        results.append(
            UpcomingAppointmentReminder(
                appointment_id=appointment.id,
                patient_id=patient.id,

                patient_name=(
                    f"{patient.first_name} "
                    f"{patient.last_name}"
                ),

                patient_email=patient.user.email,

                provider_name=(
                    f"{provider.first_name} "
                    f"{provider.last_name}"
                ),

                appointment_type=(
                    appointment.appointment_type.value
                ),

                start_datetime=appointment.start_datetime,
                end_datetime=appointment.end_datetime
            )
        )

    return results
