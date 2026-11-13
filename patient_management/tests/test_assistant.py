from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from agents.rag import (
    RetrievedChunk,
    authorise_patient_history_access,
    build_prescription_text,
    chunk_text,
)
from models.user import UserRole
from schemas.assistant import PatientQuestionRequest
from schemas.assistant import AppointmentPlanRequest
from agents.graph import _confirmation_message, _slot_response


def test_question_requires_meaningful_bounded_text():
    assert PatientQuestionRequest(question="Summarize the last visit").question
    with pytest.raises(ValueError):
        PatientQuestionRequest(question="no")
    with pytest.raises(ValueError):
        PatientQuestionRequest(question="x" * 501)


def test_chunk_text_preserves_short_visit_note():
    text = "Visit summary: symptoms improved after treatment."
    assert chunk_text(text) == [text]


def test_chunk_text_splits_long_visit_note_without_empty_chunks():
    chunks = chunk_text("word " * 1_000)
    assert len(chunks) > 1
    assert all(chunk.strip() for chunk in chunks)


def test_citation_metadata_can_be_represented():
    citation = RetrievedChunk(
        source_type="VISIT_NOTE",
        source_id=12,
        content="record text",
        relevance_score=0.9,
        appointment_id=42,
        appointment_date=datetime(2026, 11, 2, tzinfo=timezone.utc),
    )
    assert citation.source_id == 12


def test_build_prescription_text_includes_medication_details():
    prescription = Mock(
        id=8,
        issued_at=datetime(2026, 11, 13, tzinfo=timezone.utc),
        status="ACTIVE",
        provider=Mock(first_name="Asha", last_name="Sharma"),
        appointment_id=1,
        notes="Take with food",
        items=[Mock(
            medication_name="Paracetamol",
            dosage="500 mg",
            frequency="Twice daily",
            duration_days=5,
            quantity=10,
            instructions="After meals",
        )],
    )

    text = build_prescription_text(prescription)

    assert "[PRESCRIPTION:8 | 2026-11-13]" in text
    assert "Paracetamol" in text
    assert "Dosage: 500 mg" in text
    assert "Frequency: Twice daily" in text
    assert "Instructions: After meals" in text


def test_patient_cannot_access_another_patient_history():
    db = Mock()
    requested_patient = Mock(user_id=2)
    db.query.return_value.filter.return_value.first.return_value = requested_patient
    current_user = Mock(role=UserRole.PATIENT, id=1)

    with pytest.raises(HTTPException) as error:
        authorise_patient_history_access(db, 20, current_user)

    assert error.value.status_code == 403


def test_appointment_plan_request_has_safe_scheduling_defaults():
    request = AppointmentPlanRequest(symptom_description="A persistent cough")

    assert request.search_days == 14
    assert request.duration_minutes == 30


def test_slot_audit_payload_is_json_serialisable_and_message_is_factual():
    slot = {
        "id": 8,
        "name": "Asha Sharma",
        "specialties": ["General Medicine"],
        "start_datetime": datetime(2026, 11, 16, 10, 30, tzinfo=timezone.utc),
        "end_datetime": datetime(2026, 11, 16, 11, 0, tzinfo=timezone.utc),
    }

    payload = _slot_response(slot)
    message = _confirmation_message(slot, "IN_PERSON")

    assert payload["start_datetime"] == "2026-11-16T10:30:00+00:00"
    assert "Asha Sharma" in message
    assert "Please confirm" in message
