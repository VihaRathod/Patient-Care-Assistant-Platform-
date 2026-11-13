
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from dependencies.auth import require_roles
from models.user import User

from schemas.visit_note import (
    VisitNoteCreate,
    VisitNoteUpdate,
    VisitNoteResponse,
)

from services.visit_note_service import (
    create_visit_note,
    get_visit_notes,
    get_visit_note_by_id,
    get_visit_note_by_appointment_id,
    update_visit_note,
)


router = APIRouter(
    prefix="/visit-notes",
    tags=["Visit Notes"]
)


# --------------------------------------------------
# Create visit note
# --------------------------------------------------

@router.post(
    "/",
    response_model=VisitNoteResponse,
    status_code=201
)
def create_note(
    note_data: VisitNoteCreate,
    current_user: User = Depends(
        require_roles("PROVIDER")
    ),
    db: Session = Depends(get_db)
):

    return create_visit_note(
        db,
        current_user,
        note_data.model_dump()
    )


# --------------------------------------------------
# List visit notes for current user
# --------------------------------------------------

@router.get(
    "/",
    response_model=list[VisitNoteResponse]
)
def list_visit_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(
        require_roles("PATIENT", "PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):

    return get_visit_notes(
        db,
        current_user,
        skip,
        limit
    )


# --------------------------------------------------
# Get visit note by appointment ID
# --------------------------------------------------

@router.get(
    "/appointment/{appointment_id}",
    response_model=VisitNoteResponse
)
def get_note_by_appointment(
    appointment_id: int,
    current_user: User = Depends(
        require_roles("PATIENT", "PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):

    return get_visit_note_by_appointment_id(
        db,
        appointment_id,
        current_user
    )


# --------------------------------------------------
# Get visit note by note ID
# --------------------------------------------------

@router.get(
    "/{note_id}",
    response_model=VisitNoteResponse
)
def get_note(
    note_id: int,
    current_user: User = Depends(
        require_roles("PATIENT", "PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):

    return get_visit_note_by_id(
        db,
        note_id,
        current_user
    )


# --------------------------------------------------
# Update visit note
# --------------------------------------------------

@router.patch(
    "/{note_id}",
    response_model=VisitNoteResponse
)
def edit_visit_note(
    note_id: int,
    note_data: VisitNoteUpdate,
    current_user: User = Depends(
        require_roles("PROVIDER")
    ),
    db: Session = Depends(get_db)
):

    visit_note = get_visit_note_by_id(
        db,
        note_id,
        current_user
    )

    update_data = note_data.model_dump(
        exclude_unset=True
    )

    return update_visit_note(
        db,
        visit_note,
        current_user,
        update_data
    )
