
from pydantic import BaseModel, EmailStr

from schemas.user import UserCreate
from schemas.patient import PatientCreate


# Patient registration combines User + Patient details
class PatientRegisterRequest(UserCreate, PatientCreate):
    pass


# Login request
class LoginRequest(BaseModel):

    email: EmailStr

    password: str


# JWT response
class TokenResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"
