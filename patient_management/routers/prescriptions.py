
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from dependencies.auth import require_roles

from models.user import User
from datetime import date

from models.prescription import PrescriptionStatus
from schemas.pagination import PageResponse
from schemas.prescription import (
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionResponse
)

from services.prescription_service import (
    create_prescription,
    get_prescriptions,
    get_prescription_by_id,
    update_prescription
)


router = APIRouter(
    prefix="/prescriptions",
    tags=["Prescriptions"]
)


# Provider creates a prescription
@router.post(
    "/",
    response_model=PrescriptionResponse,
    status_code=201
)
def add_prescription(
    prescription_data: PrescriptionCreate,
    current_user: User = Depends(
        require_roles("PROVIDER")
    ),
    db: Session = Depends(get_db)
):
    return create_prescription(
        db,
        current_user,
        prescription_data.model_dump()
    )


# List prescriptions according to logged-in user's role

@router.get(
    "/",
    response_model=PageResponse[PrescriptionResponse]
)
def list_prescriptions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),

    patient_id: int | None = Query(None, gt=0),
    provider_id: int | None = Query(None, gt=0),

    status: PrescriptionStatus | None = Query(None),

    start_date: date | None = Query(None),
    end_date: date | None = Query(None),

    sort: str | None = Query(None),

    current_user: User = Depends(
        require_roles("PATIENT", "PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):
    return get_prescriptions(
        db=db,
        current_user=current_user,
        page=page,
        limit=limit,
        patient_id=patient_id,
        provider_id=provider_id,
        prescription_status=status,
        start_date=start_date,
        end_date=end_date,
        sort=sort
    )



# Get a particular prescription
@router.get(
    "/{prescription_id}",
    response_model=PrescriptionResponse
)
def get_prescription(
    prescription_id: int,
    current_user: User = Depends(
        require_roles("PATIENT", "PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):
    return get_prescription_by_id(
        db,
        prescription_id,
        current_user
    )


# Provider or admin updates a prescription
@router.patch(
    "/{prescription_id}",
    response_model=PrescriptionResponse
)
def edit_prescription(
    prescription_id: int,
    prescription_data: PrescriptionUpdate,
    current_user: User = Depends(
        require_roles("PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):
    prescription = get_prescription_by_id(
        db,
        prescription_id,
        current_user
    )

    update_data = prescription_data.model_dump(
        exclude_unset=True
    )

    return update_prescription(
        db,
        prescription,
        update_data
    )
