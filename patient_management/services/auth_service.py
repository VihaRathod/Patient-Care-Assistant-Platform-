
from sqlalchemy.orm import Session

from models.user import User

from utils.password import verify_password
from utils.jwt import create_access_token


def authenticate_user(
    db: Session,
    email: str,
    password: str
):

    # 1. Find user by email

    user = (
        db.query(User)
        .filter(
            User.email == email
        )
        .first()
    )

    if not user:
        return None

    # 2. Verify password

    if not verify_password(
        password,
        user.password_hash
    ):
        return None

    # 3. Check whether account is active

    if not user.is_active:
        return None

    return user


def login_user(
    db: Session,
    email: str,
    password: str
):

    # Authenticate user

    user = authenticate_user(
        db,
        email,
        password
    )

    if not user:
        return None

    # Convert enum role into string

    role = (
        user.role.value
        if hasattr(user.role, "value")
        else str(user.role)
    )

    # Generate JWT

    token = create_access_token(
        user_id=user.id,
        role=role
    )

    return token
