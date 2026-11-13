import pytest
from pydantic import ValidationError

from schemas.prescription import (
    PrescriptionCreate,
    PrescriptionUpdate,
)


def valid_prescription_data():
    return {
        "patient_id": 1,
        "appointment_id": 1,
        "notes": "Take medication after meals",
        "items": [
            {
                # Replace these fields with the exact fields
                # required by your PrescriptionItemCreate schema.
            }
        ],
    }


def test_prescription_requires_at_least_one_item():
    data = {
        "patient_id": 1,
        "appointment_id": 1,
        "items": [],
    }

    with pytest.raises(ValidationError):
        PrescriptionCreate(**data)


def test_prescription_rejects_more_than_50_items():
    data = {
        "patient_id": 1,
        "appointment_id": 1,
        "items": [{}] * 51,
    }

    with pytest.raises(ValidationError):
        PrescriptionCreate(**data)


def test_prescription_rejects_long_notes():
    data = {
        "patient_id": 1,
        "appointment_id": 1,
        "notes": "A" * 501,
        "items": [{}],
    }

    with pytest.raises(ValidationError):
        PrescriptionCreate(**data)


def test_prescription_update_accepts_valid_notes():
    data = {
        "notes": "Continue medication for five days"
    }

    result = PrescriptionUpdate(**data)

    assert result.notes == data["notes"]


def test_prescription_update_rejects_long_notes():
    data = {
        "notes": "A" * 501
    }

    with pytest.raises(ValidationError):
        PrescriptionUpdate(**data)