import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session, joinedload

from config.settings import settings
from database.connection import get_db

from models.appointment import Appointment, AppointmentStatus
from models.prescription import Prescription
from models.patient import Patient

from schemas.internal_documents import (
    VisitSummaryDocumentData,
    PrescriptionDocumentData,
)

from routers.internal_appointments import verify_internal_token


router = APIRouter(
    prefix="/internal/documents",
    tags=["Internal Document Communication"]
)


@router.get(
    "/appointments/{appointment_id}/visit-summary-data",
    response_model=VisitSummaryDocumentData,
    dependencies=[Depends(verify_internal_token)]
)
def get_visit_summary_document_data(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    appointment = (
        db.query(Appointment)
        .options(
            joinedload(Appointment.patient)
            .joinedload(Patient.user),
            joinedload(Appointment.provider),
            joinedload(Appointment.visit_note)
        )
        .filter(Appointment.id == appointment_id)
        .first()
    )

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    if appointment.status != AppointmentStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Visit summary is available only for completed appointments"
        )

    if not appointment.visit_note:
        raise HTTPException(
            status_code=404,
            detail="Visit note not found for this appointment"
        )

    patient = appointment.patient
    provider = appointment.provider
    note = appointment.visit_note

    if not patient or not patient.user or not patient.user.email:
        raise HTTPException(
            status_code=404,
            detail="Patient email information not found"
        )

    return VisitSummaryDocumentData(
        appointment_id=appointment.id,
        appointment_type=appointment.appointment_type.value,
        appointment_status=appointment.status.value,
        appointment_datetime=appointment.start_datetime,
        appointment_reason=appointment.reason,

        patient_name=f"{patient.first_name} {patient.last_name}",
        patient_email=patient.user.email,

        provider_name=f"{provider.first_name} {provider.last_name}",
        provider_qualification=provider.qualification,

        symptoms=note.symptoms,
        diagnosis=note.diagnosis,
        treatment_plan=note.treatment_plan,
        follow_up_instructions=note.follow_up_instructions,
        summary=note.summary
    )


@router.get(
    "/prescriptions/{prescription_id}/data",
    response_model=PrescriptionDocumentData,
    dependencies=[Depends(verify_internal_token)]
)
def get_prescription_document_data(
    prescription_id: int,
    db: Session = Depends(get_db)
):
    prescription = (
        db.query(Prescription)
        .options(
            joinedload(Prescription.patient)
            .joinedload(Patient.user),
            joinedload(Prescription.provider),
            joinedload(Prescription.items)
        )
        .filter(Prescription.id == prescription_id)
        .first()
    )

    if not prescription:
        raise HTTPException(
            status_code=404,
            detail="Prescription not found"
        )

    patient = prescription.patient
    provider = prescription.provider

    if not patient or not patient.user or not patient.user.email:
        raise HTTPException(
            status_code=404,
            detail="Patient email information not found"
        )

    return PrescriptionDocumentData(
        prescription_id=prescription.id,
        issued_at=prescription.issued_at,
        status=prescription.status.value,
        notes=prescription.notes,

        patient_name=f"{patient.first_name} {patient.last_name}",
        patient_email=patient.user.email,

        provider_name=f"{provider.first_name} {provider.last_name}",
        provider_qualification=provider.qualification,

        items=[
            {
                "medication_name": item.medication_name,
                "dosage": item.dosage,
                "frequency": item.frequency,
                "duration_days": item.duration_days,
                "quantity": item.quantity,
                "instructions": item.instructions
            }
            for item in prescription.items
        ]
    )