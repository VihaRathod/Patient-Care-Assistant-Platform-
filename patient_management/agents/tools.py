"""Narrow, read-only tools available to the appointment concierge.

The model never receives a database session or unrestricted query capability.
These functions are also useful for the deterministic fallback used when an
OpenAI key has not been configured in a local development environment.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from models.provider import Provider
from models.provider_specialty import ProviderSpecialty
from models.specialty import Specialty
from models.user import User
from services.availability_service import get_available_slots


def search_specialties(db: Session, query: str) -> list[dict]:
    """Return catalog specialties whose name or description matches ``query``."""
    text = query.strip()
    if not text:
        return []
    rows = (
        db.query(Specialty)
        .filter(
            Specialty.name.ilike(f"%{text}%")
            | Specialty.description.ilike(f"%{text}%")
        )
        .order_by(Specialty.name)
        .limit(10)
        .all()
    )
    return [{"id": item.id, "name": item.name, "description": item.description} for item in rows]


def list_specialties(db: Session) -> list[dict]:
    rows = db.query(Specialty).order_by(Specialty.name).all()
    return [{"id": item.id, "name": item.name, "description": item.description} for item in rows]


def find_active_providers(db: Session, specialty_ids: list[int] | None = None) -> list[dict]:
    query = db.query(Provider).join(User, Provider.user_id == User.id).filter(User.is_active.is_(True))
    if specialty_ids:
        query = query.join(ProviderSpecialty).filter(ProviderSpecialty.specialty_id.in_(specialty_ids))
    providers = query.order_by(Provider.id).all()
    specialty_rows = (
        db.query(ProviderSpecialty.provider_id, Specialty.name)
        .join(Specialty, ProviderSpecialty.specialty_id == Specialty.id)
        .filter(ProviderSpecialty.provider_id.in_([provider.id for provider in providers]))
        .all()
        if providers else []
    )
    names_by_provider: dict[int, list[str]] = {}
    for provider_id, specialty_name in specialty_rows:
        names_by_provider.setdefault(provider_id, []).append(specialty_name)
    return [
        {
            "id": provider.id,
            "name": f"{provider.first_name} {provider.last_name}",
            "specialties": names_by_provider.get(provider.id, []),
        }
        for provider in providers
    ]


def find_earliest_slots(
    db: Session,
    providers: list[dict],
    start_date: date,
    search_days: int,
    duration_minutes: int,
    limit: int = 4,
) -> list[dict]:
    """Search real provider calendars and return chronologically sorted slots."""
    slots: list[dict] = []
    for offset in range(search_days):
        requested_date = start_date + timedelta(days=offset)
        for provider in providers:
            for slot in get_available_slots(db, provider["id"], requested_date, duration_minutes):
                slots.append({**provider, **slot})
    slots.sort(key=lambda item: (item["start_datetime"], item["provider_id"] if "provider_id" in item else item["id"]))
    return slots[:limit]
