
from fastapi import (
    Request,
    Depends,
    HTTPException,
    status
)

from fastapi.security import OAuth2PasswordBearer

from models.user import User


# -----------------------------------------
# OAUTH2 SECURITY SCHEME
# -----------------------------------------

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token"
)


# -----------------------------------------
# GET CURRENT USER
# -----------------------------------------

def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> User:

    # JWT has already been validated
    # by AuthMiddleware

    user = getattr(
        request.state,
        "current_user",
        None
    )

    if not user:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    return user


def require_roles(*allowed_roles):

    def role_checker(
        current_user: User = Depends(get_current_user)
    ):

        user_role = (
            current_user.role.value
            if hasattr(current_user.role, "value")
            else str(current_user.role)
        )

        if user_role not in allowed_roles:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )

        return current_user

    return role_checker
