
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from dependencies.auth import require_roles

from models.user import User

from schemas.provider_availability import (
    ProviderAvailabilityCreate,
    ProviderAvailabilityUpdate,
    ProviderAvailabilityResponse
)

from services.availability_service import (
    resolve_provider_id,
    get_provider_availability,
    get_availability_by_id,
    create_availability,
    update_availability,
    delete_availability
)
from datetime import date


from schemas.provider_availability import AvailableSlotResponse
from services.availability_service import get_available_slots

router = APIRouter(
    prefix="/provider-availability",
    tags=["Provider Availability"]
)


# Create availability
@router.post(
    "/",
    response_model=ProviderAvailabilityResponse,
    status_code=201
)
def add_availability(
    availability_data: ProviderAvailabilityCreate,
    provider_id: int | None = Query(default=None),
    current_user: User = Depends(
        require_roles("PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):
    target_provider_id = resolve_provider_id(
        db,
        current_user,
        provider_id
    )

    return create_availability(
        db,
        target_provider_id,
        availability_data.model_dump()
    )


# View provider availability
@router.get(
    "/",
    response_model=list[ProviderAvailabilityResponse]
)
def list_availability(
    provider_id: int = Query(..., gt=0),
    current_user: User = Depends(
        require_roles("PATIENT", "PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):
    return get_provider_availability(
        db,
        provider_id
    )


# Update availability
@router.patch(
    "/{availability_id}",
    response_model=ProviderAvailabilityResponse
)
def edit_availability(
    availability_id: int,
    availability_data: ProviderAvailabilityUpdate,
    current_user: User = Depends(
        require_roles("PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):
    availability = get_availability_by_id(
        db,
        availability_id
    )

    target_provider_id = resolve_provider_id(
        db,
        current_user,
        availability.provider_id
    )

    if target_provider_id != availability.provider_id:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=403,
            detail="You cannot update another provider's availability"
        )

    update_data = availability_data.model_dump(
        exclude_unset=True
    )

    return update_availability(
        db,
        availability,
        update_data
    )


# Delete availability
@router.delete(
    "/{availability_id}"
)
def remove_availability(
    availability_id: int,
    current_user: User = Depends(
        require_roles("PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):
    availability = get_availability_by_id(
        db,
        availability_id
    )

    target_provider_id = resolve_provider_id(
        db,
        current_user,
        availability.provider_id
    )

    if target_provider_id != availability.provider_id:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=403,
            detail="You cannot delete another provider's availability"
        )

    return delete_availability(
        db,
        availability
    )


# --------------------------------------------------
# GET AVAILABLE APPOINTMENT SLOTS
# --------------------------------------------------

@router.get(
    "/{provider_id}/available-slots",
    response_model=list[AvailableSlotResponse]
)
def list_available_slots(
    provider_id: int,
    requested_date: date = Query(..., alias="date"),
    duration_minutes: int = Query(default=30, ge=5, le=240),
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
