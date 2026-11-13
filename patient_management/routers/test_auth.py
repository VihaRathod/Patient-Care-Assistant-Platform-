
from fastapi import APIRouter, Depends

from models.user import User

from dependencies.auth import get_current_user


router = APIRouter(
    prefix="/test",
    tags=["Authentication Testing"]
)


@router.get("/protected")
def protected_route(
    current_user: User = Depends(get_current_user)
):

    return {
        "message": "Authentication successful",

        "user_id": current_user.id,

        "email": current_user.email,

        "role": (
            current_user.role.value
            if hasattr(current_user.role, "value")
            else str(current_user.role)
        )
    }
