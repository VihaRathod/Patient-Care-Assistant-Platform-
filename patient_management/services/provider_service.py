
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.provider import Provider
from models.user import User, UserRole


def create_provider(
    db: Session,
    provider_data: dict
):
    user_id = provider_data["user_id"]

    # Check whether the user exists
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Only PROVIDER users can have provider profiles
    if user.role != UserRole.PROVIDER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must have PROVIDER role"
        )

    # Check whether a provider profile already exists
    existing_provider = (
        db.query(Provider)
        .filter(Provider.user_id == user_id)
        .first()
    )

    if existing_provider:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Provider profile already exists"
        )

    provider = Provider(**provider_data)

    db.add(provider)
    db.commit()
    db.refresh(provider)

    return provider


def get_all_providers(
    db: Session,
    skip: int = 0,
    limit: int = 20
):
    return (
        db.query(Provider)
        .join(User, Provider.user_id == User.id)
        .filter(User.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_provider_by_id(
    db: Session,
    provider_id: int
):
    provider = (
        db.query(Provider)
        .filter(Provider.id == provider_id)
        .first()
    )

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )

    return provider


def get_provider_by_user_id(
    db: Session,
    user_id: int
):
    provider = (
        db.query(Provider)
        .filter(Provider.user_id == user_id)
        .first()
    )

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider profile not found"
        )

    return provider


def update_provider(
    db: Session,
    provider: Provider,
    update_data: dict
):
    for field, value in update_data.items():
        setattr(provider, field, value)

    db.commit()
    db.refresh(provider)

    return provider
