
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session

from database.connection import get_db

from schemas.auth import (
    LoginRequest,
    TokenResponse,
    PatientRegisterRequest
)

from schemas.user import UserResponse

from services.auth_service import login_user

from services.user_service import create_patient_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# -----------------------------------------
# REGISTER
# -----------------------------------------

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    user_data: PatientRegisterRequest,
    db: Session = Depends(get_db)
):

    user, error = create_patient_user(
        db,
        user_data
    )

    if error:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return user


# -----------------------------------------
# LOGIN
# -----------------------------------------

@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):

    token = login_user(
        db,
        data.email,
        data.password
    )

    if not token:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# -----------------------------------------
# OAUTH2 TOKEN
# -----------------------------------------

@router.post(
    "/token",
    response_model=TokenResponse
)
def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    access_token = login_user(
        db,
        form_data.username,
        form_data.password
    )

    if not access_token:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
