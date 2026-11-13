
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator



class ProviderTimeOffCreate(BaseModel):

    start_datetime: datetime
    end_datetime: datetime

    reason: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_time_range(self):

        # First check timezone awareness
        if (self.start_datetime.tzinfo is None) != (
            self.end_datetime.tzinfo is None
        ):
            raise ValueError(
                "Both datetimes must have the same timezone awareness"
            )

        # Then compare datetimes
        if self.start_datetime >= self.end_datetime:
            raise ValueError(
                "End datetime must be after start datetime"
            )

        return self


class ProviderTimeOffUpdate(BaseModel):

    start_datetime: datetime | None = None
    end_datetime: datetime | None = None

    reason: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_time_range(self):

        # Check only when both values are supplied
        if (
            self.start_datetime is not None
            and self.end_datetime is not None
        ):

            # First check timezone awareness
            if (self.start_datetime.tzinfo is None) != (
                self.end_datetime.tzinfo is None
            ):
                raise ValueError(
                    "Both datetimes must have the same timezone awareness"
                )

            # Then compare datetimes
            if self.start_datetime >= self.end_datetime:
                raise ValueError(
                    "End datetime must be after start datetime"
                )

        return self


class ProviderTimeOffResponse(BaseModel):

    id: int
    provider_id: int

    start_datetime: datetime
    end_datetime: datetime

    reason: str | None

    model_config = ConfigDict(from_attributes=True)
