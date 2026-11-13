
# routers/documents.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from services.email_service import send_visit_summary_email
import smtplib
import httpx
import traceback
from services.pdf_service import (
    fetch_visit_summary_data,
    generate_visit_summary_pdf
)
from services.pdf_service import (
    fetch_prescription_data,
    generate_prescription_pdf
)

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

        # Step 3: Verify that PDF exists
        if not Path(pdf_path).is_file():
            raise HTTPException(
                status_code=500,
                detail="Visit summary PDF could not be generated"
            )

        # Step 4: Return PDF as downloadable response
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"visit_summary_{appointment_id}.pdf"
        )

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

        # Download PDF
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"prescription_{prescription_id}.pdf"
        )

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

    except Exception as e:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate prescription PDF: {str(e)}"
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

        # Step 3: Send email with PDF attachment
        send_visit_summary_email(
            recipient_email=recipient_email,
            patient_name=visit_data.get("patient_name", "Patient"),
            provider_name=visit_data.get("provider_name", "Provider"),
            appointment_datetime=visit_data.get(
                "appointment_datetime", ""
            ),
            pdf_path=pdf_path
        )

        return {
            "message": "Visit summary emailed successfully",
            "appointment_id": appointment_id,
            "recipient_email": recipient_email,
            "attachment": Path(pdf_path).name
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
