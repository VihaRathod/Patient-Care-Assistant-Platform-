
from pydantic import BaseModel, ConfigDict, Field


class SpecialtyCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100
    )

    description: str | None = Field(
        default=None,
        max_length=500
    )


class SpecialtyUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    description: str | None = Field(
        default=None,
        max_length=500
    )


class SpecialtyResponse(BaseModel):
    id: int
    name: str
    description: str | None

    model_config = ConfigDict(from_attributes=True)
