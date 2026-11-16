
# routers/documents.py

from fastapi import APIRouter, HTTPException
from pathlib import Path
from services.email_service import send_visit_summary_email
import smtplib
import httpx
from services.pdf_service import (
    fetch_visit_summary_data,
    generate_visit_summary_pdf
)
from services.pdf_service import (
    fetch_prescription_data,
    generate_prescription_pdf
)
from services.s3_service import DocumentStorageError, upload_document

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.get("/visit-summaries/{appointment_id}/download")
async def download_visit_summary(appointment_id: int):

    try:
        # Step 1: Fetch visit summary data from Patient Management
        visit_data = await fetch_visit_summary_data(appointment_id)

        # Step 2: Generate PDF
        pdf_path = generate_visit_summary_pdf(visit_data)

        # Step 3: Store the generated PDF privately in S3 and return a
        # time-limited URL instead of returning patient data in this response.
        if not Path(pdf_path).is_file():
            raise HTTPException(
                status_code=500,
                detail="Visit summary PDF could not be generated"
            )

        document = upload_document(pdf_path, "visit-summaries", appointment_id)

        return {
            "appointment_id": appointment_id,
            "document_url": document.url,
            "expires_in_seconds": document.expires_in_seconds,
        }

    except HTTPException:
        raise

    except httpx.HTTPStatusError as e:

        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Visit summary not found"
            )

        raise HTTPException(
            status_code=502,
            detail="Patient Management service returned an error"
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to Patient Management service"
        )

    except DocumentStorageError:
        raise HTTPException(
            status_code=502,
            detail="Failed to store visit summary in document storage"
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate visit summary PDF"
        )

@router.get("/prescriptions/{prescription_id}/download")
async def download_prescription(prescription_id: int):

    try:
        # Fetch prescription data
        prescription_data = await fetch_prescription_data(
            prescription_id
        )

        # Generate PDF
        pdf_path = generate_prescription_pdf(
            prescription_data
        )

        if not Path(pdf_path).is_file():
            raise HTTPException(
                status_code=500,
                detail="Prescription PDF could not be generated"
            )

        document = upload_document(pdf_path, "prescriptions", prescription_id)

        return {
            "prescription_id": prescription_id,
            "document_url": document.url,
            "expires_in_seconds": document.expires_in_seconds,
        }

    except HTTPException:
        raise

    except httpx.HTTPStatusError as e:

        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Prescription not found"
            )

        raise HTTPException(
            status_code=502,
            detail="Patient Management service returned an error"
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to Patient Management service"
        )

    except DocumentStorageError:
        raise HTTPException(
            status_code=502,
            detail="Failed to store prescription in document storage"
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate prescription PDF"
        )


@router.post("/visit-summaries/{appointment_id}/email")
async def email_visit_summary(appointment_id: int):

    try:
        # Step 1: Fetch visit summary data
        visit_data = await fetch_visit_summary_data(
            appointment_id
        )

        recipient_email = visit_data.get("patient_email")

        if not recipient_email:
            raise HTTPException(
                status_code=422,
                detail="Patient email address is not available"
            )

        # Step 2: Generate PDF
        pdf_path = generate_visit_summary_pdf(visit_data)

        # Step 3: Store the PDF and share its short-lived link by email.
        document = upload_document(pdf_path, "visit-summaries", appointment_id)
        send_visit_summary_email(
            recipient_email=recipient_email,
            patient_name=visit_data.get("patient_name", "Patient"),
            provider_name=visit_data.get("provider_name", "Provider"),
            appointment_datetime=visit_data.get(
                "appointment_datetime", ""
            ),
            document_url=document.url,
            link_expiry_seconds=document.expires_in_seconds,
        )

        return {
            "message": "Visit summary emailed successfully",
            "appointment_id": appointment_id,
            "recipient_email": recipient_email,
            "document_url": document.url,
            "expires_in_seconds": document.expires_in_seconds,
        }

    except HTTPException:
        raise

    except httpx.HTTPStatusError as e:

        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Visit summary not found"
            )

        raise HTTPException(
            status_code=502,
            detail="Patient Management service returned an error"
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to Patient Management service"
        )

    except DocumentStorageError:
        raise HTTPException(
            status_code=502,
            detail="Failed to store visit summary in document storage"
        )

    except (smtplib.SMTPException, OSError):
        raise HTTPException(
            status_code=502,
            detail="Failed to send visit summary email"
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to process visit summary email"
        )
