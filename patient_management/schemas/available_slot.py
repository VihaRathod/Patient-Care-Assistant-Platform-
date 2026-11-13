
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AvailableSlotResponse(BaseModel):

    start_datetime: datetime
    end_datetime: datetime

    model_config = ConfigDict(from_attributes=True)
