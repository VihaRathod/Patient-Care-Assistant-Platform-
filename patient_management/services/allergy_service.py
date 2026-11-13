
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.user import User, UserRole
from models.patient import Patient
from models.provider import Provider
from models.allergy import Allergy
from models.patient_allergy import (
    PatientAllergy,
    AllergySeverity
)
from models.appointment import Appointment

from utils.query import (
    apply_sort,
    paginate_query
)


# ==================================================
# SORTING CONFIGURATION
# ==================================================

ALLERGY_SORT_FIELDS = {
    "id",
    "name"
}

PATIENT_ALLERGY_SORT_FIELDS = {
    "id",
    "allergy_id",
    "severity"
}


# ==================================================
# ALLERGY CATALOG
# ==================================================

def create_allergy(db: Session, data: dict):

    existing = (
        db.query(Allergy)
        .filter(Allergy.name.ilike(data["name"].strip()))
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This allergy already exists"
        )

    allergy = Allergy(
        **{**data, "name": data["name"].strip()}
    )

    try:
        db.add(allergy)
        db.commit()
        db.refresh(allergy)
    except Exception:
        db.rollback()
        raise

    return allergy


def get_all_allergies(
    db: Session,
    page: int = 1,
    limit: int = 10,
    name: str | None = None,
    description: str | None = None,
    sort: str | None = None
):

    query = db.query(Allergy)

    # Filter by allergy name
    if name:
        query = query.filter(
            Allergy.name.ilike(f"%{name.strip()}%")
        )

    # Filter by description
    if description:
        query = query.filter(
            Allergy.description.ilike(
                f"%{description.strip()}%"
            )
        )

    # Apply sorting
    query = apply_sort(
        query,
        Allergy,
        sort,
        ALLERGY_SORT_FIELDS
    )

    if not sort:
        query = query.order_by(Allergy.name.asc())

    query = query.order_by(Allergy.id.asc())

    return paginate_query(query, page, limit)


def get_allergy_by_id(db: Session, allergy_id: int):

    allergy = (
        db.query(Allergy)
        .filter(Allergy.id == allergy_id)
        .first()
    )

    if not allergy:
        raise HTTPException(
            status_code=404,
            detail="Allergy not found"
        )

    return allergy


def update_allergy(
    db: Session,
    allergy: Allergy,
    data: dict
):

    if "name" in data and data["name"] is not None:

        new_name = data["name"].strip()

        duplicate = (
            db.query(Allergy)
            .filter(
                Allergy.name.ilike(new_name),
                Allergy.id != allergy.id
            )
            .first()
        )

        if duplicate:
            raise HTTPException(
                status_code=409,
                detail="An allergy with this name already exists"
            )

        data["name"] = new_name

    for field, value in data.items():
        setattr(allergy, field, value)

    try:
        db.commit()
        db.refresh(allergy)
    except Exception:
        db.rollback()
        raise

    return allergy


def delete_allergy(db: Session, allergy: Allergy):

    if allergy.patients:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete an allergy that is assigned to patients"
        )

    db.delete(allergy)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Allergy deleted successfully"
    }


# ==================================================
# PATIENT ACCESS HELPERS
# ==================================================

def get_patient_by_id(db: Session, patient_id: int):

    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    return patient


def get_current_patient(current_user: User):

    if current_user.patient is None:
        raise HTTPException(
            status_code=403,
            detail="Your account does not have a patient profile"
        )

    return current_user.patient


def get_current_provider(db: Session, current_user: User):

    provider = (
        db.query(Provider)
        .filter(Provider.user_id == current_user.id)
        .first()
    )

    if not provider:
        raise HTTPException(
            status_code=403,
            detail="Your account does not have a provider profile"
        )

    return provider


def ensure_provider_has_patient_access(
    db: Session,
    provider_id: int,
    patient_id: int
):

    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.provider_id == provider_id,
            Appointment.patient_id == patient_id
        )
        .first()
    )

    if not appointment:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to access this patient's records"
        )


def authorize_patient_access(
    db: Session,
    current_user: User,
    patient_id: int
):

    if current_user.role == UserRole.ADMIN:
        get_patient_by_id(db, patient_id)
        return

    if current_user.role == UserRole.PATIENT:

        patient = get_current_patient(current_user)

        if patient.id != patient_id:
            raise HTTPException(
                status_code=403,
                detail="You can only access your own allergy records"
            )

        return

    if current_user.role == UserRole.PROVIDER:

        provider = get_current_provider(db, current_user)

        ensure_provider_has_patient_access(
            db,
            provider.id,
            patient_id
        )

        return

    raise HTTPException(
        status_code=403,
        detail="Access denied"
    )


# ==================================================
# PATIENT ALLERGY RECORDS
# ==================================================

def create_patient_allergy(
    db: Session,
    patient_id: int,
    data: dict
):

    get_patient_by_id(db, patient_id)

    # Ensure the allergy exists
    get_allergy_by_id(db, data["allergy_id"])

    existing = (
        db.query(PatientAllergy)
        .filter(
            PatientAllergy.patient_id == patient_id,
            PatientAllergy.allergy_id == data["allergy_id"]
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="This allergy is already recorded for this patient"
        )

    record = PatientAllergy(
        patient_id=patient_id,
        **data
    )

    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        raise

    return record


def get_patient_allergies(
    db: Session,
    patient_id: int,
    page: int = 1,
    limit: int = 10,
    allergy_id: int | None = None,
    severity: AllergySeverity | None = None,
    sort: str | None = None
):

    # Check whether patient exists
    get_patient_by_id(db, patient_id)

    # Get only this patient's allergy records
    query = (
        db.query(PatientAllergy)
        .filter(PatientAllergy.patient_id == patient_id)
    )

    # Filter by allergy ID
    if allergy_id is not None:
        query = query.filter(
            PatientAllergy.allergy_id == allergy_id
        )

    # Filter by severity
    if severity is not None:
        query = query.filter(
            PatientAllergy.severity == severity
        )

    # Apply sorting
    query = apply_sort(
        query,
        PatientAllergy,
        sort,
        PATIENT_ALLERGY_SORT_FIELDS
    )

    # Default sorting
    if not sort:
        query = query.order_by(PatientAllergy.id.desc())
    else:
        query = query.order_by(PatientAllergy.id.desc())

    # Pagination
    return paginate_query(query, page, limit)


def get_patient_allergy_by_id(
    db: Session,
    record_id: int
):

    record = (
        db.query(PatientAllergy)
        .filter(PatientAllergy.id == record_id)
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Patient allergy record not found"
        )

    return record


def update_patient_allergy(
    db: Session,
    record: PatientAllergy,
    data: dict
):

    for field, value in data.items():
        setattr(record, field, value)

    try:
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        raise

    return record


def delete_patient_allergy(
    db: Session,
    record: PatientAllergy
):

    db.delete(record)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Patient allergy record deleted successfully"
    }
