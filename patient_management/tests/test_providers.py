
from datetime import date, datetime, time, timedelta, timezone

import pytest
from pydantic import ValidationError

from schemas.provider import (
    ProviderCreate,
    ProviderUpdate,
    ProviderResponse,
)

from schemas.provider_availability import (
    ProviderAvailabilityCreate,
    ProviderAvailabilityUpdate,
    ProviderAvailabilityResponse,
    AvailableSlotResponse,
)

from schemas.provider_time_off import (
    ProviderTimeOffCreate,
    ProviderTimeOffUpdate,
    ProviderTimeOffResponse,
)

from schemas.provider_speciality import (
    ProviderSpecialtyCreate,
    ProviderSpecialtyResponse,
)


# =====================================================
# PROVIDER SCHEMA TESTS
# =====================================================

def valid_provider_data():
    return {
        "user_id": 1,
        "first_name": "Aarav",
        "last_name": "Shah",
        "qualification": "MBBS",
        "experience": 5,
        "phone": "9876543210",
    }


def test_provider_create_valid_data():
    provider = ProviderCreate(**valid_provider_data())

    assert provider.user_id == 1
    assert provider.first_name == "Aarav"
    assert provider.qualification == "MBBS"
    assert provider.experience == 5


def test_provider_create_missing_user_id():
    data = valid_provider_data()
    data.pop("user_id")

    with pytest.raises(ValidationError):
        ProviderCreate(**data)


def test_provider_create_missing_first_name():
    data = valid_provider_data()
    data.pop("first_name")

    with pytest.raises(ValidationError):
        ProviderCreate(**data)


def test_provider_create_missing_qualification():
    data = valid_provider_data()
    data.pop("qualification")

    with pytest.raises(ValidationError):
        ProviderCreate(**data)


def test_provider_create_first_name_too_short():
    data = valid_provider_data()
    data["first_name"] = "A"

    with pytest.raises(ValidationError):
        ProviderCreate(**data)


def test_provider_create_first_name_too_long():
    data = valid_provider_data()
    data["first_name"] = "A" * 101

    with pytest.raises(ValidationError):
        ProviderCreate(**data)


def test_provider_create_negative_experience():
    data = valid_provider_data()
    data["experience"] = -1

    with pytest.raises(ValidationError):
        ProviderCreate(**data)


def test_provider_create_invalid_phone():
    data = valid_provider_data()
    data["phone"] = "123"

    with pytest.raises(ValidationError):
        ProviderCreate(**data)


def test_provider_create_optional_phone():
    data = valid_provider_data()
    data["phone"] = None

    provider = ProviderCreate(**data)

    assert provider.phone is None


def test_provider_create_default_experience():
    data = valid_provider_data()
    data.pop("experience")

    provider = ProviderCreate(**data)

    assert provider.experience == 0


# ---------------- PROVIDER UPDATE ----------------

def test_provider_update_valid_data():
    provider = ProviderUpdate(
        first_name="Viha",
        experience=6
    )

    assert provider.first_name == "Viha"
    assert provider.experience == 6


def test_provider_update_partial_data():
    provider = ProviderUpdate(first_name="Viha")

    update_data = provider.model_dump(exclude_unset=True)

    assert update_data == {"first_name": "Viha"}


def test_provider_update_empty_data():
    provider = ProviderUpdate()

    assert provider.model_dump(exclude_unset=True) == {}


def test_provider_update_negative_experience():
    with pytest.raises(ValidationError):
        ProviderUpdate(experience=-2)


def test_provider_update_invalid_phone():
    with pytest.raises(ValidationError):
        ProviderUpdate(phone="123")


def test_provider_update_optional_phone_none():
    provider = ProviderUpdate(phone=None)

    assert provider.phone is None


# ---------------- PROVIDER RESPONSE ----------------

def test_provider_response_valid_data():
    provider = ProviderResponse(
        id=1,
        user_id=10,
        first_name="Aarav",
        last_name="Shah",
        qualification="MBBS",
        experience=5,
        phone="9876543210"
    )

    assert provider.id == 1
    assert provider.user_id == 10
    assert provider.first_name == "Aarav"


def test_provider_response_missing_required_field():
    with pytest.raises(ValidationError):
        ProviderResponse(
            id=1,
            user_id=10,
            first_name="Aarav",
            last_name="Shah",
            qualification="MBBS",
            experience=5
        )


# =====================================================
# PROVIDER AVAILABILITY SCHEMA TESTS
# =====================================================

def test_availability_create_valid_data():
    availability = ProviderAvailabilityCreate(
        day_of_week=1,
        start_time=time(9, 0),
        end_time=time(17, 0)
    )

    assert availability.day_of_week == 1
    assert availability.start_time == time(9, 0)
    assert availability.end_time == time(17, 0)
    assert availability.is_active is True


def test_availability_create_invalid_day():
    with pytest.raises(ValidationError):
        ProviderAvailabilityCreate(
            day_of_week=7,
            start_time=time(9, 0),
            end_time=time(17, 0)
        )


def test_availability_create_negative_day():
    with pytest.raises(ValidationError):
        ProviderAvailabilityCreate(
            day_of_week=-1,
            start_time=time(9, 0),
            end_time=time(17, 0)
        )


def test_availability_create_end_before_start():
    with pytest.raises(ValidationError):
        ProviderAvailabilityCreate(
            day_of_week=1,
            start_time=time(17, 0),
            end_time=time(9, 0)
        )


def test_availability_create_equal_times():
    with pytest.raises(ValidationError):
        ProviderAvailabilityCreate(
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(9, 0)
        )


def test_availability_create_custom_active_status():
    availability = ProviderAvailabilityCreate(
        day_of_week=2,
        start_time=time(10, 0),
        end_time=time(16, 0),
        is_active=False
    )

    assert availability.is_active is False


# ---------------- AVAILABILITY UPDATE ----------------

def test_availability_update_valid_data():
    availability = ProviderAvailabilityUpdate(
        start_time=time(10, 0),
        end_time=time(18, 0)
    )

    assert availability.start_time == time(10, 0)
    assert availability.end_time == time(18, 0)


def test_availability_update_partial_data():
    availability = ProviderAvailabilityUpdate(
        is_active=False
    )

    assert availability.model_dump(exclude_unset=True) == {
        "is_active": False
    }


def test_availability_update_invalid_day():
    with pytest.raises(ValidationError):
        ProviderAvailabilityUpdate(day_of_week=8)


def test_availability_update_invalid_time_range():
    with pytest.raises(ValidationError):
        ProviderAvailabilityUpdate(
            start_time=time(18, 0),
            end_time=time(9, 0)
        )


# ---------------- AVAILABILITY RESPONSE ----------------

def test_availability_response_valid_data():
    availability = ProviderAvailabilityResponse(
        id=1,
        provider_id=10,
        day_of_week=1,
        start_time=time(9, 0),
        end_time=time(17, 0),
        is_active=True
    )

    assert availability.id == 1
    assert availability.provider_id == 10


def test_availability_response_missing_required_field():
    with pytest.raises(ValidationError):
        ProviderAvailabilityResponse(
            id=1,
            provider_id=10,
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(17, 0)
        )


# =====================================================
# PROVIDER TIME OFF SCHEMA TESTS
# =====================================================

def valid_time_off_data():
    return {
        "start_datetime": datetime(
            2026, 11, 16, 9, 0,
            tzinfo=timezone.utc
        ),
        "end_datetime": datetime(
            2026, 11, 16, 17, 0,
            tzinfo=timezone.utc
        ),
        "reason": "Personal leave"
    }


def test_time_off_create_valid_data():
    time_off = ProviderTimeOffCreate(**valid_time_off_data())

    assert time_off.reason == "Personal leave"
    assert time_off.start_datetime < time_off.end_datetime


def test_time_off_create_end_before_start():
    data = valid_time_off_data()
    data["start_datetime"] = datetime(
        2026, 11, 16, 17, 0,
        tzinfo=timezone.utc
    )

    with pytest.raises(ValidationError):
        ProviderTimeOffCreate(**data)


def test_time_off_create_equal_datetimes():
    data = valid_time_off_data()
    data["end_datetime"] = data["start_datetime"]

    with pytest.raises(ValidationError):
        ProviderTimeOffCreate(**data)


def test_time_off_create_mixed_timezone_awareness():
    data = valid_time_off_data()
    data["end_datetime"] = datetime(2026, 11, 16, 17, 0)

    with pytest.raises(ValidationError):
        ProviderTimeOffCreate(**data)


def test_time_off_create_both_naive_datetimes():
    data = {
        "start_datetime": datetime(2026, 11, 16, 9, 0),
        "end_datetime": datetime(2026, 11, 16, 17, 0),
        "reason": "Personal leave"
    }

    # Your current schema permits both datetimes to be naive.
    time_off = ProviderTimeOffCreate(**data)

    assert time_off.start_datetime.tzinfo is None
    assert time_off.end_datetime.tzinfo is None


def test_time_off_create_reason_too_long():
    data = valid_time_off_data()
    data["reason"] = "A" * 256

    with pytest.raises(ValidationError):
        ProviderTimeOffCreate(**data)


# ---------------- TIME OFF UPDATE ----------------

def test_time_off_update_valid_data():
    time_off = ProviderTimeOffUpdate(
        reason="Medical leave"
    )

    assert time_off.reason == "Medical leave"


def test_time_off_update_partial_data():
    time_off = ProviderTimeOffUpdate(
        reason="Personal leave"
    )

    assert time_off.model_dump(exclude_unset=True) == {
        "reason": "Personal leave"
    }


def test_time_off_update_invalid_time_range():
    with pytest.raises(ValidationError):
        ProviderTimeOffUpdate(
            start_datetime=datetime(
                2026, 11, 16, 18, 0,
                tzinfo=timezone.utc
            ),
            end_datetime=datetime(
                2026, 11, 16, 9, 0,
                tzinfo=timezone.utc
            )
        )


def test_time_off_update_mixed_timezone_awareness():
    with pytest.raises(ValidationError):
        ProviderTimeOffUpdate(
            start_datetime=datetime(
                2026, 11, 16, 9, 0,
                tzinfo=timezone.utc
            ),
            end_datetime=datetime(2026, 11, 16, 17, 0)
        )


def test_time_off_update_reason_too_long():
    with pytest.raises(ValidationError):
        ProviderTimeOffUpdate(reason="A" * 256)


# ---------------- TIME OFF RESPONSE ----------------

def test_time_off_response_valid_data():
    time_off = ProviderTimeOffResponse(
        id=1,
        provider_id=10,
        start_datetime=datetime(
            2026, 11, 16, 9, 0,
            tzinfo=timezone.utc
        ),
        end_datetime=datetime(
            2026, 11, 16, 17, 0,
            tzinfo=timezone.utc
        ),
        reason="Personal leave"
    )

    assert time_off.id == 1
    assert time_off.provider_id == 10


def test_time_off_response_missing_required_field():
    with pytest.raises(ValidationError):
        ProviderTimeOffResponse(
            id=1,
            provider_id=10,
            start_datetime=datetime(
                2026, 11, 16, 9, 0,
                tzinfo=timezone.utc
            ),
            end_datetime=datetime(
                2026, 11, 16, 17, 0,
                tzinfo=timezone.utc
            )
        )


# =====================================================
# PROVIDER SPECIALTY SCHEMA TESTS
# =====================================================

def test_specialty_create_valid_data():
    specialty = ProviderSpecialtyCreate(specialty_id=5)

    assert specialty.specialty_id == 5


def test_specialty_create_missing_id():
    with pytest.raises(ValidationError):
        ProviderSpecialtyCreate()


def test_specialty_response_valid_data():
    specialty = ProviderSpecialtyResponse(
        id=1,
        provider_id=10,
        specialty_id=5
    )

    assert specialty.id == 1
    assert specialty.provider_id == 10
    assert specialty.specialty_id == 5


def test_specialty_response_missing_field():
    with pytest.raises(ValidationError):
        ProviderSpecialtyResponse(
            id=1,
            provider_id=10
        )


# =====================================================
# AVAILABLE SLOT RESPONSE TESTS
# =====================================================

def test_available_slot_response_valid_data():
    slot = AvailableSlotResponse(
        start_datetime=datetime(
            2026, 11, 16, 9, 0,
            tzinfo=timezone.utc
        ),
        end_datetime=datetime(
            2026, 11, 16, 9, 30,
            tzinfo=timezone.utc
        )
    )

    assert slot.start_datetime < slot.end_datetime


def test_available_slot_response_missing_field():
    with pytest.raises(ValidationError):
        AvailableSlotResponse(
            start_datetime=datetime(
                2026, 11, 16, 9, 0,
                tzinfo=timezone.utc
            )
        )
