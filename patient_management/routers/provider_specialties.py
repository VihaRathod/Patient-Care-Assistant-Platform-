
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from dependencies.auth import require_roles
from models.user import User

from schemas.provider_speciality import (
    ProviderSpecialtyCreate,
    ProviderSpecialtyResponse
)

from services.specialty_service import (
    add_provider_specialty,
    get_provider_specialties,
    get_provider_specialty_by_id,
    remove_provider_specialty
)


router = APIRouter(
    prefix="/provider-specialties",
    tags=["Provider Specialties"]
)


@router.post(
    "/{provider_id}",
    response_model=ProviderSpecialtyResponse,
    status_code=201
)
def assign_specialty(
    provider_id: int,
    data: ProviderSpecialtyCreate,
    current_user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db)
):
    return add_provider_specialty(
        db,
        provider_id,
        data.specialty_id
    )


@router.get(
    "/{provider_id}",
    response_model=list[ProviderSpecialtyResponse]
)
def list_provider_specialties(
    provider_id: int,
    current_user: User = Depends(
        require_roles("PATIENT", "PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):
    return get_provider_specialties(db, provider_id)


@router.delete("/{association_id}")
def unassign_specialty(
    association_id: int,
    current_user: User = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db)
):
    association = get_provider_specialty_by_id(
        db,
        association_id
    )

    return remove_provider_specialty(db, association)
