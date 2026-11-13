
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.patient import Patient
from models.user import User
from datetime import date

from sqlalchemy import or_

from utils.query import (
    apply_sort,
    paginate_query
)

PATIENT_SORT_FIELDS = {
    "id",
    "first_name",
    "last_name",
    "date_of_birth",
    "gender"
}
def get_patient_by_user_id(
    db: Session,
    user_id: int
):
    patient = (
        db.query(Patient)
        .filter(Patient.user_id == user_id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )

    return patient


def get_all_patients(
    db: Session,
    page: int = 1,
    limit: int = 10,
    first_name: str | None = None,
    last_name: str | None = None,
    gender: str | None = None,
    date_of_birth: date | None = None,
    sort: str | None = None
):

    query = (
        db.query(Patient)
        .join(User, Patient.user_id == User.id)
        .filter(User.is_active == True)
    )

    # 1. Filter by first name
    if first_name:
        query = query.filter(
            Patient.first_name.ilike(
                f"%{first_name.strip()}%"
            )
        )

    # 2. Filter by last name
    if last_name:
        query = query.filter(
            Patient.last_name.ilike(
                f"%{last_name.strip()}%"
            )
        )

    # 3. Filter by gender
    if gender:
        query = query.filter(
            Patient.gender.ilike(
                gender.strip()
            )
        )

    # 4. Filter by date of birth
    if date_of_birth is not None:
        query = query.filter(
            Patient.date_of_birth == date_of_birth
        )

    # 5. Sorting
    query = apply_sort(
        query,
        Patient,
        sort,
        PATIENT_SORT_FIELDS
    )

    # Default sorting
    if not sort:
        query = query.order_by(
            Patient.id.asc()
        )

    # Stable secondary ordering
    query = query.order_by(
        Patient.id.asc()
    )

    # 6. Pagination
    return paginate_query(
        query,
        page,
        limit
    )


def get_patient_by_id(
    db: Session,
    patient_id: int
):
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    return patient


def update_patient(
    db: Session,
    patient: Patient,
    update_data: dict
):
    for field, value in update_data.items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)

    return patient
