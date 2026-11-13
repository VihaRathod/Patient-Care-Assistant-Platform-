
from pydantic import BaseModel, ConfigDict, Field


class VisitNoteCreate(BaseModel):

    appointment_id: int

    symptoms: str | None = None
    diagnosis: str | None = None
    treatment_plan: str | None = None
    follow_up_instructions: str | None = None

    summary: str = Field(
        min_length=5
    )


class VisitNoteUpdate(BaseModel):

    symptoms: str | None = None
    diagnosis: str | None = None
    treatment_plan: str | None = None
    follow_up_instructions: str | None = None

    summary: str | None = Field(
        default=None,
        min_length=5
    )


class VisitNoteResponse(BaseModel):

    id: int
    appointment_id: int

    symptoms: str | None
    diagnosis: str | None
    treatment_plan: str | None
    follow_up_instructions: str | None

    summary: str

    model_config = ConfigDict(from_attributes=True)
