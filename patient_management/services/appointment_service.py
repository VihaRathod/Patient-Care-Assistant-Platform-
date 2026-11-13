
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.patient import Patient
from models.provider import Provider
from models.appointment import (
    Appointment,
    AppointmentStatus,
)
from models.provider_availability import ProviderAvailability
from models.provider_time_off import ProviderTimeOff
from models.user import User, UserRole
from datetime import date


from utils.query import apply_sort, paginate_query

APP_TIMEZONE = ZoneInfo("Asia/Kolkata")
APPOINTMENT_SORT_FIELDS = {
    "id",
    "start_datetime",
    "end_datetime",
    "created_at"
}

# --------------------------------------------------
# Common helpers
# --------------------------------------------------

def normalize_datetime(value: datetime) -> datetime:
    """
    Convert a timezone-aware datetime to Asia/Kolkata.
    Naive database datetimes are treated as Asia/Kolkata.
    """

    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=APP_TIMEZONE)

    return value.astimezone(APP_TIMEZONE)


def commit_changes(db: Session):
    """
    Commit changes and rollback if the transaction fails.
    """

    try:
        db.commit()

    except Exception:
        db.rollback()
        raise


# --------------------------------------------------
# Profile helpers
# --------------------------------------------------

def get_patient_profile(db: Session, user_id: int):

    patient = (
        db.query(Patient)
        .filter(Patient.user_id == user_id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found"
        )

    return patient


def get_provider_profile(db: Session, user_id: int):

    provider = (
        db.query(Provider)
        .filter(Provider.user_id == user_id)
        .first()
    )

    if not provider:
        raise HTTPException(
            status_code=404,
            detail="Provider profile not found"
        )

    return provider


# --------------------------------------------------
# Provider schedule validation
# --------------------------------------------------

def validate_provider_schedule(
    db: Session,
    provider_id: int,
    start_datetime: datetime,
    end_datetime: datetime,
    exclude_appointment_id: int | None = None
):

    # Check timezone awareness

    if (
        start_datetime.tzinfo is None
        or start_datetime.utcoffset() is None
        or end_datetime.tzinfo is None
        or end_datetime.utcoffset() is None
    ):
        raise HTTPException(
            status_code=400,
            detail="Appointment datetimes must include timezone information"
        )

    # Normalize to application timezone

    start_datetime = normalize_datetime(start_datetime)
    end_datetime = normalize_datetime(end_datetime)

    if start_datetime >= end_datetime:
        raise HTTPException(
            status_code=400,
            detail="End datetime must be after start datetime"
        )

    # Appointments must be on the same local day

    if start_datetime.date() != end_datetime.date():
        raise HTTPException(
            status_code=400,
            detail="Appointments must start and end on the same day"
        )

    day_of_week = start_datetime.weekday()

    start_time = start_datetime.time().replace(tzinfo=None)
    end_time = end_datetime.time().replace(tzinfo=None)

    # 1. Check weekly provider availability

    availability = (
        db.query(ProviderAvailability)
        .filter(
            ProviderAvailability.provider_id == provider_id,
            ProviderAvailability.day_of_week == day_of_week,
            ProviderAvailability.is_active.is_(True)
        )
        .all()
    )

    is_available = any(
        slot.start_time <= start_time
        and slot.end_time >= end_time
        for slot in availability
    )

    if not is_available:
        raise HTTPException(
            status_code=400,
            detail="Provider is not available during this time"
        )

    # 2. Check provider time off

    time_off = (
        db.query(ProviderTimeOff)
        .filter(
            ProviderTimeOff.provider_id == provider_id,
            ProviderTimeOff.start_datetime < end_datetime,
            ProviderTimeOff.end_datetime > start_datetime
        )
        .first()
    )

    if time_off:
        raise HTTPException(
            status_code=409,
            detail="Provider is unavailable due to scheduled time off"
        )

    # 3. Check overlapping appointments

    overlap_query = (
        db.query(Appointment)
        .filter(
            Appointment.provider_id == provider_id,
            Appointment.status.notin_([
                AppointmentStatus.CANCELLED,
                AppointmentStatus.NO_SHOW
            ]),
            Appointment.start_datetime < end_datetime,
            Appointment.end_datetime > start_datetime
        )
    )

    if exclude_appointment_id is not None:
        overlap_query = overlap_query.filter(
            Appointment.id != exclude_appointment_id
        )

    if overlap_query.first():
        raise HTTPException(
            status_code=409,
            detail="Provider already has an appointment during this time"
        )


# --------------------------------------------------
# Create appointment
# --------------------------------------------------

def create_appointment(
    db: Session,
    current_user: User,
    appointment_data: dict
):

    patient = get_patient_profile(db, current_user.id)

    # Make sure the provider exists and is active

    provider = (
        db.query(Provider)
        .join(User, Provider.user_id == User.id)
        .filter(
            Provider.id == appointment_data["provider_id"],
            User.is_active.is_(True)
        )
        .first()
    )

    if not provider:
        raise HTTPException(
            status_code=404,
            detail="Active provider not found"
        )

    start_datetime = appointment_data["start_datetime"]
    end_datetime = appointment_data["end_datetime"]

    validate_provider_schedule(
        db=db,
        provider_id=provider.id,
        start_datetime=start_datetime,
        end_datetime=end_datetime
    )

    appointment = Appointment(
        patient_id=patient.id,
        **appointment_data
    )

    db.add(appointment)

    commit_changes(db)
    db.refresh(appointment)

    return appointment


# --------------------------------------------------
# List appointments
# --------------------------------------------------

def get_appointments(
    db: Session,
    page: int = 1,
    limit: int = 10,
    appointment_date: date | None = None,
    provider_id: int | None = None,
    appointment_status=None,
    sort: str | None = None
):

    query = db.query(Appointment)

    # 1. Filter by appointment date
    if appointment_date is not None:
        query = query.filter(
            func.date(Appointment.start_datetime) == appointment_date
        )

    # 2. Filter by provider
    if provider_id is not None:
        query = query.filter(
            Appointment.provider_id == provider_id
        )

    # 3. Filter by appointment status
    if appointment_status is not None:
        query = query.filter(
            Appointment.status == appointment_status
        )

    # 4. Sorting
    query = apply_sort(
        query,
        Appointment,
        sort,
        APPOINTMENT_SORT_FIELDS
    )

    # Default sorting when no sort is supplied
    if not sort:
        query = query.order_by(
            Appointment.start_datetime.desc()
        )

    # 5. Pagination
    return paginate_query(
        query,
        page,
        limit
    )


# --------------------------------------------------
# Get appointment by ID
# --------------------------------------------------

def get_appointment_by_id(
    db: Session,
    appointment_id: int,
    current_user: User
):

    appointment = (
        db.query(Appointment)
        .filter(Appointment.id == appointment_id)
        .first()
    )

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    if current_user.role == UserRole.PATIENT:

        patient = get_patient_profile(db, current_user.id)

        if appointment.patient_id != patient.id:
            raise HTTPException(
                status_code=403,
                detail="You cannot access this appointment"
            )

    elif current_user.role == UserRole.PROVIDER:

        provider = get_provider_profile(db, current_user.id)

        if appointment.provider_id != provider.id:
            raise HTTPException(
                status_code=403,
                detail="You cannot access this appointment"
            )

    elif current_user.role != UserRole.ADMIN:

        raise HTTPException(
            status_code=403,
            detail="You cannot access this appointment"
        )

    return appointment


# --------------------------------------------------
# Update appointment details
# --------------------------------------------------

def update_appointment(
    db: Session,
    appointment: Appointment,
    update_data: dict
):

    if appointment.status in (
        AppointmentStatus.CANCELLED,
        AppointmentStatus.COMPLETED,
        AppointmentStatus.NO_SHOW
    ):
        raise HTTPException(
            status_code=400,
            detail="This appointment can no longer be updated"
        )

    # Do not allow null for required fields

    for field in (
        "appointment_type",
        "start_datetime",
        "end_datetime"
    ):
        if field in update_data and update_data[field] is None:
            raise HTTPException(
                status_code=400,
                detail=f"{field} cannot be null"
            )

    new_start = update_data.get(
        "start_datetime",
        appointment.start_datetime
    )

    new_end = update_data.get(
        "end_datetime",
        appointment.end_datetime
    )

    new_start = normalize_datetime(new_start)
    new_end = normalize_datetime(new_end)

    if new_start >= new_end:
        raise HTTPException(
            status_code=400,
            detail="End datetime must be after start datetime"
        )

    # Revalidate schedule if either time changes

    if (
        "start_datetime" in update_data
        or "end_datetime" in update_data
    ):

        validate_provider_schedule(
            db=db,
            provider_id=appointment.provider_id,
            start_datetime=new_start,
            end_datetime=new_end,
            exclude_appointment_id=appointment.id
        )

        update_data["start_datetime"] = new_start
        update_data["end_datetime"] = new_end

    for field, value in update_data.items():
        setattr(appointment, field, value)

    commit_changes(db)
    db.refresh(appointment)

    return appointment


# --------------------------------------------------
# Appointment status transitions
# --------------------------------------------------

def change_appointment_status(
    db: Session,
    appointment: Appointment,
    new_status: AppointmentStatus,
    allowed_current_statuses: tuple
):

    if appointment.status not in allowed_current_statuses:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot change appointment from "
                f"{appointment.status.value} to {new_status.value}"
            )
        )

    appointment.status = new_status

    commit_changes(db)
    db.refresh(appointment)

    return appointment


def confirm_appointment(db: Session, appointment: Appointment):

    return change_appointment_status(
        db,
        appointment,
        AppointmentStatus.CONFIRMED,
        (AppointmentStatus.SCHEDULED,)
    )


def check_in_appointment(db: Session, appointment: Appointment):

    return change_appointment_status(
        db,
        appointment,
        AppointmentStatus.CHECKED_IN,
        (AppointmentStatus.CONFIRMED,)
    )


def complete_appointment(db: Session, appointment: Appointment):

    return change_appointment_status(
        db,
        appointment,
        AppointmentStatus.COMPLETED,
        (AppointmentStatus.CHECKED_IN,)
    )


def mark_appointment_no_show(db: Session, appointment: Appointment):

    return change_appointment_status(
        db,
        appointment,
        AppointmentStatus.NO_SHOW,
        (
            AppointmentStatus.SCHEDULED,
            AppointmentStatus.CONFIRMED
        )
    )


# --------------------------------------------------
# Cancel appointment
# --------------------------------------------------

def cancel_appointment(
    db: Session,
    appointment: Appointment
):

    return change_appointment_status(
        db,
        appointment,
        AppointmentStatus.CANCELLED,
        (
            AppointmentStatus.SCHEDULED,
            AppointmentStatus.CONFIRMED
        )
    )
