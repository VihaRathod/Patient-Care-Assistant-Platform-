
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from models.appointment import AppointmentType, AppointmentStatus


class AppointmentCreate(BaseModel):

    provider_id: int
    appointment_type: AppointmentType

    start_datetime: datetime
    end_datetime: datetime

    reason: str | None = None

    room: str | None = Field(
        default=None,
        max_length=100
    )

    @model_validator(mode="after")
    def validate_appointment(self):

        if (
            self.start_datetime.utcoffset() is None
            or self.end_datetime.utcoffset() is None
        ):
            raise ValueError(
                "Appointment datetimes must include timezone information"
            )

        if self.start_datetime >= self.end_datetime:
            raise ValueError(
                "End time must be after start time"
            )

        return self


class AppointmentUpdate(BaseModel):

    appointment_type: AppointmentType | None = None

    start_datetime: datetime | None = None
    end_datetime: datetime | None = None

    reason: str | None = None

    room: str | None = Field(
        default=None,
        max_length=100
    )

    @model_validator(mode="after")
    def validate_appointment(self):

        if (
            self.start_datetime is not None
            and self.start_datetime.utcoffset() is None
        ):
            raise ValueError(
                "Start datetime must include timezone information"
            )

        if (
            self.end_datetime is not None
            and self.end_datetime.utcoffset() is None
        ):
            raise ValueError(
                "End datetime must include timezone information"
            )

        if (
            self.start_datetime is not None
            and self.end_datetime is not None
            and self.start_datetime >= self.end_datetime
        ):
            raise ValueError(
                "End time must be after start time"
            )

        return self


class AppointmentResponse(BaseModel):

    id: int

    patient_id: int
    provider_id: int

    appointment_type: AppointmentType
    status: AppointmentStatus

    start_datetime: datetime
    end_datetime: datetime

    reason: str | None
    room: str | None

    model_config = ConfigDict(from_attributes=True)
