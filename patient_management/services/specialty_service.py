
from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.specialty import Specialty
from models.provider_specialty import ProviderSpecialty
from models.provider import Provider
from utils.query import apply_sort, paginate_query


SPECIALTY_SORT_FIELDS = {
    "id",
    "name"
}
# ==================================================
# SPECIALTY CATALOG
# ==================================================

def create_specialty(db: Session, data: dict):
    name = data["name"].strip()

    existing = db.query(Specialty).filter(
        Specialty.name.ilike(name)
    ).first()

    if existing:
        raise HTTPException(
            409,
            "This specialty already exists"
        )

    specialty = Specialty(
        **{**data, "name": name}
    )

    try:
        db.add(specialty)
        db.commit()
        db.refresh(specialty)
    except Exception:
        db.rollback()
        raise

    return specialty



def get_all_specialties(
    db: Session,
    page: int = 1,
    limit: int = 10,
    name: str | None = None,
    sort: str | None = None
):
    query = db.query(Specialty)

    # Filter by specialty name
    if name:
        query = query.filter(
            Specialty.name.ilike(f"%{name.strip()}%")
        )

    # Apply sorting
    query = apply_sort(
        query,
        Specialty,
        sort,
        SPECIALTY_SORT_FIELDS
    )

    # Default sorting
    if not sort:
        query = query.order_by(Specialty.name.asc())

    # Stable secondary sorting
    if not sort or "id" not in {
        field.strip().removeprefix("desc:")
        for field in sort.split(",")
    }:
        query = query.order_by(Specialty.id.asc())

    return paginate_query(
        query,
        page,
        limit
    )



def get_specialty_by_id(db: Session, specialty_id: int):
    specialty = db.query(Specialty).filter(
        Specialty.id == specialty_id
    ).first()

    if not specialty:
        raise HTTPException(404, "Specialty not found")

    return specialty


def update_specialty(db: Session, specialty: Specialty, data: dict):
    if data.get("name") is not None:
        name = data["name"].strip()

        duplicate = db.query(Specialty).filter(
            Specialty.name.ilike(name),
            Specialty.id != specialty.id
        ).first()

        if duplicate:
            raise HTTPException(
                409,
                "A specialty with this name already exists"
            )

        data["name"] = name

    for field, value in data.items():
        setattr(specialty, field, value)

    try:
        db.commit()
        db.refresh(specialty)
    except Exception:
        db.rollback()
        raise

    return specialty


def delete_specialty(db: Session, specialty: Specialty):
    if specialty.providers:
        raise HTTPException(
            409,
            "Cannot delete a specialty assigned to providers"
        )

    db.delete(specialty)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "Specialty deleted successfully"}


# ==================================================
# PROVIDER SPECIALTY ASSOCIATIONS
# ==================================================

def get_provider_by_id(db: Session, provider_id: int):
    provider = db.query(Provider).filter(
        Provider.id == provider_id
    ).first()

    if not provider:
        raise HTTPException(404, "Provider not found")

    return provider


def add_provider_specialty(
    db: Session,
    provider_id: int,
    specialty_id: int
):
    get_provider_by_id(db, provider_id)
    get_specialty_by_id(db, specialty_id)

    existing = db.query(ProviderSpecialty).filter(
        ProviderSpecialty.provider_id == provider_id,
        ProviderSpecialty.specialty_id == specialty_id
    ).first()

    if existing:
        raise HTTPException(
            409,
            "This specialty is already assigned to the provider"
        )

    association = ProviderSpecialty(
        provider_id=provider_id,
        specialty_id=specialty_id
    )

    try:
        db.add(association)
        db.commit()
        db.refresh(association)
    except Exception:
        db.rollback()
        raise

    return association


def get_provider_specialties(db: Session, provider_id: int):
    get_provider_by_id(db, provider_id)

    return (
        db.query(ProviderSpecialty)
        .filter(ProviderSpecialty.provider_id == provider_id)
        .all()
    )


def get_provider_specialty_by_id(
    db: Session,
    association_id: int
):
    association = db.query(ProviderSpecialty).filter(
        ProviderSpecialty.id == association_id
    ).first()

    if not association:
        raise HTTPException(
            404,
            "Provider specialty association not found"
        )

    return association


def remove_provider_specialty(
    db: Session,
    association: ProviderSpecialty
):
    db.delete(association)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Provider specialty removed successfully"
    }
