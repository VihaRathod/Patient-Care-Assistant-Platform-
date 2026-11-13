
from pydantic import BaseModel, ConfigDict, Field

from models.patient_allergy import AllergySeverity


class PatientAllergyCreate(BaseModel):
    allergy_id: int
    severity: AllergySeverity
    reaction: str | None = Field(
        default=None,
        max_length=500
    )


class PatientAllergyUpdate(BaseModel):
    severity: AllergySeverity | None = None
    reaction: str | None = Field(
        default=None,
        max_length=500
    )


class PatientAllergyResponse(BaseModel):
    id: int
    patient_id: int
    allergy_id: int
    severity: AllergySeverity
    reaction: str | None

    model_config = ConfigDict(from_attributes=True)
