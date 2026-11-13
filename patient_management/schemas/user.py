
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict
)

from models.user import UserRole


# Public user registration
class UserCreate(BaseModel):

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128
    )


# Internal account creation
class UserInternalCreate(BaseModel):

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128
    )

    role: UserRole


# User response
class UserResponse(BaseModel):

    id: int
    email: EmailStr
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
