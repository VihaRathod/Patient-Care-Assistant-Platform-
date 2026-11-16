
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from dependencies.auth import require_roles

from models.user import User
from schemas.provider import (
    ProviderUpdate,
    ProviderResponse
)

from services.provider_service import (
    get_all_providers,
    get_provider_by_id,
    get_provider_by_user_id,
    update_provider
)
from datetime import date

from schemas.available_slot import AvailableSlotResponse
from services.availability_service import get_available_slots


router = APIRouter(
    prefix="/providers",
    tags=["Providers"]
)


# View all active providers
@router.get(
    "/",
    response_model=list[ProviderResponse]
)
def list_providers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(
        require_roles(
            "PATIENT",
            "PROVIDER",
            "ADMIN"
        )
    ),
    db: Session = Depends(get_db)
):
    return get_all_providers(
        db,
        skip,
        limit
    )


# Provider views their own profile
@router.get(
    "/me",
    response_model=ProviderResponse
)
def get_my_provider_profile(
    current_user: User = Depends(
        require_roles("PROVIDER")
    ),
    db: Session = Depends(get_db)
):
    return get_provider_by_user_id(
        db,
        current_user.id
    )


# Provider updates their own profile
@router.patch(
    "/me",
    response_model=ProviderResponse
)
def update_my_provider_profile(
    provider_data: ProviderUpdate,
    current_user: User = Depends(
        require_roles("PROVIDER")
    ),
    db: Session = Depends(get_db)
):
    provider = get_provider_by_user_id(
        db,
        current_user.id
    )

    update_data = provider_data.model_dump(
        exclude_unset=True
    )

    return update_provider(
        db,
        provider,
        update_data
    )


# View a particular provider
@router.get(
    "/{provider_id}",
    response_model=ProviderResponse
)
def get_provider(
    provider_id: int,
    current_user: User = Depends(
        require_roles(
            "PATIENT",
            "PROVIDER",
            "ADMIN"
        )
    ),
    db: Session = Depends(get_db)
):
    return get_provider_by_id(
        db,
        provider_id
    )


# Admin updates a provider profile
@router.patch(
    "/{provider_id}",
    response_model=ProviderResponse
)
def update_provider_by_admin(
    provider_id: int,
    provider_data: ProviderUpdate,
    current_user: User = Depends(
        require_roles("ADMIN")
    ),
    db: Session = Depends(get_db)
):
    provider = get_provider_by_id(
        db,
        provider_id
    )

    update_data = provider_data.model_dump(
        exclude_unset=True
    )

    return update_provider(
        db,
        provider,
        update_data
    )



# Get available appointment slots for a provider
@router.get(
    "/{provider_id}/available-slots",
    response_model=list[AvailableSlotResponse]
)
def list_available_slots(
    provider_id: int,
    requested_date: date = Query(..., alias="date"),
    duration_minutes: int = Query(30, ge=5, le=240),
    current_user: User = Depends(
        require_roles("PATIENT", "PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):
    return get_available_slots(
        db=db,
        provider_id=provider_id,
        requested_date=requested_date,
        duration_minutes=duration_minutes
    )
