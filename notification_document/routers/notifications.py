
from fastapi import APIRouter

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


@router.get("/health")
def notification_health():

    return {
        "status": "healthy",
        "service": "Notification & Document Service"
    }
