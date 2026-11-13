
from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
)


def valid_patient_data():
    return {
        "first_name": "Viha",
        "last_name": "Rathod",
        "date_of_birth": date(2003, 5, 15),
        "gender": "Female",
        "phone": "9876543210",
        "address": "Ahmedabad, Gujarat",
    }


# -----------------------------
# PATIENT CREATE TESTS
# -----------------------------

def test_patient_create_valid_data():
    patient = PatientCreate(**valid_patient_data())

    assert patient.first_name == "Viha"
    assert patient.last_name == "Rathod"
    assert patient.gender == "Female"


def test_patient_create_missing_first_name():
    data = valid_patient_data()
    data.pop("first_name")

    with pytest.raises(ValidationError):
        PatientCreate(**data)


def test_patient_create_missing_last_name():
    data = valid_patient_data()
    data.pop("last_name")

    with pytest.raises(ValidationError):
        PatientCreate(**data)


def test_patient_create_missing_date_of_birth():
    data = valid_patient_data()
    data.pop("date_of_birth")

    with pytest.raises(ValidationError):
        PatientCreate(**data)


def test_patient_create_future_date_of_birth():
    data = valid_patient_data()
    data["date_of_birth"] = date.today() + timedelta(days=1)

    with pytest.raises(ValidationError):
        PatientCreate(**data)


def test_patient_create_first_name_too_short():
    data = valid_patient_data()
    data["first_name"] = "V"

    with pytest.raises(ValidationError):
        PatientCreate(**data)


def test_patient_create_first_name_too_long():
    data = valid_patient_data()
    data["first_name"] = "A" * 101

    with pytest.raises(ValidationError):
        PatientCreate(**data)


def test_patient_create_invalid_phone_length():
    data = valid_patient_data()
    data["phone"] = "123"

    with pytest.raises(ValidationError):
        PatientCreate(**data)


def test_patient_create_optional_fields_can_be_none():
    data = valid_patient_data()
    data["gender"] = None
    data["phone"] = None
    data["address"] = None

    patient = PatientCreate(**data)

    assert patient.gender is None
    assert patient.phone is None
    assert patient.address is None


# -----------------------------
# PATIENT UPDATE TESTS
# -----------------------------

def test_patient_update_valid_data():
    patient = PatientUpdate(
        first_name="Viya",
        phone="9876543210"
    )

    assert patient.first_name == "Viya"
    assert patient.phone == "9876543210"


def test_patient_update_partial_data():
    patient = PatientUpdate(first_name="Viya")

    update_data = patient.model_dump(exclude_unset=True)

    assert update_data == {"first_name": "Viya"}


def test_patient_update_empty_data():
    patient = PatientUpdate()

    update_data = patient.model_dump(exclude_unset=True)

    assert update_data == {}


def test_patient_update_future_date_of_birth():
    with pytest.raises(ValidationError):
        PatientUpdate(
            date_of_birth=date.today() + timedelta(days=1)
        )


def test_patient_update_first_name_too_short():
    with pytest.raises(ValidationError):
        PatientUpdate(first_name="V")


def test_patient_update_invalid_phone_length():
    with pytest.raises(ValidationError):
        PatientUpdate(phone="123")


def test_patient_update_can_set_optional_fields_to_none():
    patient = PatientUpdate(
        gender=None,
        phone=None,
        address=None
    )

    update_data = patient.model_dump(exclude_unset=True)

    assert update_data == {
        "gender": None,
        "phone": None,
        "address": None,
    }


# -----------------------------
# PATIENT RESPONSE TESTS
# -----------------------------

def test_patient_response_valid_data():
    patient = PatientResponse(
        id=1,
        user_id=10,
        first_name="Viha",
        last_name="Rathod",
        date_of_birth=date(2003, 5, 15),
        gender="Female",
        phone="9876543210",
        address="Ahmedabad, Gujarat"
    )

    assert patient.id == 1
    assert patient.user_id == 10
    assert patient.first_name == "Viha"


def test_patient_response_missing_required_field():
    data = {
        "user_id": 10,
        "first_name": "Viha",
        "last_name": "Rathod",
        "date_of_birth": date(2003, 5, 15),
        "gender": "Female",
        "phone": "9876543210",
        "address": "Ahmedabad, Gujarat"
    }

    with pytest.raises(ValidationError):
        PatientResponse(**data)
