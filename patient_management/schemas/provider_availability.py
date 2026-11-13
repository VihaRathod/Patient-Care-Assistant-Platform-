
from datetime import time

from pydantic import BaseModel, ConfigDict, Field, model_validator


from datetime import datetime

from pydantic import BaseModel, ConfigDict

class ProviderAvailabilityCreate(BaseModel):

    day_of_week: int = Field(ge=0, le=6)

    start_time: time
    end_time: time

    is_active: bool = True

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.start_time >= self.end_time:
            raise ValueError("End time must be after start time")
        return self


class ProviderAvailabilityUpdate(BaseModel):

    day_of_week: int | None = Field(default=None, ge=0, le=6)

    start_time: time | None = None
    end_time: time | None = None

    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.start_time is not None and self.end_time is not None:
            if self.start_time >= self.end_time:
                raise ValueError("End time must be after start time")
        return self


class ProviderAvailabilityResponse(BaseModel):

    id: int
    provider_id: int

    day_of_week: int
    start_time: time
    end_time: time

    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AvailableSlotResponse(BaseModel):
    start_datetime: datetime
    end_datetime: datetime

    model_config = ConfigDict(from_attributes=True)
