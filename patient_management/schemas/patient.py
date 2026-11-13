
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PatientCreate(BaseModel):

    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)

    date_of_birth: date

    gender: str | None = Field(default=None, max_length=20)
    phone: str | None = Field(default=None, min_length=7, max_length=20)
    address: str | None = Field(default=None, max_length=500)

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value):
        if value > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return value


class PatientUpdate(BaseModel):

    first_name: str | None = Field(default=None, min_length=2, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)

    date_of_birth: date | None = None

    gender: str | None = Field(default=None, max_length=20)
    phone: str | None = Field(default=None, min_length=7, max_length=20)
    address: str | None = Field(default=None, max_length=500)

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value):
        if value is not None and value > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return value


class PatientResponse(BaseModel):

    id: int
    user_id: int

    first_name: str
    last_name: str
    date_of_birth: date

    gender: str | None
    phone: str | None
    address: str | None

    model_config = ConfigDict(from_attributes=True)
