## Goal
Build an Italian-first AI receptionist and luxury hotel concierge for Sina Hotels (Sina Bernini Bristol, Rome) that answers phone calls, checks real-time room availability, creates, modifies, and cancels bookings, handles early departures, manages Guest 360 CRM profiles, coordinates concierge services, and dispatches owner/management notifications.

**Primary MVP flow:** Phone call (Twilio Media Streams) → Voice pipeline (VAD / Groq Whisper STT / ElevenLabs TTS) → Native VoiceAgent → Typed Tools → Deterministic Services → Supabase CRM/Database → Owner/Guest Notifications (Email/SMS).

---

## Principles
- **Dual Scope:** Primary focus on 5-star luxury hotel reception and concierge services; secondary legacy support for restaurant table reservations.
- **Deterministic Business Logic:** The LLM understands natural Italian caller requests and selects tools; deterministic Python services enforce pricing, availability, identity verification, and database mutations.
- **Strict Hallucination Prevention:** Never invent room availability, rates, policies, or successful actions. Only quote prices and confirmation codes returned by services.
- **Human Escalation:** When uncertain or handling complex scenarios (> 10 guests, custom events), take a detailed message and notify the management/owner.
- **AI Transparency:** Clearly identify the assistant as an AI virtual receptionist in the greeting.
- **Guest Safety:** Record dietary restrictions and allergies, but always state the mandatory safety disclaimer reminding the guest to inform waitstaff upon arrival. Never guarantee 100% allergen safety.
- **Data Minimization:** Stream audio in-memory; do not store raw caller audio. Minimize and redact PII.

---

## Core Capabilities

### 1. Hotel Room Bookings & Inventory (Primary)
- Real-time room availability checking across 4 tiers:
  - **Superior:** €250 / night (max 2 guests)
  - **Deluxe con Vista Città:** €350 / night (max 2 guests)
  - **Junior Suite con Balcone:** €480 / night (max 3 guests)
  - **Suite Panoramica Barberini:** €750 / night (max 4 guests, 360° terrace, jacuzzi)
- Booking creation with read-back confirmation and reference code generation (e.g. `SINA-XXXX`).
- Booking modifications and cancellations with identity verification (phone number + reservation code).
- Early departure registration (`report_early_departure`): recalculates billing, releases room, and alerts housekeeping.
- Automated email and SMS booking confirmations via SendGrid/SMTP and Twilio.

### 2. Guest 360 CRM & Personalization
- Recognition of repeat and in-house guests by caller ID phone number.
- VIP tier handling (Standard, Silver, Gold, Platinum, VIP) and personalized greetings.
- Persistent guest preferences: dietary restrictions, room preferences, favorite drinks, and special occasion notes.
- Immediate allergy alerts to management upon recording food allergies.

### 3. Concierge Services & Hotel FAQs
- Concierge request intake: dining recommendations, private airport transfers, Spa & Wellness bookings, and city experiences.
- Official hotel service FAQs: check-in (15:00), check-out (12:00), gourmet breakfast hours, Rooftop Restaurant "The Flair", spa treatments, and valet parking.
- Guest feedback and NPS score collection (1-10) with management notification.

### 4. Restaurant Table Bookings (Secondary / Legacy)
- Table availability checking for restaurant slots.
- Table reservation creation, modification, and cancellation (`BV-XXXX`).
- Restaurant FAQs (opening hours, parking agreements, pets, dress code).
- Owner message escalation for large groups (> 10 people) or human manager requests.

---

## Architecture & Layers
- **Voice layer (`src/voice/`):** Twilio media streams WebSocket, WebRTC Voice Activity Detection (VAD) with RMS pre-filter, Groq Whisper STT, ElevenLabs TTS, and real-time barge-in interruption handling.
- **Agent layer (`src/voice/agent.py`, `src/agent/`):** Fast async single-loop LLM agent with native tool-calling, dynamic Italian system prompts, context management, and session store.
- **Tools layer (`src/voice/tools.py`, `src/tools/`):** OpenAI/Groq function calling schemas with code-level guardrails, date validation, and deterministic caller phone injection.
- **Services layer (`src/services/`):** Pure deterministic business rules (`HotelBookingService`, `GuestCRMService`, `BookingService`, `AvailabilityService`, `RestaurantService`, `NotificationService`).
- **Integrations layer (`src/integrations/`):** Twilio SMS/telephony and SMTP email delivery with luxury Italian templates.
- **Repositories & Storage (`src/repositories/`):** Abstract repository interfaces with dual implementations: Supabase PostgreSQL tables and fast in-memory stores for testing.

Never let the LLM run SQL or write directly to the database. Always enforce: `Agent → Tool → Service → Repository → DB`.

---

## Reservation & Business Rules
- **Dates & Timezone:** Resolve relative dates (e.g., "stasera", "dopodomani", "questo weekend") explicitly against Europe/Rome date. Reject check-in dates in the past and check-outs before check-in.
- **Identity Verification:** Require booking reference code and matching guest phone number before modifying or cancelling any reservation.
- **Read-Back Confirmation:** Require caller read-back confirmation of dates, category, and total rate before creating room bookings.
- **Alternative Slots:** Offer only alternative dates or times explicitly returned by availability services.
- **Graceful Failure:** On service or network errors, never pretend success; apologize politely and offer to take a message for the reception team.

---

## Engineering Conventions
- **Stack:** Python 3.12+, `uv`, FastAPI, Pydantic v2, Groq, Twilio, ElevenLabs, Supabase, pytest, Ruff, pre-commit, GitHub Actions.
- **Type Safety:** Type hints throughout with typed Pydantic models in `src/models/`.
- **Modular Design:** Prompts, tools, business logic, routes, and voice streaming reside in strictly separated packages.
- **Testing Standards:** Comprehensive unit tests, integration tests, agent flow tests, and LLM evaluations under `tests/`.

---

## Repository Structure
```text
src/
  agent/          # System prompts (hotel & restaurant), date formatting
  api/
    middleware/   # API key authentication & security
    routes/       # Chat, Twilio, CRM, Room Bookings, Reservations
    main.py       # FastAPI application & lifespan pre-cached services
  config.py       # Pydantic BaseSettings & environment variables
  integrations/   # TwilioService (SMS/call) & EmailService (SMTP)
  models/         # Pydantic domain models (hotel, CRM, restaurant, notifications)
  repositories/   # Abstract bases, Supabase implementations, and in-memory stores
  services/       # Deterministic business logic & reservation engines
  tools/          # Tool schemas & definitions
  voice/          # WebRTC VAD, Twilio WebSocket streaming, TTS/STT, VoiceAgent
tests/
  agent/          # Scripted mock multi-turn agent flow tests
  evals/          # LLM evaluation tests with live Groq tool calling (pytest.mark.eval)
  integration/    # REST API & WebSocket endpoint integration tests
  unit/           # Services, VAD, tools, and notification delivery unit tests
```

---

## Development Workflow
1. Define tool contracts, schemas, and acceptance tests.
2. Build and test deterministic business services in isolation.
3. Test agent orchestration and multi-turn conversational guardrails.
4. Verify voice streaming, VAD interruptions, and notification dispatches.
5. Run full test suite (`uv run pytest tests/unit tests/integration`) and LLM evaluation scenarios (`uv run pytest tests/evals -m eval`).

**North star:** Be conversational and welcoming at the edges; keep business operations, pricing, and database state completely deterministic.
