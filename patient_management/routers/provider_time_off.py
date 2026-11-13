
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from dependencies.auth import require_roles

from models.user import User

from schemas.provider_time_off import (
    ProviderTimeOffCreate,
    ProviderTimeOffUpdate,
    ProviderTimeOffResponse
)

from services.availability_service import (
    resolve_provider_id,
    get_provider_time_off,
    get_time_off_by_id,
    create_time_off,
    update_time_off,
    delete_time_off
)


router = APIRouter(
    prefix="/provider-time-off",
    tags=["Provider Time Off"]
)


# Create time off
@router.post(
    "/",
    response_model=ProviderTimeOffResponse,
    status_code=201
)
def add_time_off(
    time_off_data: ProviderTimeOffCreate,
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

    return create_time_off(
        db,
        target_provider_id,
        time_off_data.model_dump()
    )


# View time off
@router.get(
    "/",
    response_model=list[ProviderTimeOffResponse]
)
def list_time_off(
    provider_id: int | None = Query(default=None, gt=0),
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

    return get_provider_time_off(
        db,
        target_provider_id
    )


# Update time off
@router.patch(
    "/{time_off_id}",
    response_model=ProviderTimeOffResponse
)
def edit_time_off(
    time_off_id: int,
    time_off_data: ProviderTimeOffUpdate,
    current_user: User = Depends(
        require_roles("PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):
    time_off = get_time_off_by_id(
        db,
        time_off_id
    )

    target_provider_id = resolve_provider_id(
        db,
        current_user,
        time_off.provider_id
    )

    if target_provider_id != time_off.provider_id:
        raise HTTPException(
            status_code=403,
            detail="You cannot update another provider's time off"
        )

    update_data = time_off_data.model_dump(
        exclude_unset=True
    )

    return update_time_off(
        db,
        time_off,
        update_data
    )


# Delete time off
@router.delete(
    "/{time_off_id}"
)
def remove_time_off(
    time_off_id: int,
    current_user: User = Depends(
        require_roles("PROVIDER", "ADMIN")
    ),
    db: Session = Depends(get_db)
):
    time_off = get_time_off_by_id(
        db,
        time_off_id
    )

    target_provider_id = resolve_provider_id(
        db,
        current_user,
        time_off.provider_id
    )

    if target_provider_id != time_off.provider_id:
        raise HTTPException(
            status_code=403,
            detail="You cannot delete another provider's time off"
        )

    return delete_time_off(
        db,
        time_off
    )
