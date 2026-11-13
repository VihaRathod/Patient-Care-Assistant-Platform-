
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from database.connection import SessionLocal

from models.user import User

from utils.jwt import decode_access_token


class AuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self,
        request,
        call_next
    ):

        # ---------------------------------
        # PUBLIC ROUTES
        # ---------------------------------

        public_paths = {
            "/auth/register",
            "/auth/login",
            "/auth/token",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/"
        }

        # Allow public routes and CORS preflight

        if (
            request.url.path.startswith("/internal/")
            or request.url.path in public_paths
            or request.method == "OPTIONS"
        ):
            return await call_next(request)

        # ---------------------------------
        # 1. Get Authorization header
        # ---------------------------------

        authorization = request.headers.get(
            "Authorization"
        )

        if not authorization:

            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Authorization header missing"
                }
            )

        # Expected:
        # Authorization: Bearer <token>

        parts = authorization.split()

        if (
            len(parts) != 2
            or parts[0].lower() != "bearer"
        ):

            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Invalid authorization header"
                }
            )

        token = parts[1]

        # ---------------------------------
        # 2. Decode JWT
        # ---------------------------------

        try:

            payload = decode_access_token(
                token
            )

        except ValueError:

            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Invalid or expired token"
                }
            )

        # ---------------------------------
        # 3. Extract user ID
        # ---------------------------------

        user_id = payload.get("sub")

        if not user_id:

            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Invalid token"
                }
            )

        try:

            user_id = int(user_id)

        except (TypeError, ValueError):

            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Invalid token"
                }
            )

        # ---------------------------------
        # 4. Fetch user from database
        # ---------------------------------

        db = SessionLocal()

        try:

            user = (
                db.query(User)
                .filter(
                    User.id == user_id
                )
                .first()
            )

            if not user:

                return JSONResponse(
                    status_code=401,
                    content={
                        "detail": "User not found"
                    }
                )

            if not user.is_active:

                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "User is inactive"
                    }
                )

            # ---------------------------------
            # 5. Store authenticated user
            # ---------------------------------

            request.state.current_user = user

            return await call_next(request)

        finally:

            db.close()
