
import smtplib

from email.message import EmailMessage
from config.settings import settings


def send_appointment_reminder(
    recipient_email: str,
    patient_name: str,
    provider_name: str,
    appointment_type: str,
    appointment_datetime: str
):

    message = EmailMessage()

    message["Subject"] = "Appointment Reminder - Patient Care"
    message["From"] = settings.EMAIL_FROM
    message["To"] = recipient_email

    body = f"""
Hello {patient_name},

This is a reminder about your upcoming appointment.

Appointment Details:

Provider: Dr. {provider_name}
Appointment Type: {appointment_type}
Date and Time: {appointment_datetime}

Please make sure to attend your scheduled appointment.

Thank you,
Patient Care Team
"""

    message.set_content(body)

    with smtplib.SMTP(
        settings.SMTP_HOST,
        settings.SMTP_PORT,
        timeout=20
    ) as server:

        server.ehlo()

        if settings.SMTP_USE_TLS:
            server.starttls()
            server.ehlo()

        if (
            settings.SMTP_USERNAME
            and settings.SMTP_PASSWORD
        ):
            server.login(
                settings.SMTP_USERNAME,
                settings.SMTP_PASSWORD
            )

        server.send_message(message)


def send_visit_summary_email(
    recipient_email: str,
    patient_name: str,
    provider_name: str,
    appointment_datetime: str,
    document_url: str,
    link_expiry_seconds: int,
):

    message = EmailMessage()

    message["Subject"] = "Your Visit Summary - Patient Care"
    message["From"] = settings.EMAIL_FROM
    message["To"] = recipient_email

    body = f"""
Hello {patient_name},

Thank you for visiting Patient Care.

Use the secure link below to download your visit summary PDF. The link expires
in {link_expiry_seconds // 60} minutes:

{document_url}

Appointment Details:

Provider: Dr. {provider_name}
Date and Time: {appointment_datetime}

Please keep this document for your records.

Thank you,
Patient Care Team
"""

    message.set_content(body)

    # Send email using existing SMTP configuration
    with smtplib.SMTP(
        settings.SMTP_HOST,
        settings.SMTP_PORT,
        timeout=20
    ) as server:

        server.ehlo()

        if settings.SMTP_USE_TLS:
            server.starttls()
            server.ehlo()

        if (
            settings.SMTP_USERNAME
            and settings.SMTP_PASSWORD
        ):
            server.login(
                settings.SMTP_USERNAME,
                settings.SMTP_PASSWORD
            )

        server.send_message(message)

