from datetime import datetime
from pydantic import BaseModel, ConfigDict


class VisitSummaryDocumentData(BaseModel):
    appointment_id: int
    appointment_type: str
    appointment_status: str
    appointment_datetime: datetime
    appointment_reason: str | None = None

    patient_name: str
    patient_email: str

    provider_name: str
    provider_qualification: str

    symptoms: str | None = None
    diagnosis: str | None = None
    treatment_plan: str | None = None
    follow_up_instructions: str | None = None
    summary: str

    model_config = ConfigDict(from_attributes=True)


class PrescriptionItemDocumentData(BaseModel):
    medication_name: str
    dosage: str
    frequency: str
    duration_days: int
    quantity: int
    instructions: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PrescriptionDocumentData(BaseModel):
    prescription_id: int
    issued_at: datetime
    status: str
    notes: str | None = None

    patient_name: str
    patient_email: str

    provider_name: str
    provider_qualification: str

    items: list[PrescriptionItemDocumentData]

    model_config = ConfigDict(from_attributes=True)