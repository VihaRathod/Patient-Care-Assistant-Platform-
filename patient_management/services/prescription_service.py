
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from datetime import date, datetime, time, timedelta, timezone

from utils.query import apply_sort, paginate_query
from models.patient import Patient
from models.provider import Provider
from models.appointment import Appointment
from models.prescription import (
    Prescription,
    PrescriptionStatus
)
from models.prescription_item import PrescriptionItem
from models.user import User, UserRole


def _refresh_prescription_rag_index(db: Session, prescription: Prescription) -> None:
    """Keep searchable prescription text in sync without failing CRUD writes."""
    try:
        from agents.rag import RAGServiceError, index_prescription

        index_prescription(db, prescription)
    except RAGServiceError:
        # The prescription is already committed; the patient can be reindexed
        # after OpenAI configuration or connectivity is restored.
        return

PRESCRIPTION_SORT_FIELDS = {
    "id",
    "issued_at",
    "status"
}
def get_patient_profile(
    db: Session,
    patient_id: int
):
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    return patient


def get_provider_profile(
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
            status_code=404,
            detail="Provider profile not found"
        )

    return provider


def validate_provider_patient_relationship(
    db: Session,
    provider_id: int,
    patient_id: int,
    appointment_id: int | None
):
    # If an appointment is provided, it must belong to
    # this provider and patient.
    if appointment_id is not None:
        appointment = (
            db.query(Appointment)
            .filter(
                Appointment.id == appointment_id,
                Appointment.provider_id == provider_id,
                Appointment.patient_id == patient_id
            )
            .first()
        )

        if not appointment:
            raise HTTPException(
                status_code=400,
                detail="Appointment does not belong to this provider and patient"
            )

        if appointment.status == "CANCELLED":
            raise HTTPException(
                status_code=400,
                detail="Cannot prescribe against a cancelled appointment"
            )

        return

    # Without an appointment_id, require an existing
    # appointment relationship between this provider and patient.
    existing_appointment = (
        db.query(Appointment)
        .filter(
            Appointment.provider_id == provider_id,
            Appointment.patient_id == patient_id,
            Appointment.status != "CANCELLED"
        )
        .first()
    )

    if not existing_appointment:
        raise HTTPException(
            status_code=403,
            detail="Provider has no appointment relationship with this patient"
        )


def create_prescription(
    db: Session,
    current_user: User,
    prescription_data: dict
):
    provider = get_provider_profile(
        db,
        current_user.id
    )

    patient = get_patient_profile(
        db,
        prescription_data["patient_id"]
    )

    appointment_id = prescription_data.get("appointment_id")

    validate_provider_patient_relationship(
        db,
        provider.id,
        patient.id,
        appointment_id
    )

    items_data = prescription_data.pop("items")

    prescription = Prescription(
        patient_id=patient.id,
        provider_id=provider.id,
        appointment_id=appointment_id,
        issued_at=datetime.now(timezone.utc),
        notes=prescription_data.get("notes"),
        status=PrescriptionStatus.ACTIVE
    )

    for item_data in items_data:
        prescription.items.append(
            PrescriptionItem(**item_data)
        )

    db.add(prescription)
    db.commit()
    db.refresh(prescription)

    _refresh_prescription_rag_index(db, prescription)

    return prescription



def get_prescriptions(
    db: Session,
    current_user: User,
    page: int = 1,
    limit: int = 10,
    patient_id: int | None = None,
    provider_id: int | None = None,
    prescription_status: PrescriptionStatus | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    sort: str | None = None
):

    query = db.query(Prescription).options(
        joinedload(Prescription.items)
    )

    # -----------------------------------------
    # ROLE-BASED ACCESS
    # -----------------------------------------

    if current_user.role == UserRole.PATIENT:

        patient = (
            db.query(Patient)
            .filter(Patient.user_id == current_user.id)
            .first()
        )

        if not patient:
            raise HTTPException(
                status_code=404,
                detail="Patient profile not found"
            )

        query = query.filter(
            Prescription.patient_id == patient.id
        )

    elif current_user.role == UserRole.PROVIDER:

        provider = get_provider_profile(
            db,
            current_user.id
        )

        query = query.filter(
            Prescription.provider_id == provider.id
        )

    # -----------------------------------------
    # OPTIONAL FILTERS
    # -----------------------------------------

    if patient_id is not None:
        query = query.filter(
            Prescription.patient_id == patient_id
        )

    if provider_id is not None:
        query = query.filter(
            Prescription.provider_id == provider_id
        )

    if prescription_status is not None:
        query = query.filter(
            Prescription.status == prescription_status
        )

    # Filter by issue date
    if start_date is not None:
        start_datetime = datetime.combine(
            start_date,
            time.min,
            tzinfo=timezone.utc
        )

        query = query.filter(
            Prescription.issued_at >= start_datetime
        )

    if end_date is not None:
        end_datetime = datetime.combine(
            end_date + timedelta(days=1),
            time.min,
            tzinfo=timezone.utc
        )

        query = query.filter(
            Prescription.issued_at < end_datetime
        )

    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be after end_date"
        )

    # -----------------------------------------
    # SORTING
    # -----------------------------------------

    query = apply_sort(
        query,
        Prescription,
        sort,
        PRESCRIPTION_SORT_FIELDS
    )

    if not sort:
        query = query.order_by(
            Prescription.issued_at.desc()
        )

    # Stable secondary sorting
    query = query.order_by(Prescription.id.desc())

    # -----------------------------------------
    # PAGINATION
    # -----------------------------------------

    return paginate_query(
        query,
        page,
        limit
    )



def get_prescription_by_id(
    db: Session,
    prescription_id: int,
    current_user: User
):
    prescription = (
        db.query(Prescription)
        .options(joinedload(Prescription.items))
        .filter(Prescription.id == prescription_id)
        .first()
    )

    if not prescription:
        raise HTTPException(
            status_code=404,
            detail="Prescription not found"
        )

    if current_user.role == UserRole.PATIENT:
        patient = (
            db.query(Patient)
            .filter(Patient.user_id == current_user.id)
            .first()
        )

        if not patient or prescription.patient_id != patient.id:
            raise HTTPException(
                status_code=403,
                detail="You cannot access this prescription"
            )

    elif current_user.role == UserRole.PROVIDER:
        provider = get_provider_profile(
            db,
            current_user.id
        )

        if prescription.provider_id != provider.id:
            raise HTTPException(
                status_code=403,
                detail="You cannot access this prescription"
            )

    return prescription


def update_prescription(
    db: Session,
    prescription: Prescription,
    update_data: dict
):
    if prescription.status in (
        PrescriptionStatus.CANCELLED,
        PrescriptionStatus.COMPLETED
    ):
        raise HTTPException(
            status_code=400,
            detail="This prescription can no longer be updated"
        )

    for field, value in update_data.items():
        setattr(prescription, field, value)

    db.commit()
    db.refresh(prescription)

    _refresh_prescription_rag_index(db, prescription)

    return prescription
