
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models.prescription import PrescriptionStatus
from schemas.prescription_item import (
    PrescriptionItemCreate,
    PrescriptionItemResponse,
)

class PrescriptionCreate(BaseModel):

    patient_id: int
    appointment_id: int | None = None

    notes: str | None = Field(
        default=None,
        max_length=500
    )

    items: list[PrescriptionItemCreate] = Field(
        min_length=1,
        max_length=50
    )


class PrescriptionUpdate(BaseModel):

    status: PrescriptionStatus | None = None

    notes: str | None = Field(
        default=None,
        max_length=500
    )


class PrescriptionResponse(BaseModel):

    id: int
    patient_id: int
    provider_id: int
    appointment_id: int | None

    issued_at: datetime
    status: PrescriptionStatus
    notes: str | None

    items: list[PrescriptionItemResponse]

    model_config = ConfigDict(from_attributes=True)
