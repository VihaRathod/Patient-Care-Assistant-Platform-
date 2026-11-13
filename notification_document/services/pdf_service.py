
# services/pdf_service.py

import os
from pathlib import Path
from datetime import datetime
from xml.sax.saxutils import escape

import httpx
from reportlab.platypus import KeepTogether
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)


# --------------------------------------------------
# Configuration
# --------------------------------------------------

PATIENT_MANAGEMENT_API_URL = os.getenv(
    "PATIENT_MANAGEMENT_API_URL",
    "http://localhost:8000"
)

INTERNAL_SERVICE_TOKEN = os.getenv("INTERNAL_SERVICE_TOKEN")

BASE_DIR = Path(__file__).resolve().parent.parent

VISIT_SUMMARY_DIR = BASE_DIR / "documents" / "visit_summaries"


# --------------------------------------------------
# 1. Fetch visit summary data
# --------------------------------------------------

async def fetch_visit_summary_data(appointment_id: int) -> dict:

    if not INTERNAL_SERVICE_TOKEN:
        raise RuntimeError("INTERNAL_SERVICE_TOKEN is not configured")

    url = (
        f"{PATIENT_MANAGEMENT_API_URL.rstrip('/')}"
        f"/internal/documents/appointments/"
        f"{appointment_id}/visit-summary-data"
    )

    headers = {
        "X-Internal-Service-Token": INTERNAL_SERVICE_TOKEN
    }

    async with httpx.AsyncClient(timeout=30.0) as client:

        response = await client.get(url, headers=headers)

        response.raise_for_status()

        return response.json()


# --------------------------------------------------
# 2. Helper functions
# --------------------------------------------------

def format_datetime(value: str) -> str:

    if not value:
        return "Not provided"

    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%d %B %Y, %I:%M %p")

    except (ValueError, TypeError):
        return str(value)


def safe_text(value) -> str:
    """Escape text before inserting it into a ReportLab Paragraph."""

    if value is None or value == "":
        return "Not provided"

    return escape(str(value))


# --------------------------------------------------
# 3. Generate visit summary PDF
# --------------------------------------------------

def generate_visit_summary_pdf(data: dict) -> str:

    VISIT_SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

    appointment_id = data["appointment_id"]

    file_path = (
        VISIT_SUMMARY_DIR /
        f"visit_summary_{appointment_id}.pdf"
    )

    # PDF document setup
    pdf = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocumentTitle",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#17365D"),
        alignment=TA_CENTER,
        spaceAfter=8
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#17365D"),
        spaceBefore=12,
        spaceAfter=7
    )

    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#333333")
    )

    label_style = ParagraphStyle(
        "LabelStyle",
        parent=body_style,
        fontName="Helvetica-Bold"
    )

    story = []

    # --------------------------------------------------
    # Header
    # --------------------------------------------------

    story.append(
        Paragraph("PATIENT VISIT SUMMARY", title_style)
    )

    story.append(
        Paragraph(
            f"Appointment ID: {safe_text(appointment_id)}",
            body_style
        )
    )

    story.append(Spacer(1, 8))

    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#17365D")
        )
    )

    # --------------------------------------------------
    # Patient details
    # --------------------------------------------------

    story.append(
        Paragraph("1. Patient Details", heading_style)
    )

    patient_data = [
        [
            Paragraph("Patient Name", label_style),
            Paragraph(safe_text(data.get("patient_name")), body_style)
        ],
        [
            Paragraph("Email", label_style),
            Paragraph(safe_text(data.get("patient_email")), body_style)
        ]
    ]

    patient_table = Table(
        patient_data,
        colWidths=[45 * mm, 115 * mm]
    )

    patient_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF0F8")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 8)
    ]))

    story.append(patient_table)

    # --------------------------------------------------
    # Provider details
    # --------------------------------------------------

    story.append(
        Paragraph("2. Provider Details", heading_style)
    )

    provider_data = [
        [
            Paragraph("Provider Name", label_style),
            Paragraph(safe_text(data.get("provider_name")), body_style)
        ],
        [
            Paragraph("Qualification", label_style),
            Paragraph(
                safe_text(data.get("provider_qualification")),
                body_style
            )
        ]
    ]

    provider_table = Table(
        provider_data,
        colWidths=[45 * mm, 115 * mm]
    )

    provider_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF0F8")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 8)
    ]))

    story.append(provider_table)

    # --------------------------------------------------
    # Appointment information
    # --------------------------------------------------

    story.append(
        Paragraph("3. Appointment Information", heading_style)
    )

    appointment_data = [
        ["Appointment Type", data.get("appointment_type")],
        ["Status", data.get("appointment_status")],
        [
            "Date and Time",
            format_datetime(data.get("appointment_datetime"))
        ],
        ["Reason", data.get("appointment_reason")]
    ]

    appointment_rows = [
        [
            Paragraph(safe_text(label), label_style),
            Paragraph(safe_text(value), body_style)
        ]
        for label, value in appointment_data
    ]

    appointment_table = Table(
        appointment_rows,
        colWidths=[45 * mm, 115 * mm]
    )

    appointment_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF0F8")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 8)
    ]))

    story.append(appointment_table)

    # --------------------------------------------------
    # Visit details
    # --------------------------------------------------

    story.append(
        Paragraph("4. Clinical Visit Details", heading_style)
    )

    clinical_sections = [
        ("Symptoms", "symptoms"),
        ("Diagnosis", "diagnosis"),
        ("Treatment Plan", "treatment_plan"),
        ("Follow-up Instructions", "follow_up_instructions"),
        ("Visit Summary", "summary")
    ]

    for heading, field in clinical_sections:

        story.append(
            Paragraph(heading, label_style)
        )

        story.append(
            Paragraph(
                safe_text(data.get(field)),
                body_style
            )
        )

        story.append(Spacer(1, 6))

    # --------------------------------------------------
    # Footer
    # --------------------------------------------------

    story.append(Spacer(1, 15))

    story.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.lightgrey
        )
    )

    story.append(Spacer(1, 6))

    story.append(
        Paragraph(
            "This document is a summary of the recorded clinical visit.",
            ParagraphStyle(
                "Footer",
                parent=body_style,
                alignment=TA_CENTER,
                fontSize=8,
                textColor=colors.grey
            )
        )
    )

    # Generate PDF
    pdf.build(story)

    return str(file_path)



async def fetch_prescription_data(prescription_id: int) -> dict:

    if not INTERNAL_SERVICE_TOKEN:
        raise RuntimeError("INTERNAL_SERVICE_TOKEN is not configured")

    url = (
        f"{PATIENT_MANAGEMENT_API_URL.rstrip('/')}"
        f"/internal/documents/prescriptions/"
        f"{prescription_id}/data"
    )

    headers = {
        "X-Internal-Service-Token": INTERNAL_SERVICE_TOKEN
    }

    async with httpx.AsyncClient(timeout=30.0) as client:

        response = await client.get(url, headers=headers)

        response.raise_for_status()

        return response.json()
# --------------------------------------------------
# 4. Generate prescription PDF
# --------------------------------------------------


def generate_prescription_pdf(data: dict) -> str:

    prescription_id = data["prescription_id"]

    items = data.get("items", [])

    if not items:
        raise ValueError("Prescription has no medication items")

    prescription_dir = BASE_DIR / "documents" / "prescriptions"
    prescription_dir.mkdir(parents=True, exist_ok=True)

    file_path = prescription_dir / f"prescription_{prescription_id}.pdf"

    pdf = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PrescriptionTitle",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#17365D"),
        alignment=TA_CENTER,
        spaceAfter=10
    )

    heading_style = ParagraphStyle(
        "PrescriptionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#17365D"),
        spaceBefore=12,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        "PrescriptionBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13
    )

    label_style = ParagraphStyle(
        "PrescriptionLabel",
        parent=body_style,
        fontName="Helvetica-Bold"
    )

    story = []

    # Header
    story.append(
        Paragraph("MEDICAL PRESCRIPTION", title_style)
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#17365D")
        )
    )

    story.append(Spacer(1, 12))

    # Patient Details
    story.append(
        Paragraph("Patient Details", heading_style)
    )

    patient_details = [
        ["Patient Name", data.get("patient_name")],
        ["Patient Email", data.get("patient_email")]
    ]

    patient_rows = [
        [
            Paragraph(safe_text(label), label_style),
            Paragraph(safe_text(value), body_style)
        ]
        for label, value in patient_details
    ]

    patient_table = Table(
        patient_rows,
        colWidths=[45 * mm, 115 * mm]
    )

    patient_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF0F8")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 8)
    ]))

    story.append(patient_table)

    # Provider Details
    story.append(
        Paragraph("Provider Details", heading_style)
    )

    provider_details = [
        ["Provider Name", data.get("provider_name")],
        ["Qualification", data.get("provider_qualification")]
    ]

    provider_rows = [
        [
            Paragraph(safe_text(label), label_style),
            Paragraph(safe_text(value), body_style)
        ]
        for label, value in provider_details
    ]

    provider_table = Table(
        provider_rows,
        colWidths=[45 * mm, 115 * mm]
    )

    provider_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF0F8")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 8)
    ]))

    story.append(provider_table)

    # Prescription Information
    story.append(
        Paragraph("Prescription Information", heading_style)
    )

    prescription_details = [
        ["Prescription ID", prescription_id],
        ["Issued At", format_datetime(data.get("issued_at"))],
        ["Status", data.get("status")]
    ]

    details_rows = [
        [
            Paragraph(safe_text(label), label_style),
            Paragraph(safe_text(value), body_style)
        ]
        for label, value in prescription_details
    ]

    details_table = Table(
        details_rows,
        colWidths=[45 * mm, 115 * mm]
    )

    details_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF0F8")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 8)
    ]))

    story.append(details_table)

    # Prescription Notes
    story.append(
        Paragraph("Prescription Notes", heading_style)
    )

    story.append(
        Paragraph(
            safe_text(data.get("notes")),
            body_style
        )
    )

    # Medication Items
    story.append(
        Paragraph("Prescribed Medications", heading_style)
    )

    medication_data = [[
        "Medication",
        "Dosage",
        "Frequency",
        "Duration",
        "Quantity",
        "Instructions"
    ]]

    for item in items:

        medication_data.append([
            Paragraph(safe_text(item.get("medication_name")), body_style),
            Paragraph(safe_text(item.get("dosage")), body_style),
            Paragraph(safe_text(item.get("frequency")), body_style),
            Paragraph(f"{safe_text(item.get('duration_days'))} days", body_style),
            Paragraph(safe_text(item.get("quantity")), body_style),
            Paragraph(safe_text(item.get("instructions")), body_style)
        ])

    medication_table = Table(
        medication_data,
        colWidths=[
            30 * mm,
            17 * mm,
            24 * mm,
            19 * mm,
            15 * mm,
            55 * mm
        ],
        repeatRows=1
    )

    medication_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white,
            colors.HexColor("#F4F7FB")
        ])
    ]))

    story.append(medication_table)

    # Footer
    story.append(Spacer(1, 20))

    story.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.lightgrey
        )
    )

    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            "This document reflects the prescription information "
            "recorded in the Patient Care system. Follow the prescribing "
            "provider's instructions.",
            ParagraphStyle(
                "PrescriptionFooter",
                parent=body_style,
                alignment=TA_CENTER,
                fontSize=8,
                textColor=colors.grey
            )
        )
    )

    pdf.build(story)

    return str(file_path)
