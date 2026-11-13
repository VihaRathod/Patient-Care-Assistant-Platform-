from pydantic import BaseModel, ConfigDict, Field


class PrescriptionItemCreate(BaseModel):

    medication_name: str = Field(
        min_length=2,
        max_length=255
    )

    dosage: str = Field(
        min_length=1,
        max_length=100
    )

    frequency: str = Field(
        min_length=1,
        max_length=100
    )

    duration_days: int = Field(
        gt=0
    )

    quantity: int = Field(
        gt=0
    )

    instructions: str | None = None


class PrescriptionItemResponse(BaseModel):

    id: int
    prescription_id: int
    medication_name: str
    dosage: str
    frequency: str
    duration_days: int
    quantity: int
    instructions: str | None

    model_config = ConfigDict(from_attributes=True)