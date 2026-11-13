# Appointment Concierge API

The Appointment Concierge is a read-only, tool-driven scheduling workflow. It
uses the configured OpenAI model to search the application's specialty catalog,
then checks the application's own provider calendars. It never books an
appointment until the patient explicitly confirms the recommendation.

## Create a plan

`POST /assistant/appointment-plans` is available to authenticated patients.

```json
{
  "symptom_description": "I have a persistent cough and need the earliest appointment.",
  "preferred_start_date": "2026-11-16",
  "search_days": 14,
  "duration_minutes": 30,
  "appointment_type": "IN_PERSON"
}
```

The response contains the `agent_run_id`, the earliest suitable real slot,
alternatives, a confirmation-message draft, and a scheduling-only disclaimer.
`agent_runs` retains the tool activity and recommendation for audit purposes.

If `OPENAI_API_KEY` is absent, local development falls back to searching the
configured provider catalog broadly; scheduling and availability validation
remain fully server-side.

## Confirm a plan

`POST /assistant/appointment-plans/{agent_run_id}/confirm` books only the
recommended slot belonging to the requesting patient. The existing appointment
service validates provider availability again immediately before the booking,
so a stale recommendation cannot bypass conflict checks.
