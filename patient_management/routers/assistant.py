from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from agents.rag import (
    RAGServiceError,
    answer_patient_question,
    authorise_patient_history_access,
    index_patient_history,
)
from agents.graph import create_appointment_plan, confirm_appointment_plan
from database.connection import get_db
from dependencies.auth import require_roles
from models.user import User
from schemas.assistant import (
    PatientAnswerResponse,
    PatientQuestionRequest,
    RAGCitation,
    ReindexPatientResponse,
    AppointmentPlanRequest,
    AppointmentPlanResponse,
    AppointmentPlanConfirmationResponse,
)


router = APIRouter(prefix="/assistant", tags=["Patient History Assistant"])


@router.post("/appointment-plans", response_model=AppointmentPlanResponse)
def create_plan(
    payload: AppointmentPlanRequest,
    current_user: User = Depends(require_roles("PATIENT")),
    db: Session = Depends(get_db),
):
    return create_appointment_plan(db, current_user, payload)


@router.post("/appointment-plans/{run_id}/confirm", response_model=AppointmentPlanConfirmationResponse, status_code=201)
def confirm_plan(
    run_id: int,
    current_user: User = Depends(require_roles("PATIENT")),
    db: Session = Depends(get_db),
):
    appointment = confirm_appointment_plan(db, current_user, run_id)
    return AppointmentPlanConfirmationResponse(agent_run_id=run_id, appointment_id=appointment.id, status=appointment.status.value)


@router.post(
    "/patients/{patient_id}/ask",
    response_model=PatientAnswerResponse,
)
def ask_patient_history(
    patient_id: int,
    payload: PatientQuestionRequest,
    current_user: User = Depends(require_roles("PATIENT", "PROVIDER", "ADMIN")),
    db: Session = Depends(get_db),
):
    authorise_patient_history_access(db, patient_id, current_user)
    try:
        answer, sources = answer_patient_question(db, patient_id, payload.question)
    except RAGServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    return PatientAnswerResponse(
        answer=answer,
        sources=[
            RAGCitation(
                source_type=source.source_type,
                source_id=source.source_id,
                appointment_id=source.appointment_id,
                appointment_date=source.appointment_date,
                relevance_score=source.relevance_score,
            )
            for source in sources
        ],
    )


@router.post(
    "/patients/{patient_id}/reindex",
    response_model=ReindexPatientResponse,
)
def reindex_patient_history(
    patient_id: int,
    current_user: User = Depends(require_roles("PROVIDER", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Index existing sample data after enabling RAG for the first time."""
    authorise_patient_history_access(db, patient_id, current_user)
    try:
        indexed_chunks = index_patient_history(db, patient_id)
    except RAGServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    return ReindexPatientResponse(
        patient_id=patient_id,
        indexed_chunks=indexed_chunks,
    )
