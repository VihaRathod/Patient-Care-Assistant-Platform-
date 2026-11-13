from datetime import date, datetime

from pydantic import BaseModel, Field

from models.appointment import AppointmentType


class PatientQuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class RAGCitation(BaseModel):
    source_type: str
    source_id: int
    appointment_id: int | None = None
    appointment_date: datetime | None = None
    relevance_score: float


class PatientAnswerResponse(BaseModel):
    answer: str
    sources: list[RAGCitation]


class ReindexPatientResponse(BaseModel):
    patient_id: int
    indexed_chunks: int


class AppointmentPlanRequest(BaseModel):
    """A scheduling request.  This deliberately is not a diagnosis request."""

    symptom_description: str = Field(min_length=3, max_length=1_000)
    preferred_start_date: date | None = None
    search_days: int = Field(default=14, ge=1, le=30)
    duration_minutes: int = Field(default=30, ge=5, le=240)
    appointment_type: AppointmentType = AppointmentType.IN_PERSON
    preferred_provider_id: int | None = Field(default=None, gt=0)


class AppointmentPlanSlot(BaseModel):
    provider_id: int
    provider_name: str
    specialty_names: list[str]
    start_datetime: datetime
    end_datetime: datetime


class AppointmentPlanResponse(BaseModel):
    agent_run_id: int
    status: str
    recommendation: AppointmentPlanSlot | None = None
    alternatives: list[AppointmentPlanSlot] = Field(default_factory=list)
    matching_specialties: list[str] = Field(default_factory=list)
    confirmation_message: str | None = None
    disclaimer: str


class AppointmentPlanConfirmationResponse(BaseModel):
    agent_run_id: int
    appointment_id: int
    status: str
