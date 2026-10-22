## Goal
Build an Italian-first AI receptionist that answers restaurant calls when staff are busy, checks real availability, books or updates tables, records relevant guest notes, and notifies the owner.

**MVP flow:** Phone call → Voice (STT/TTS) → Agent → booking tools → CRM/database → owner notification.

## Principles
- Keep the MVP focused on restaurant phone bookings.
- The LLM understands requests and selects tools; deterministic services enforce business rules and modify data.
- Never invent availability, menu details, prices, policies, or successful actions.
- If uncertain, ask a clarification or take a message/escalate.
- Clearly identify the assistant as AI.
- Record dietary/allergy notes, but never guarantee allergen safety.
- Collect only necessary data; do not store raw audio by default.

## MVP capabilities
1. Answer restaurant FAQs using trusted data.
2. Check table availability.
3. Create, modify, and cancel reservations.
4. Add booking notes/preferences.
5. Take messages and notify the owner.

## Architecture
- **Voice layer:** telephony, speech-to-text, text-to-speech, interruptions.
- **Agent (LangGraph):** conversation state, intent/entity extraction, tool selection, clarification, escalation.
- **Tools/services:** typed inputs/outputs, validation, authorization, deterministic business rules.
- **CRM/database:** source of truth for restaurant settings, reservations, customer details, and notes.

Never let the LLM run arbitrary SQL or write directly to the database. Use `Agent → Tool → Service → CRM/DB`.

## Reservation rules
- Gather required details: date, time, party size, and contact/name according to restaurant policy.
- Use the restaurant's timezone; resolve relative dates explicitly.
- Check availability before booking. Offer only alternatives returned by the system.
- Confirm success to the caller only after the booking service confirms it.
- Require appropriate verification/confirmation for modifications and cancellations.
- On API failure, do not pretend success; offer to take a message or escalate.

## Privacy and security
- Never hard-code or commit secrets. Use environment variables/secret management.
- Minimize personal data and redact sensitive values from logs.
- Apply access controls and audit important actions.
- Only claim data stays in Italy or within Fastweb infrastructure if the actual deployment proves it.

## Engineering conventions
Preferred stack: Python 3.12+, `uv`, FastAPI, Pydantic, LangGraph, pytest, Ruff, Ty, pre-commit, GitHub Actions.

- Use type hints and typed Pydantic schemas.
- Keep prompts, orchestration, integrations, and business logic in separate modules.
- Test from the beginning: booking success, full slot, alternatives, changes, cancellations, dietary notes, unknown questions, human requests, and dependency failures.
- Give the voice agent concise, natural Italian responses.

## Suggested structure
```text
src/
  api/
  agent/       # graph, state, prompts, policies
  tools/       # booking, restaurant, customer, notifications
  services/    # business rules
  repositories/
  integrations/ # CRM, telephony, messaging
  models/
tests/         # unit, agent, integration, evals
```

## Development workflow
1. Define intents, tool contracts, CRM schema, and acceptance tests before coding.
2. Build and test deterministic booking/CRM services.
3. Add agent orchestration and guardrails.
4. Integrate voice and owner notifications.
5. Demo an end-to-end call, including a full time slot or another curveball.

**North star:** Be conversational at the edges; keep business operations deterministic. When in doubt, verify, clarify, or take a message.
