
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from dependencies.auth import get_current_user, require_roles

from models.user import User
from schemas.patient import (
    PatientUpdate,
    PatientResponse
)
from schemas.pagination import PageResponse
from datetime import date
from services.patient_service import (
    get_patient_by_user_id,
    get_all_patients,
    get_patient_by_id,
    update_patient
)


router = APIRouter(
    prefix="/patients",
    tags=["Patients"]
)


# Patient views their own profile
@router.get(
    "/me",
    response_model=PatientResponse
)
def get_my_profile(
    current_user: User = Depends(
        require_roles("PATIENT")
    ),
    db: Session = Depends(get_db)
):
    return get_patient_by_user_id(
        db,
        current_user.id
    )


# Patient updates their own profile
@router.patch(
    "/me",
    response_model=PatientResponse
)
def update_my_profile(
    patient_data: PatientUpdate,
    current_user: User = Depends(
        require_roles("PATIENT")
    ),
    db: Session = Depends(get_db)
):
    patient = get_patient_by_user_id(
        db,
        current_user.id
    )

    update_data = patient_data.model_dump(
        exclude_unset=True
    )

    return update_patient(
        db,
        patient,
        update_data
    )


# Admin views all patients
@router.get(
    "/",
    response_model=PageResponse[PatientResponse]
)
def list_patients(

    page: int = Query(1, ge=1),

    limit: int = Query(10, ge=1, le=100),

    first_name: str | None = Query(None),

    last_name: str | None = Query(None),

    gender: str | None = Query(None),

    date_of_birth: date | None = Query(None),

    sort: str | None = Query(None),

    current_user: User = Depends(
        require_roles("ADMIN")
    ),

    db: Session = Depends(get_db)
):

    return get_all_patients(
        db=db,
        page=page,
        limit=limit,
        first_name=first_name,
        last_name=last_name,
        gender=gender,
        date_of_birth=date_of_birth,
        sort=sort
    )


# Admin views a particular patient
@router.get(
    "/{patient_id}",
    response_model=PatientResponse
)
def get_patient(
    patient_id: int,
    current_user: User = Depends(
        require_roles("ADMIN")
    ),
    db: Session = Depends(get_db)
):
    return get_patient_by_id(
        db,
        patient_id
    )


# Admin updates a particular patient
@router.patch(
    "/{patient_id}",
    response_model=PatientResponse
)
def update_patient_by_admin(
    patient_id: int,
    patient_data: PatientUpdate,
    current_user: User = Depends(
        require_roles("ADMIN")
    ),
    db: Session = Depends(get_db)
):
    patient = get_patient_by_id(
        db,
        patient_id
    )

    update_data = patient_data.model_dump(
        exclude_unset=True
    )

    return update_patient(
        db,
        patient,
        update_data
    )
