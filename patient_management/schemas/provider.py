
from pydantic import BaseModel, ConfigDict, Field


class ProviderUpdate(BaseModel):

    first_name: str | None = Field(default=None, min_length=2, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)

    qualification: str | None = Field(default=None, min_length=2, max_length=150)

    experience: int | None = Field(default=None, ge=0)

    phone: str | None = Field(default=None, min_length=7, max_length=20)


class ProviderResponse(BaseModel):

    id: int
    user_id: int

    first_name: str
    last_name: str
    qualification: str
    experience: int

    phone: str | None

    model_config = ConfigDict(from_attributes=True)
