
import httpx

from config.settings import settings


def get_upcoming_appointments():

    if not settings.INTERNAL_SERVICE_TOKEN:
        raise ValueError(
            "INTERNAL_SERVICE_TOKEN is not configured"
        )

    url = (
        f"{settings.PATIENT_MANAGEMENT_API_URL}"
        "/internal/appointments/upcoming-reminders"
    )

    headers = {
        "X-Internal-Service-Token":
            settings.INTERNAL_SERVICE_TOKEN
    }

    try:

        response = httpx.get(
            url,
            headers=headers,
            timeout=20.0
        )

        response.raise_for_status()

        return response.json()

    except httpx.HTTPError as error:

        raise RuntimeError(
            f"Could not fetch appointments: {error}"
        ) from error
