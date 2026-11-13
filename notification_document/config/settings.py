
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:

    # Own notification database
    DATABASE_URL = os.getenv("NOTIFICATION_DATABASE_URL")

    # Patient Management API
    PATIENT_MANAGEMENT_API_URL = os.getenv(
        "PATIENT_MANAGEMENT_API_URL",
        "http://localhost:8000"
    )

    # Communication security
    INTERNAL_SERVICE_TOKEN = os.getenv(
        "INTERNAL_SERVICE_TOKEN"
    )

    # Email configuration
    SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))

    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

    SMTP_USE_TLS = os.getenv(
        "SMTP_USE_TLS", "false"
    ).lower() == "true"

    EMAIL_FROM = os.getenv(
        "EMAIL_FROM",
        "notifications@patientcare.com"
    )

    # Reminder configuration
    REMINDER_HOURS_BEFORE = int(
        os.getenv("REMINDER_HOURS_BEFORE", "24")
    )

    SCHEDULER_INTERVAL_MINUTES = int(
        os.getenv("SCHEDULER_INTERVAL_MINUTES", "15")
    )


settings = Settings()
