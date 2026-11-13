
from fastapi import Depends, HTTPException, status

from models.user import User, UserRole

from dependencies.auth import get_current_user


# -----------------------------------------
# ROLE CHECKER
# -----------------------------------------

def require_roles(*allowed_roles: UserRole):

    def role_checker(
        current_user: User = Depends(get_current_user)
    ):

        # Get current user's role

        user_role = current_user.role

        # Compare against allowed roles

        if user_role not in allowed_roles:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )

        return current_user

    return role_checker


# -----------------------------------------
# REUSABLE ROLE PERMISSIONS
# -----------------------------------------
require_patient = require_roles("PATIENT")
require_provider = require_roles("PROVIDER")
require_admin = require_roles("ADMIN")


# -----------------------------------------
# MULTI-ROLE PERMISSIONS
# -----------------------------------------
require_patient_or_provider = require_roles(
    "PATIENT",
    "PROVIDER"
)

require_provider_or_admin = require_roles(
    "PROVIDER",
    "ADMIN"
)
require_all_authenticated = require_roles(
    "PATIENT",
    "PROVIDER",
    "ADMIN"
)
