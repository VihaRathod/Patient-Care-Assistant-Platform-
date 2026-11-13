
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UpcomingAppointmentReminder(BaseModel):

    appointment_id: int
    patient_id: int

    patient_name: str
    patient_email: str

    provider_name: str

    appointment_type: str
    start_datetime: datetime
    end_datetime: datetime

    model_config = ConfigDict(from_attributes=True)
