import pytest

from datetime import datetime
from pydantic import ValidationError

from schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
)

from models.appointment import (
    AppointmentType,
    AppointmentStatus,
)


# --------------------------------------------------
# Helper function
# --------------------------------------------------

def valid_appointment_data():

    return {
        "provider_id": 1,
        "appointment_type": AppointmentType.IN_PERSON,
        "start_datetime": datetime.fromisoformat(
            "2026-11-16T10:00:00+05:30"
        ),
        "end_datetime": datetime.fromisoformat(
            "2026-11-16T10:30:00+05:30"
        ),
        "reason": "Regular checkup",
        "room": "Room 101",
    }


# --------------------------------------------------
# Appointment Create Tests
# --------------------------------------------------

def test_create_appointment_with_valid_data():

    data = valid_appointment_data()

    appointment = AppointmentCreate(**data)

    assert appointment.provider_id == 1
    assert appointment.appointment_type == AppointmentType.IN_PERSON
    assert appointment.reason == "Regular checkup"


def test_create_appointment_requires_provider_id():

    data = valid_appointment_data()

    del data["provider_id"]

    with pytest.raises(ValidationError):
        AppointmentCreate(**data)


def test_create_appointment_requires_appointment_type():

    data = valid_appointment_data()

    del data["appointment_type"]

    with pytest.raises(ValidationError):
        AppointmentCreate(**data)


def test_create_appointment_rejects_naive_datetime():

    data = valid_appointment_data()

    data["start_datetime"] = datetime(
        2026, 11, 16, 10, 0
    )

    with pytest.raises(ValidationError):
        AppointmentCreate(**data)


def test_create_appointment_rejects_end_before_start():

    data = valid_appointment_data()

    data["start_datetime"] = datetime.fromisoformat(
        "2026-11-16T11:00:00+05:30"
    )

    data["end_datetime"] = datetime.fromisoformat(
        "2026-11-16T10:00:00+05:30"
    )

    with pytest.raises(ValidationError):
        AppointmentCreate(**data)


def test_create_appointment_rejects_equal_start_and_end():

    data = valid_appointment_data()

    data["end_datetime"] = data["start_datetime"]

    with pytest.raises(ValidationError):
        AppointmentCreate(**data)


def test_create_appointment_rejects_room_longer_than_100_characters():

    data = valid_appointment_data()

    data["room"] = "R" * 101

    with pytest.raises(ValidationError):
        AppointmentCreate(**data)


def test_create_appointment_allows_optional_fields_to_be_empty():

    data = valid_appointment_data()

    data["reason"] = None
    data["room"] = None

    appointment = AppointmentCreate(**data)

    assert appointment.reason is None
    assert appointment.room is None


# --------------------------------------------------
# Appointment Update Tests
# --------------------------------------------------

def test_update_appointment_with_valid_data():

    data = {
        "reason": "Follow-up consultation",
        "room": "Room 202",
    }

    appointment = AppointmentUpdate(**data)

    assert appointment.reason == "Follow-up consultation"
    assert appointment.room == "Room 202"


def test_update_appointment_allows_partial_updates():

    data = {
        "reason": "Updated reason"
    }

    appointment = AppointmentUpdate(**data)

    assert appointment.reason == "Updated reason"
    assert appointment.room is None


def test_update_appointment_rejects_naive_start_datetime():

    data = {
        "start_datetime": datetime(
            2026, 11, 16, 10, 0
        )
    }

    with pytest.raises(ValidationError):
        AppointmentUpdate(**data)


def test_update_appointment_rejects_naive_end_datetime():

    data = {
        "end_datetime": datetime(
            2026, 11, 16, 10, 30
        )
    }

    with pytest.raises(ValidationError):
        AppointmentUpdate(**data)


def test_update_appointment_rejects_invalid_time_range():

    data = {
        "start_datetime": datetime.fromisoformat(
            "2026-11-16T11:00:00+05:30"
        ),
        "end_datetime": datetime.fromisoformat(
            "2026-11-16T10:00:00+05:30"
        ),
    }

    with pytest.raises(ValidationError):
        AppointmentUpdate(**data)


def test_update_appointment_accepts_valid_datetime_range():

    data = {
        "start_datetime": datetime.fromisoformat(
            "2026-11-16T11:00:00+05:30"
        ),
        "end_datetime": datetime.fromisoformat(
            "2026-11-16T11:30:00+05:30"
        ),
    }

    appointment = AppointmentUpdate(**data)

    assert appointment.start_datetime < appointment.end_datetime


def test_update_appointment_rejects_long_room_name():

    data = {
        "room": "R" * 101
    }

    with pytest.raises(ValidationError):
        AppointmentUpdate(**data)


# --------------------------------------------------
# Appointment Response Tests
# --------------------------------------------------

def test_appointment_response_with_valid_data():

    data = {
        "id": 1,
        "patient_id": 10,
        "provider_id": 20,
        "appointment_type": AppointmentType.IN_PERSON,
        "status": AppointmentStatus.SCHEDULED,
        "start_datetime": datetime.fromisoformat(
            "2026-11-16T10:00:00+05:30"
        ),
        "end_datetime": datetime.fromisoformat(
            "2026-11-16T10:30:00+05:30"
        ),
        "reason": "Regular checkup",
        "room": "Room 101",
    }

    response = AppointmentResponse(**data)

    assert response.id == 1
    assert response.patient_id == 10
    assert response.provider_id == 20
    assert response.status == AppointmentStatus.SCHEDULED


def test_appointment_response_requires_id():

    data = {
        "patient_id": 10,
        "provider_id": 20,
        "appointment_type": AppointmentType.IN_PERSON,
        "status": AppointmentStatus.SCHEDULED,
        "start_datetime": datetime.fromisoformat(
            "2026-11-16T10:00:00+05:30"
        ),
        "end_datetime": datetime.fromisoformat(
            "2026-11-16T10:30:00+05:30"
        ),
        "reason": None,
        "room": None,
    }

    with pytest.raises(ValidationError):
        AppointmentResponse(**data)