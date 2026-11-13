
from pydantic import BaseModel, ConfigDict


class ProviderSpecialtyCreate(BaseModel):
    specialty_id: int


class ProviderSpecialtyResponse(BaseModel):
    id: int
    provider_id: int
    specialty_id: int

    model_config = ConfigDict(from_attributes=True)
