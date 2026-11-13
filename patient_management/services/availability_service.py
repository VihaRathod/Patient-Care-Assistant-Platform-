
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.user import User, UserRole
from models.provider import Provider
from models.provider_availability import ProviderAvailability
from models.provider_time_off import ProviderTimeOff
from models.appointment import Appointment, AppointmentStatus

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


# --------------------------------------------------
# COMMON HELPER
# --------------------------------------------------

def get_provider_by_id(
    db: Session,
    provider_id: int
):
    provider = (
        db.query(Provider)
        .filter(Provider.id == provider_id)
        .first()
    )

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )

    return provider


def get_provider_by_user_id(
    db: Session,
    user_id: int
):
    provider = (
        db.query(Provider)
        .filter(Provider.user_id == user_id)
        .first()
    )

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider profile not found"
        )

    return provider


def resolve_provider_id(
    db: Session,
    current_user: User,
    provider_id: int | None = None
):
    """
    Provider: always use their own provider profile.
    Admin: must provide the target provider_id when creating.
    """

    if current_user.role == UserRole.PROVIDER:
        provider = get_provider_by_user_id(
            db,
            current_user.id
        )
        return provider.id

    if current_user.role == UserRole.ADMIN:
        if provider_id is None:
            raise HTTPException(
                status_code=400,
                detail="provider_id is required for admin"
            )

        get_provider_by_id(db, provider_id)
        return provider_id

    raise HTTPException(
        status_code=403,
        detail="You do not have permission to manage provider schedules"
    )


# --------------------------------------------------
# PROVIDER AVAILABILITY
# --------------------------------------------------

def create_availability(
    db: Session,
    provider_id: int,
    availability_data: dict
):
    get_provider_by_id(db, provider_id)

    day = availability_data["day_of_week"]
    start = availability_data["start_time"]
    end = availability_data["end_time"]

    if start >= end:
        raise HTTPException(
            status_code=400,
            detail="End time must be after start time"
        )

    # Prevent overlapping availability slots
    existing_slots = (
        db.query(ProviderAvailability)
        .filter(
            ProviderAvailability.provider_id == provider_id,
            ProviderAvailability.day_of_week == day,
            ProviderAvailability.is_active == True,
            ProviderAvailability.start_time < end,
            ProviderAvailability.end_time > start
        )
        .first()
    )

    if existing_slots:
        raise HTTPException(
            status_code=409,
            detail="Availability overlaps with an existing slot"
        )

    availability = ProviderAvailability(
        provider_id=provider_id,
        **availability_data
    )

    try:
        db.add(availability)
        db.commit()
        db.refresh(availability)

    except Exception:
        db.rollback()
        raise

    return availability


def get_provider_availability(
    db: Session,
    provider_id: int
):
    get_provider_by_id(db, provider_id)

    return (
        db.query(ProviderAvailability)
        .filter(
            ProviderAvailability.provider_id == provider_id
        )
        .order_by(
            ProviderAvailability.day_of_week,
            ProviderAvailability.start_time
        )
        .all()
    )


def get_availability_by_id(
    db: Session,
    availability_id: int
):
    availability = (
        db.query(ProviderAvailability)
        .filter(
            ProviderAvailability.id == availability_id
        )
        .first()
    )

    if not availability:
        raise HTTPException(
            status_code=404,
            detail="Availability slot not found"
        )

    return availability


def update_availability(
    db: Session,
    availability: ProviderAvailability,
    update_data: dict
):
    new_day = update_data.get(
        "day_of_week",
        availability.day_of_week
    )

    new_start = update_data.get(
        "start_time",
        availability.start_time
    )

    new_end = update_data.get(
        "end_time",
        availability.end_time
    )

    if new_start >= new_end:
        raise HTTPException(
            status_code=400,
            detail="End time must be after start time"
        )

    new_is_active = update_data.get(
        "is_active",
        availability.is_active
    )

    # Check for overlapping slots if the updated slot is active
    if new_is_active:
        overlapping_slot = (
            db.query(ProviderAvailability)
            .filter(
                ProviderAvailability.provider_id == availability.provider_id,
                ProviderAvailability.day_of_week == new_day,
                ProviderAvailability.is_active == True,
                ProviderAvailability.id != availability.id,
                ProviderAvailability.start_time < new_end,
                ProviderAvailability.end_time > new_start
            )
            .first()
        )

        if overlapping_slot:
            raise HTTPException(
                status_code=409,
                detail="Updated availability overlaps with another slot"
            )

    for field, value in update_data.items():
        setattr(availability, field, value)

    try:
        db.commit()
        db.refresh(availability)

    except Exception:
        db.rollback()
        raise

    return availability


def delete_availability(
    db: Session,
    availability: ProviderAvailability
):
    db.delete(availability)

    try:
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "message": "Availability slot deleted successfully"
    }


# --------------------------------------------------
# PROVIDER TIME OFF
# --------------------------------------------------

def create_time_off(
    db: Session,
    provider_id: int,
    time_off_data: dict
):
    get_provider_by_id(db, provider_id)

    start = time_off_data["start_datetime"]
    end = time_off_data["end_datetime"]

    if start >= end:
        raise HTTPException(
            status_code=400,
            detail="End datetime must be after start datetime"
        )

    # Check whether provider already has appointments
    # during the requested time off.
    existing_appointment = (
        db.query(Appointment)
        .filter(
            Appointment.provider_id == provider_id,
            Appointment.status.notin_([
                AppointmentStatus.CANCELLED,
                AppointmentStatus.NO_SHOW
            ]),
            Appointment.start_datetime < end,
            Appointment.end_datetime > start
        )
        .first()
    )

    if existing_appointment:
        raise HTTPException(
            status_code=409,
            detail="Provider has existing appointments during this time"
        )

    time_off = ProviderTimeOff(
        provider_id=provider_id,
        **time_off_data
    )

    try:
        db.add(time_off)
        db.commit()
        db.refresh(time_off)

    except Exception:
        db.rollback()
        raise

    return time_off


def get_provider_time_off(
    db: Session,
    provider_id: int
):
    get_provider_by_id(db, provider_id)

    return (
        db.query(ProviderTimeOff)
        .filter(
            ProviderTimeOff.provider_id == provider_id
        )
        .order_by(
            ProviderTimeOff.start_datetime
        )
        .all()
    )


def get_time_off_by_id(
    db: Session,
    time_off_id: int
):
    time_off = (
        db.query(ProviderTimeOff)
        .filter(
            ProviderTimeOff.id == time_off_id
        )
        .first()
    )

    if not time_off:
        raise HTTPException(
            status_code=404,
            detail="Time off record not found"
        )

    return time_off


def update_time_off(
    db: Session,
    time_off: ProviderTimeOff,
    update_data: dict
):
    new_start = update_data.get(
        "start_datetime",
        time_off.start_datetime
    )

    new_end = update_data.get(
        "end_datetime",
        time_off.end_datetime
    )

    if new_start >= new_end:
        raise HTTPException(
            status_code=400,
            detail="End datetime must be after start datetime"
        )

    # Prevent time off from overlapping existing appointments
    existing_appointment = (
        db.query(Appointment)
        .filter(
            Appointment.provider_id == time_off.provider_id,
            Appointment.status.notin_([
                AppointmentStatus.CANCELLED,
                AppointmentStatus.NO_SHOW
            ]),
            Appointment.start_datetime < new_end,
            Appointment.end_datetime > new_start
        )
        .first()
    )

    if existing_appointment:
        raise HTTPException(
            status_code=409,
            detail="Provider has existing appointments during this time"
        )

    for field, value in update_data.items():
        setattr(time_off, field, value)

    try:
        db.commit()
        db.refresh(time_off)

    except Exception:
        db.rollback()
        raise

    return time_off


def delete_time_off(
    db: Session,
    time_off: ProviderTimeOff
):
    db.delete(time_off)

    try:
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "message": "Time off record deleted successfully"
    }


# --------------------------------------------------
# AVAILABLE APPOINTMENT SLOTS
# --------------------------------------------------

APP_TIMEZONE = ZoneInfo("Asia/Kolkata")



def get_available_slots(
    db: Session,
    provider_id: int,
    requested_date: date,
    duration_minutes: int = 30
):
    """
    Generate available appointment slots based on:
    1. Provider's weekly availability
    2. Provider's time off
    3. Existing appointments
    4. Appointment duration
    """

    get_provider_by_id(db, provider_id)

    if duration_minutes <= 0:
        raise HTTPException(
            status_code=400,
            detail="Appointment duration must be greater than zero"
        )

    day_of_week = requested_date.weekday()

    # Get active availability for the requested weekday
    availability_slots = (
        db.query(ProviderAvailability)
        .filter(
            ProviderAvailability.provider_id == provider_id,
            ProviderAvailability.day_of_week == day_of_week,
            ProviderAvailability.is_active.is_(True)
        )
        .order_by(ProviderAvailability.start_time)
        .all()
    )

    if not availability_slots:
        return []

    # Start and end of the requested day
    day_start = datetime.combine(
        requested_date,
        datetime.min.time(),
        tzinfo=APP_TIMEZONE
    )

    day_end = day_start + timedelta(days=1)

    # Get time-off records overlapping the requested date
    time_off_records = (
        db.query(ProviderTimeOff)
        .filter(
            ProviderTimeOff.provider_id == provider_id,
            ProviderTimeOff.start_datetime < day_end,
            ProviderTimeOff.end_datetime > day_start
        )
        .all()
    )

    # Get appointments overlapping the requested date
    appointments = (
        db.query(Appointment)
        .filter(
            Appointment.provider_id == provider_id,
            Appointment.start_datetime < day_end,
            Appointment.end_datetime > day_start,
            Appointment.status.notin_([
                AppointmentStatus.CANCELLED,
                AppointmentStatus.NO_SHOW
            ])
        )
        .all()
    )

    # Normalize database datetimes for consistent comparison
    def normalize_datetime(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=APP_TIMEZONE)

        return value.astimezone(APP_TIMEZONE)

    now = datetime.now(APP_TIMEZONE)
    duration = timedelta(minutes=duration_minutes)

    available_slots = []

    for availability in availability_slots:

        slot_start = datetime.combine(
            requested_date,
            availability.start_time,
            tzinfo=APP_TIMEZONE
        )

        availability_end = datetime.combine(
            requested_date,
            availability.end_time,
            tzinfo=APP_TIMEZONE
        )

        while slot_start + duration <= availability_end:

            slot_end = slot_start + duration

            # Skip past slots
            if slot_start <= now:
                slot_start += duration
                continue

            # Check time-off overlap
            overlaps_time_off = any(
                slot_start < normalize_datetime(record.end_datetime)
                and slot_end > normalize_datetime(record.start_datetime)
                for record in time_off_records
            )

            # Check appointment overlap
            overlaps_appointment = any(
                slot_start < normalize_datetime(appointment.end_datetime)
                and slot_end > normalize_datetime(appointment.start_datetime)
                for appointment in appointments
            )

            if not overlaps_time_off and not overlaps_appointment:
                available_slots.append({
                    "start_datetime": slot_start,
                    "end_datetime": slot_end
                })

            slot_start += duration

    return available_slots
