"""Bounded orchestration for appointment recommendations.

The OpenAI model may select read-only functions, while the application owns all
database access, limits, audit records, and the later booking confirmation.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
import json
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from openai import OpenAI, OpenAIError
from sqlalchemy.orm import Session

from agents.prompts import APPOINTMENT_AGENT_INSTRUCTIONS
from agents.state import AppointmentAgentState
from agents.tools import find_active_providers, find_earliest_slots, list_specialties, search_specialties
from config.settings import settings
from models.agent_run import AgentRun, AgentRunStatus
from models.user import User
from schemas.assistant import AppointmentPlanRequest


MAX_TOOL_ROUNDS = 6
DISCLAIMER = (
    "This is a scheduling recommendation, not a diagnosis or medical advice. "
    "For severe or emergency symptoms, seek immediate emergency care."
)


def _commit_run(db: Session, run: AgentRun) -> None:
    try:
        db.commit()
        db.refresh(run)
    except Exception:
        db.rollback()
        raise


def _tool_definitions() -> list[dict]:
    return [
        {"type": "function", "name": "search_specialties", "description": "Search the configured specialty catalog by a short phrase.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"], "additionalProperties": False}},
        {"type": "function", "name": "list_specialties", "description": "List all configured specialties when a narrow search is inconclusive.", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}},
    ]


def _model_specialty_ids(db: Session, request: AppointmentPlanRequest, state: AppointmentAgentState) -> list[int]:
    """Let the model choose catalog searches, but return only catalog IDs."""
    if not settings.openai_api_key:
        state.record("model_unavailable", reason="OPENAI_API_KEY is not configured; searching all specialties")
        return []
    client = OpenAI(api_key=settings.openai_api_key)
    input_items: list[dict] = [{"role": "user", "content": request.symptom_description}]
    found: list[dict] = []
    try:
        for _ in range(MAX_TOOL_ROUNDS):
            response = client.responses.create(
                model=settings.openai_agent_model,
                instructions=APPOINTMENT_AGENT_INSTRUCTIONS,
                input=input_items,
                tools=_tool_definitions(),
            )
            calls = [item for item in response.output if item.type == "function_call"]
            if not calls:
                break
            input_items.extend(response.output)
            for call in calls:
                arguments = json.loads(call.arguments)
                if call.name == "search_specialties":
                    result = search_specialties(db, arguments["query"])
                else:
                    result = list_specialties(db)
                found.extend(result)
                state.record(call.name, arguments=arguments, result_count=len(result))
                input_items.append({"type": "function_call_output", "call_id": call.call_id, "output": json.dumps(result)})
    except (OpenAIError, ValueError, json.JSONDecodeError) as error:
        state.record("model_error", error="Specialty matching fell back to broad availability search")
        return []
    # Preserve catalog order while removing duplicates.  The model can only surface IDs returned by tools.
    return list(dict.fromkeys(item["id"] for item in found))


def _slot_response(slot: dict) -> dict:
    return {
        "provider_id": slot["id"],
        "provider_name": slot["name"],
        "specialty_names": slot["specialties"],
        # AgentRun.result is JSONB, so persist ISO strings rather than Python
        # datetime instances. Pydantic converts these back for the API response.
        "start_datetime": slot["start_datetime"].isoformat(),
        "end_datetime": slot["end_datetime"].isoformat(),
    }


def _confirmation_message(slot: dict, appointment_type: str) -> str:
    specialties = ", ".join(slot["specialties"]) or "the selected service"
    return (
        f"Proposed {appointment_type.lower().replace('_', ' ')} appointment with "
        f"{slot['name']} ({specialties}) on {slot['start_datetime']:%A, %d %B at %I:%M %p}. "
        "Please confirm to book this time."
    )


def create_appointment_plan(db: Session, current_user: User, request: AppointmentPlanRequest) -> dict:
    run = AgentRun(
        user_id=current_user.id,
        goal=request.symptom_description,
        status=AgentRunStatus.RUNNING,
        steps=[],
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    _commit_run(db, run)
    state = AppointmentAgentState(goal=request.symptom_description)
    try:
        specialty_ids = _model_specialty_ids(db, request, state)
        providers = find_active_providers(db, specialty_ids or None)
        if request.preferred_provider_id:
            providers = [provider for provider in providers if provider["id"] == request.preferred_provider_id]
        state.record("find_active_providers", specialty_ids=specialty_ids, result_count=len(providers))
        start_date = request.preferred_start_date or datetime.now(ZoneInfo("Asia/Kolkata")).date()
        slots = find_earliest_slots(db, providers, start_date, request.search_days, request.duration_minutes)
        state.record("find_earliest_slots", start_date=start_date.isoformat(), search_days=request.search_days, result_count=len(slots))
        recommendation = _slot_response(slots[0]) if slots else None
        result = {
            "request": request.model_dump(mode="json"),
            "recommendation": recommendation,
            "alternatives": [_slot_response(slot) for slot in slots[1:]],
            "matching_specialties": sorted({name for provider in providers for name in provider["specialties"]}),
        }
        run.status = AgentRunStatus.COMPLETED
        run.completed_at = datetime.now(timezone.utc)
        run.steps = state.steps
        run.result = result
        _commit_run(db, run)
        return {"agent_run_id": run.id, "status": run.status.value, **result, "confirmation_message": _confirmation_message(slots[0], request.appointment_type.value) if slots else None, "disclaimer": DISCLAIMER}
    except Exception as error:
        run.status = AgentRunStatus.FAILED
        run.completed_at = datetime.now(timezone.utc)
        run.steps = state.steps
        run.error_message = "Unable to prepare an appointment recommendation."
        _commit_run(db, run)
        raise


def confirm_appointment_plan(db: Session, current_user: User, run_id: int):
    """Book only an approved plan and rely on the normal service to revalidate it."""
    run = db.query(AgentRun).filter(AgentRun.id == run_id, AgentRun.user_id == current_user.id).first()
    if not run or run.status != AgentRunStatus.COMPLETED or not run.result or not run.result.get("recommendation"):
        raise HTTPException(status_code=404, detail="Bookable appointment plan not found")
    recommendation = run.result["recommendation"]
    request = run.result["request"]
    from services.appointment_service import create_appointment
    appointment = create_appointment(db, current_user, {
        "provider_id": recommendation["provider_id"],
        "appointment_type": request["appointment_type"],
        "start_datetime": datetime.fromisoformat(recommendation["start_datetime"]),
        "end_datetime": datetime.fromisoformat(recommendation["end_datetime"]),
        "reason": request["symptom_description"],
    })
    run.result = {**run.result, "appointment_id": appointment.id}
    run.steps = [*run.steps, {"tool": "create_appointment", "appointment_id": appointment.id}]
    _commit_run(db, run)
    return appointment
