
import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.visit_note import VisitNote
from models.appointment import Appointment, AppointmentStatus
from models.patient import Patient
from models.provider import Provider
from models.user import User, UserRole

from services.appointment_service import get_appointment_by_id


logger = logging.getLogger(__name__)


def _refresh_rag_index(db: Session, visit_note: VisitNote) -> None:
    """Indexing must not prevent a clinical note from being saved."""
    try:
        from agents.rag import RAGServiceError, index_visit_note

        index_visit_note(db, visit_note)
    except RAGServiceError as error:
        logger.warning("Visit note %s was saved but not indexed: %s", visit_note.id, error)
    except Exception:
        logger.exception("Visit note %s was saved but RAG indexing failed", visit_note.id)


# --------------------------------------------------
# Common database helper
# --------------------------------------------------

def commit_changes(db: Session):

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
# Create visit note
# --------------------------------------------------

def create_visit_note(
    db: Session,
    current_user: User,
    note_data: dict
):

    # Only a provider can create a clinical note

    if current_user.role != UserRole.PROVIDER:
        raise HTTPException(
            status_code=403,
            detail="Only providers can create visit notes"
        )

    provider = get_provider_profile(
        db,
        current_user.id
    )

    # Find the appointment

    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == note_data["appointment_id"]
        )
        .first()
    )

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    # Make sure this appointment belongs to the provider

    if appointment.provider_id != provider.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot create a note for this appointment"
        )

    # Notes can be created once the visit has started
    # or after it has been completed

    if appointment.status not in (
        AppointmentStatus.CHECKED_IN,
        AppointmentStatus.COMPLETED
    ):
        raise HTTPException(
            status_code=400,
            detail="Visit notes can only be created for checked-in or completed appointments"
        )

    # One note is allowed per appointment

    existing_note = (
        db.query(VisitNote)
        .filter(
            VisitNote.appointment_id == appointment.id
        )
        .first()
    )

    if existing_note:
        raise HTTPException(
            status_code=409,
            detail="A visit note already exists for this appointment"
        )

    visit_note = VisitNote(
        **note_data
    )

    db.add(visit_note)

    commit_changes(db)
    db.refresh(visit_note)

    _refresh_rag_index(db, visit_note)

    return visit_note


# --------------------------------------------------
# List visit notes for current user
# --------------------------------------------------

def get_visit_notes(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 20
):

    query = (
        db.query(VisitNote)
        .join(
            Appointment,
            VisitNote.appointment_id == Appointment.id
        )
    )

    if current_user.role == UserRole.PATIENT:

        patient = get_patient_profile(
            db,
            current_user.id
        )

        query = query.filter(
            Appointment.patient_id == patient.id
        )

    elif current_user.role == UserRole.PROVIDER:

        provider = get_provider_profile(
            db,
            current_user.id
        )

        query = query.filter(
            Appointment.provider_id == provider.id
        )

    elif current_user.role != UserRole.ADMIN:

        raise HTTPException(
            status_code=403,
            detail="You cannot access visit notes"
        )

    return (
        query
        .order_by(VisitNote.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# --------------------------------------------------
# Get visit note by ID
# --------------------------------------------------

def get_visit_note_by_id(
    db: Session,
    note_id: int,
    current_user: User
):

    visit_note = (
        db.query(VisitNote)
        .filter(VisitNote.id == note_id)
        .first()
    )

    if not visit_note:
        raise HTTPException(
            status_code=404,
            detail="Visit note not found"
        )

    # Reuse appointment ownership checks

    get_appointment_by_id(
        db,
        visit_note.appointment_id,
        current_user
    )

    return visit_note


# --------------------------------------------------
# Get visit note by appointment ID
# --------------------------------------------------

def get_visit_note_by_appointment_id(
    db: Session,
    appointment_id: int,
    current_user: User
):

    # Verify the current user can access this appointment

    get_appointment_by_id(
        db,
        appointment_id,
        current_user
    )

    visit_note = (
        db.query(VisitNote)
        .filter(
            VisitNote.appointment_id == appointment_id
        )
        .first()
    )

    if not visit_note:
        raise HTTPException(
            status_code=404,
            detail="Visit note not found for this appointment"
        )

    return visit_note


# --------------------------------------------------
# Update visit note
# --------------------------------------------------

def update_visit_note(
    db: Session,
    visit_note: VisitNote,
    current_user: User,
    update_data: dict
):

    # Only the provider assigned to the appointment
    # can update its clinical note

    if current_user.role != UserRole.PROVIDER:
        raise HTTPException(
            status_code=403,
            detail="Only the assigned provider can update this visit note"
        )

    provider = get_provider_profile(
        db,
        current_user.id
    )

    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == visit_note.appointment_id
        )
        .first()
    )

    if not appointment or appointment.provider_id != provider.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot update this visit note"
        )

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No visit note fields provided for update"
        )

    # Summary is required and cannot be set to null

    if (
        "summary" in update_data
        and update_data["summary"] is None
    ):
        raise HTTPException(
            status_code=400,
            detail="Summary cannot be null"
        )

    for field, value in update_data.items():
        setattr(visit_note, field, value)

    commit_changes(db)
    db.refresh(visit_note)

    _refresh_rag_index(db, visit_note)

    return visit_note
