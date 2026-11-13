
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):

    id: int
    patient_id: int
    appointment_id: int
    notification_type: str
    recipient_email: str
    status: str
    sent_at: datetime | None
    error_message: str | None

    model_config = ConfigDict(from_attributes=True)
