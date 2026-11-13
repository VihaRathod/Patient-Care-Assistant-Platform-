
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from dependencies.auth import require_roles
from models.user import User

from schemas.patient_allergy import (
    PatientAllergyCreate,
    PatientAllergyUpdate,
    PatientAllergyResponse
)
from schemas.pagination import PageResponse
from models.patient_allergy import AllergySeverity
from services.allergy_service import (
    get_current_patient,
    get_patient_allergies,
    get_patient_allergy_by_id,
    authorize_patient_access,
    create_patient_allergy,
    update_patient_allergy,
    delete_patient_allergy
)


router = APIRouter(
    prefix="/patient-allergies",
    tags=["Patient Allergies"]
)


@router.post("/", response_model=PatientAllergyResponse, status_code=201)
def add_patient_allergy(
    data: PatientAllergyCreate,
    patient_id: int | None = Query(default=None, gt=0),
    current_user: User = Depends(
        require_roles("PATIENT", "PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):
    if current_user.role.value == "PATIENT":
        target_patient_id = get_current_patient(current_user).id
    else:
        if patient_id is None:
            from fastapi import HTTPException
            raise HTTPException(
                400,
                "patient_id is required for providers and admins"
            )

        authorize_patient_access(db, current_user, patient_id)
        target_patient_id = patient_id

    return create_patient_allergy(
        db,
        target_patient_id,
        data.model_dump()
    )


@router.get(
    "/",
    response_model=PageResponse[PatientAllergyResponse]
)
def list_patient_allergies(

    patient_id: int | None = Query(
        default=None,
        gt=0
    ),

    allergy_id: int | None = Query(
        default=None,
        gt=0
    ),

    severity: AllergySeverity | None = Query(None),

    page: int = Query(1, ge=1),

    limit: int = Query(10, ge=1, le=100),

    sort: str | None = Query(None),

    current_user: User = Depends(
        require_roles("PATIENT", "PROVIDER", "ADMIN")
    ),

    db: Session = Depends(get_db)
):

    if current_user.role.value == "PATIENT":

        target_patient_id = get_current_patient(
            current_user
        ).id

    else:

        if patient_id is None:
            from fastapi import HTTPException

            raise HTTPException(
                400,
                "patient_id is required for providers and admins"
            )

        authorize_patient_access(
            db,
            current_user,
            patient_id
        )

        target_patient_id = patient_id

    return get_patient_allergies(
        db=db,
        patient_id=target_patient_id,
        page=page,
        limit=limit,
        allergy_id=allergy_id,
        severity=severity,
        sort=sort
    )


@router.patch("/{record_id}", response_model=PatientAllergyResponse)
def edit_patient_allergy(
    record_id: int,
    data: PatientAllergyUpdate,
    current_user: User = Depends(
        require_roles("PATIENT", "PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):
    record = get_patient_allergy_by_id(db, record_id)

    authorize_patient_access(
        db,
        current_user,
        record.patient_id
    )

    return update_patient_allergy(
        db,
        record,
        data.model_dump(exclude_unset=True)
    )


@router.delete("/{record_id}")
def remove_patient_allergy(
    record_id: int,
    current_user: User = Depends(
        require_roles("PATIENT", "ADMIN")
    ),
    db: Session = Depends(get_db)
):
    record = get_patient_allergy_by_id(db, record_id)

    authorize_patient_access(
        db,
        current_user,
        record.patient_id
    )

    return delete_patient_allergy(db, record)
