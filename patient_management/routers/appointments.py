
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from dependencies.auth import require_roles
from models.user import User

from schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
)

from services.appointment_service import (
    create_appointment,
    get_appointments,
    get_appointment_by_id,
    update_appointment,
    cancel_appointment,
    confirm_appointment,
    check_in_appointment,
    complete_appointment,
    mark_appointment_no_show,
)

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from dependencies.auth import get_current_user

from models.user import User
from models.appointment import AppointmentStatus

from schemas.appointment import AppointmentResponse
from schemas.pagination import PageResponse

from services.appointment_service import get_appointments
router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)


# --------------------------------------------------
# Book appointment
# --------------------------------------------------

@router.post(
    "/",
    response_model=AppointmentResponse,
    status_code=201
)
def book_appointment(
    appointment_data: AppointmentCreate,
    current_user: User = Depends(require_roles("PATIENT")),
    db: Session = Depends(get_db)
):

    return create_appointment(
        db,
        current_user,
        appointment_data.model_dump()
    )


# --------------------------------------------------
# List appointments
# --------------------------------------------------

@router.get(
    "/",
    response_model=PageResponse[AppointmentResponse]
)
def get_all(
    page: int = Query(1, ge=1),

    limit: int = Query(10, ge=1, le=100),

    appointment_date: date | None = Query(
        None,
        alias="date"
    ),

    provider_id: int | None = Query(None, ge=1),

    appointment_status: AppointmentStatus | None = Query(
        None,
        alias="status"
    ),

    sort: str | None = Query(None),

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    return get_appointments(
        db=db,
        page=page,
        limit=limit,
        appointment_date=appointment_date,
        provider_id=provider_id,
        appointment_status=appointment_status,
        sort=sort
    )


# --------------------------------------------------
# Get appointment by ID
# --------------------------------------------------

@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse
)
def get_appointment(
    appointment_id: int,
    current_user: User = Depends(
        require_roles("PATIENT", "PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):

    return get_appointment_by_id(
        db,
        appointment_id,
        current_user
    )


# --------------------------------------------------
# Update appointment details
# --------------------------------------------------

@router.patch(
    "/{appointment_id}",
    response_model=AppointmentResponse
)
def edit_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    current_user: User = Depends(
        require_roles("PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):

    appointment = get_appointment_by_id(
        db,
        appointment_id,
        current_user
    )

    update_data = appointment_data.model_dump(
        exclude_unset=True
    )

    if not update_data:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail="No appointment fields provided for update"
        )

    return update_appointment(
        db,
        appointment,
        update_data
    )


# --------------------------------------------------
# Confirm appointment
# --------------------------------------------------

@router.post(
    "/{appointment_id}/confirm",
    response_model=AppointmentResponse
)
def confirm_appointment_route(
    appointment_id: int,
    current_user: User = Depends(
        require_roles("PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):

    appointment = get_appointment_by_id(
        db,
        appointment_id,
        current_user
    )

    return confirm_appointment(
        db,
        appointment
    )


# --------------------------------------------------
# Check in patient
# --------------------------------------------------

@router.post(
    "/{appointment_id}/check-in",
    response_model=AppointmentResponse
)
def check_in_appointment_route(
    appointment_id: int,
    current_user: User = Depends(
        require_roles("PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):

    appointment = get_appointment_by_id(
        db,
        appointment_id,
        current_user
    )

    return check_in_appointment(
        db,
        appointment
    )


# --------------------------------------------------
# Complete appointment
# --------------------------------------------------

@router.post(
    "/{appointment_id}/complete",
    response_model=AppointmentResponse
)
def complete_appointment_route(
    appointment_id: int,
    current_user: User = Depends(
        require_roles("PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):

    appointment = get_appointment_by_id(
        db,
        appointment_id,
        current_user
    )

    return complete_appointment(
        db,
        appointment
    )


# --------------------------------------------------
# Mark appointment as no-show
# --------------------------------------------------

@router.post(
    "/{appointment_id}/no-show",
    response_model=AppointmentResponse
)
def mark_no_show_route(
    appointment_id: int,
    current_user: User = Depends(
        require_roles("PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):

    appointment = get_appointment_by_id(
        db,
        appointment_id,
        current_user
    )

    return mark_appointment_no_show(
        db,
        appointment
    )


# --------------------------------------------------
# Cancel appointment
# --------------------------------------------------

@router.post(
    "/{appointment_id}/cancel",
    response_model=AppointmentResponse
)
def cancel_patient_appointment(
    appointment_id: int,
    current_user: User = Depends(
        require_roles("PATIENT", "PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):

    appointment = get_appointment_by_id(
        db,
        appointment_id,
        current_user
    )

    return cancel_appointment(
        db,
        appointment
    )
