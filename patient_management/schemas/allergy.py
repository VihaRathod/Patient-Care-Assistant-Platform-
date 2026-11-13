
from pydantic import BaseModel, ConfigDict, Field


class AllergyCreate(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=150
    )

    description: str | None = Field(
        default=None,
        max_length=500
    )


class AllergyUpdate(BaseModel):

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150
    )

    description: str | None = Field(
        default=None,
        max_length=500
    )


class AllergyResponse(BaseModel):

    id: int
    name: str
    description: str | None

    model_config = ConfigDict(from_attributes=True)


