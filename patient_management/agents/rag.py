"""Patient-history retrieval augmented generation (RAG) services.

Embeddings remain in the existing ``record_chunks`` table. This is suitable for
the project's sample-data scale and deliberately avoids adding a vector-database
service. Every query is filtered by patient_id before similarity ranking.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
from typing import Iterable

from fastapi import HTTPException, status
from openai import OpenAI, OpenAIError
from sqlalchemy.orm import Session, joinedload

from agents.prompts import RAG_INSTRUCTIONS, build_rag_input
from config.settings import settings
from models.appointment import Appointment
from models.patient import Patient
from models.provider import Provider
from models.prescription import Prescription
from models.record_chunk import RecordChunk
from models.user import User, UserRole
from models.visit_note import VisitNote


SOURCE_TYPE_VISIT_NOTE = "VISIT_NOTE"
SOURCE_TYPE_PRESCRIPTION = "PRESCRIPTION"
CHUNK_SIZE = 1_500
CHUNK_OVERLAP = 200
MIN_RELEVANCE_SCORE = 0.20


class RAGServiceError(RuntimeError):
    """Raised when the RAG provider cannot serve a request."""


@dataclass(frozen=True)
class RetrievedChunk:
    source_type: str
    source_id: int
    content: str
    relevance_score: float
    appointment_id: int | None
    appointment_date: datetime | None


def _client() -> OpenAI:
    if not settings.openai_api_key:
        raise RAGServiceError(
            "RAG is not configured. Set OPENAI_API_KEY in patient_management/.env."
        )
    return OpenAI(api_key=settings.openai_api_key)


def _normalise(vector: Iterable[float]) -> list[float]:
    values = [float(value) for value in vector]
    magnitude = math.sqrt(sum(value * value for value in values))
    if not magnitude:
        raise RAGServiceError("Received an empty embedding vector.")
    return [value / magnitude for value in values]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        return -1.0
    return sum(a * b for a, b in zip(left, right))


def create_embeddings(texts: list[str]) -> list[list[float]]:
    """Create normalised embeddings in one API request."""
    clean_texts = [text.strip() for text in texts if text and text.strip()]
    if not clean_texts:
        return []

    try:
        response = _client().embeddings.create(
            model=settings.openai_embedding_model,
            input=clean_texts,
            encoding_format="float",
        )
    except OpenAIError as error:
        raise RAGServiceError("Embedding request failed.") from error

    return [_normalise(item.embedding) for item in response.data]


def build_visit_note_text(visit_note: VisitNote) -> str:
    """Produce self-describing, retrieval-friendly text from a visit note."""
    appointment = visit_note.appointment
    provider = appointment.provider
    appointment_date = appointment.start_datetime.date().isoformat()
    provider_name = f"{provider.first_name} {provider.last_name}"

    fields = [
        ("Symptoms", visit_note.symptoms),
        ("Diagnosis", visit_note.diagnosis),
        ("Treatment plan", visit_note.treatment_plan),
        ("Follow-up instructions", visit_note.follow_up_instructions),
        ("Visit summary", visit_note.summary),
    ]
    body = "\n".join(f"{label}: {value}" for label, value in fields if value)
    return (
        f"[VISIT_NOTE:{visit_note.id} | {appointment_date}]\n"
        f"Appointment ID: {appointment.id}\n"
        f"Provider: {provider_name}\n"
        f"{body}"
    )


def chunk_text(text: str) -> list[str]:
    """Split unusually long records without cutting words in half."""
    text = " ".join(text.split())
    if len(text) <= CHUNK_SIZE:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + CHUNK_SIZE)
        if end < len(text):
            boundary = text.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


def index_visit_note(db: Session, visit_note: VisitNote) -> int:
    """Replace index chunks for one visit note and return the chunk count."""
    note = (
        db.query(VisitNote)
        .options(
            joinedload(VisitNote.appointment).joinedload(Appointment.provider)
        )
        .filter(VisitNote.id == visit_note.id)
        .one()
    )

    content_chunks = chunk_text(build_visit_note_text(note))
    embeddings = create_embeddings(content_chunks)

    db.query(RecordChunk).filter(
        RecordChunk.source_type == SOURCE_TYPE_VISIT_NOTE,
        RecordChunk.source_id == note.id,
    ).delete(synchronize_session=False)

    for index, (content, embedding) in enumerate(zip(content_chunks, embeddings)):
        db.add(
            RecordChunk(
                patient_id=note.appointment.patient_id,
                source_type=SOURCE_TYPE_VISIT_NOTE,
                source_id=note.id,
                chunk_index=index,
                content=content,
                embedding=embedding,
            )
        )

    db.commit()
    return len(content_chunks)


def index_patient_visit_notes(db: Session, patient_id: int) -> int:
    notes = (
        db.query(VisitNote)
        .join(Appointment, VisitNote.appointment_id == Appointment.id)
        .filter(Appointment.patient_id == patient_id)
        .all()
    )
    return sum(index_visit_note(db, note) for note in notes)


def build_prescription_text(prescription: Prescription) -> str:
    """Build searchable text from a prescription and its medication items."""
    provider = prescription.provider
    provider_name = f"{provider.first_name} {provider.last_name}"
    lines = [
        f"[PRESCRIPTION:{prescription.id} | {prescription.issued_at.date().isoformat()}]",
        f"Prescription status: {prescription.status.value if hasattr(prescription.status, 'value') else prescription.status}",
        f"Provider: {provider_name}",
    ]
    if prescription.appointment_id is not None:
        lines.append(f"Appointment ID: {prescription.appointment_id}")
    if prescription.notes:
        lines.append(f"Prescription notes: {prescription.notes}")

    for index, item in enumerate(prescription.items, start=1):
        lines.extend([
            f"Medication {index}: {item.medication_name}",
            f"Dosage: {item.dosage}",
            f"Frequency: {item.frequency}",
            f"Duration: {item.duration_days} days",
            f"Quantity: {item.quantity}",
        ])
        if item.instructions:
            lines.append(f"Instructions: {item.instructions}")
    return "\n".join(lines)


def index_prescription(db: Session, prescription: Prescription) -> int:
    """Replace the searchable chunk for one prescription."""
    record = (
        db.query(Prescription)
        .options(
            joinedload(Prescription.provider),
            joinedload(Prescription.items),
        )
        .filter(Prescription.id == prescription.id)
        .one()
    )
    content_chunks = chunk_text(build_prescription_text(record))
    embeddings = create_embeddings(content_chunks)

    db.query(RecordChunk).filter(
        RecordChunk.source_type == SOURCE_TYPE_PRESCRIPTION,
        RecordChunk.source_id == record.id,
    ).delete(synchronize_session=False)

    for index, (content, embedding) in enumerate(zip(content_chunks, embeddings)):
        db.add(RecordChunk(
            patient_id=record.patient_id,
            source_type=SOURCE_TYPE_PRESCRIPTION,
            source_id=record.id,
            chunk_index=index,
            content=content,
            embedding=embedding,
        ))
    db.commit()
    return len(content_chunks)


def index_patient_prescriptions(db: Session, patient_id: int) -> int:
    prescriptions = (
        db.query(Prescription)
        .filter(Prescription.patient_id == patient_id)
        .all()
    )
    return sum(index_prescription(db, item) for item in prescriptions)


def index_patient_history(db: Session, patient_id: int) -> int:
    """Index all currently supported history sources for a patient."""
    return (
        index_patient_visit_notes(db, patient_id)
        + index_patient_prescriptions(db, patient_id)
    )


def _visit_note_metadata(db: Session, note_ids: list[int]) -> dict[int, tuple[int, datetime]]:
    if not note_ids:
        return {}
    note_rows = (
        db.query(VisitNote.id, Appointment.id, Appointment.start_datetime)
        .join(Appointment, VisitNote.appointment_id == Appointment.id)
        .filter(VisitNote.id.in_(note_ids))
        .all()
    )
    result = {
        note_id: (appointment_id, appointment_date)
        for note_id, appointment_id, appointment_date in note_rows
    }
    prescription_rows = (
        db.query(Prescription.id, Prescription.appointment_id, Prescription.issued_at)
        .filter(Prescription.id.in_(note_ids))
        .all()
    )
    for prescription_id, appointment_id, issued_at in prescription_rows:
        result[prescription_id] = (appointment_id, issued_at)
    return result


def retrieve_patient_context(
    db: Session,
    patient_id: int,
    question: str,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    question_embedding = create_embeddings([question])[0]
    chunks = (
        db.query(RecordChunk)
        .filter(
            RecordChunk.patient_id == patient_id,
            RecordChunk.embedding.isnot(None),
        )
        .all()
    )

    ranked = [
        (chunk, _cosine_similarity(question_embedding, list(chunk.embedding)))
        for chunk in chunks
        if chunk.embedding
    ]
    ranked.sort(key=lambda item: item[1], reverse=True)
    selected = [item for item in ranked[:top_k] if item[1] >= MIN_RELEVANCE_SCORE]
    metadata = _visit_note_metadata(
        db,
            [chunk.source_id for chunk, _ in selected],
    )

    return [
        RetrievedChunk(
            source_type=chunk.source_type,
            source_id=chunk.source_id,
            content=chunk.content,
            relevance_score=round(score, 4),
            appointment_id=metadata.get(chunk.source_id, (None, None))[0],
            appointment_date=metadata.get(chunk.source_id, (None, None))[1],
        )
        for chunk, score in selected
    ]


def answer_patient_question(
    db: Session,
    patient_id: int,
    question: str,
) -> tuple[str, list[RetrievedChunk]]:
    retrieved = retrieve_patient_context(db, patient_id, question)
    if not retrieved:
        return "The available patient records do not contain information that answers this question.", []

    context = "\n\n".join(chunk.content for chunk in retrieved)
    try:
        response = _client().responses.create(
            model=settings.openai_rag_model,
            instructions=RAG_INSTRUCTIONS,
            input=build_rag_input(question, context),
        )
    except OpenAIError as error:
        raise RAGServiceError("Answer-generation request failed.") from error

    answer = response.output_text.strip()
    if not answer:
        raise RAGServiceError("The answer model returned no text.")
    return answer, retrieved


def authorise_patient_history_access(
    db: Session,
    patient_id: int,
    current_user: User,
) -> None:
    """Ensure the caller may access this patient's indexed clinical records."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if current_user.role == UserRole.ADMIN:
        return
    if current_user.role == UserRole.PATIENT and patient.user_id == current_user.id:
        return
    if current_user.role == UserRole.PROVIDER:
        provider = db.query(Provider).filter(Provider.user_id == current_user.id).first()
        has_treated_patient = provider and db.query(Appointment.id).filter(
            Appointment.provider_id == provider.id,
            Appointment.patient_id == patient_id,
        ).first()
        if has_treated_patient:
            return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access this patient's history",
    )
