# SINA HOTELS — AI Voice Receptionist & Room CRM

An Italian-first AI hotel voice receptionist and guest CRM built with a **native tool-calling VoiceAgent**, **Groq**, **Twilio Voice**, **ElevenLabs**, and **PostgreSQL/Supabase** for **Sina Bernini Bristol (Roma)**.

The agent handles hotel phone calls: checks real-time room availability across 4 room categories (Superior, Deluxe, Junior Suite, Suite Panoramica), creates and modifies room bookings, tracks early departures, captures guest CRM preferences (allergies, special habits, VIP status), and runs a full-duplex telephony stream with two-tier WebRTC VAD and instant barge-in. It also provides secondary/legacy support for restaurant table reservations.

---

## 🏛️ Architecture & Session State

The system separates **in-memory conversational session state** from **long-term enterprise persistence**:

```mermaid
flowchart TD
    Caller[Caller / Phone / Terminal Simulator] -->|8kHz Audio or Text| Pipeline[FastAPI / TwilioMediaStreamPipeline / CLI]
    Pipeline --> VAD[Two-Tier VAD: RMS Pre-filter + WebRTC VAD]
    Pipeline --> Session[CallSession / SessionStore]
    Session --> Agent[Native Single-Loop VoiceAgent]
    Agent --> Prompts[Italian Luxury Tone 'dare del Lei' / Dynamic Date]
    Agent --> Guardrails[Deterministic Guardrails]
    
    subgraph "Deterministic Guardrails & Security"
        Guardrails --> DateVal[Date Validation: ISO, Non-Past, Duration]
        Guardrails --> ReadBack[Read-Back Confirmation Enforcement]
        Guardrails --> Identity[Caller Phone Authentication & User ID Injection]
    end

    Guardrails --> Tools[Native Tool Dispatcher]
    Tools --> Services[Deterministic Business Rules & Services]

    subgraph "Long-Term Enterprise Memory (Supabase CRM & Database)"
        Services --> Repositories[Repository Layer]
        Repositories --> SupabaseDB[(Supabase PostgreSQL)]
        SupabaseDB --> RoomsTable[hotel_rooms]
        SupabaseDB --> RoomBookings[hotel_bookings]
        SupabaseDB --> GuestsTable[guests & guest_preferences]
        SupabaseDB --> NotifTable[crm_notifications]
    end

    subgraph "Automated Delivery"
        Services --> Notifications[NotificationService]
        Notifications --> TwilioSMS[Twilio SMS: Owner & Guest Alerts]
        Notifications --> SMTPEmail[SMTP Email: Branded Confirmations]
    end
```

---

## ⚡ Native Tool Calling (No LangGraph Overhead)

The agent uses a **single conversational LLM loop** with native OpenAI/Groq function calling (`groq.AsyncGroq`):
- **Zero Framework Bloat**: No LangGraph, LangChain, or external graph routers on the critical audio path.
- **Fast Turnaround (<150ms LLM overhead)**: Single-turn generation with parallel native tool dispatch.
- **Per-Call Session**: Each call maintains an isolated [`CallSession`](file:///home/magesh/Magesh/Projects/Hotel_Voice_Agent/src/voice/session.py) holding message history, booking draft fields, and verification state.
- **Pre-Cached Agent Graph**: Initialized once at app startup in lifespan and shared safely across concurrent calls without memory leaks.

---

## 🛡️ Security & Business Guardrails

1. **Deterministic Identity Injection**: The caller's phone number (`caller_phone`) and `user_id` are injected by our code from the Twilio telephony handshake or session context. They are **never LLM-fillable arguments**, preventing spoofing or unauthorized access to other guests' profiles.
2. **Date Validation**: Check-in dates must be today or in the future; check-out must be strictly after check-in; stays are limited to 30 consecutive nights. Invalid temporal requests are intercepted before touching booking services.
3. **Read-Back Confirmation**: Before room reservations are confirmed in the system, the assistant must read back the dates, category, and total pricing to obtain explicit guest agreement.
4. **Identity Verification Before Modifications**: Cancellation, early departures, and booking modifications strictly verify the caller's phone number against the booking record on file.
5. **Zero Hallucination Availability**: The LLM never invents rooms or prices. Real availability is calculated deterministically by [`HotelBookingService`](file:///home/magesh/Magesh/Projects/Hotel_Voice_Agent/src/services/hotel_booking_service.py). Room rates are dynamically injected into system prompts directly from [`ROOM_CATEGORY_DETAILS`](file:///home/magesh/Magesh/Projects/Hotel_Voice_Agent/src/models/hotel_booking.py#L38) as a single source of truth.
6. **Allergen Disclaimer & Alerts**: Dietary notes and allergies trigger immediate staff alerts via email/SMS. Spoken disclaimer: *"Per la Sua sicurezza La preghiamo di ricordare l'allergia al personale di sala al Suo arrivo."*
7. **Direct Templated Delivery**: SMS confirmations via Twilio REST and luxury branded HTML confirmation emails via SMTP (`aiosmtplib`).
8. **Internal API Security**: Endpoints under `/api/crm`, `/api/reservations`, and `/api/room-bookings` require an `X-API-Key` or `Authorization: Bearer` token. Webhooks support Twilio cryptographic request signature validation (`TWILIO_VALIDATE_SIGNATURE`). CORS is locked down to configurable origins.

---

## 🎙️ Two-Tier Voice Activity Detection (VAD) & Barge-In

The telephony stream uses a two-tier voice detection architecture:
1. **Tier 1 — Fast RMS Pre-Filter**: If audio energy is below `VAD_RMS_PREFILTER_THRESHOLD` (250.0), it is discarded immediately in $<0.01$ ms, preserving CPU compute.
2. **Tier 2 — WebRTC VAD Model**: Audio frames passing the pre-filter are analyzed by [`webrtcvad`](file:///home/magesh/Magesh/Projects/Hotel_Voice_Agent/src/voice/vad.py#L26) (mode 2) at 8kHz PCM to distinguish genuine human vocal cord speech from road traffic, coughing, and background noise.
3. **Instant Barge-In**: When the caller speaks while the assistant is speaking, the bot audio stream is instantly cleared and TTS synthesis is cancelled.

---

## 🚀 Quickstart

### 1. Requirements & Setup
Ensure Python 3.12+ and `uv` are installed.

```bash
# Clone and enter directory
cd Hotel_Voice_Agent

# Create environment file
cp .env.example .env
```

Fill in your credentials in `.env`:
```ini
GROQ_API_KEY=gsk_...
GROQ_MODEL=openai/gpt-oss-20b

# Supabase REST & Database Credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres

# Twilio & ElevenLabs (Optional for local CLI simulation, required for phone calls)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
ELEVENLABS_API_KEY=...

# Security & Notifications
API_KEY=your-internal-secret-api-key
OWNER_EMAIL=management@sinabernini.it
OWNER_PHONE=+393351234567
```

### 2. Install Dependencies
```bash
uv sync
```

---

## 📞 Running the Application

### Option A: Interactive Phone Call Simulator (Terminal)
Simulate an incoming hotel phone call directly from your terminal:
```bash
uv run python main.py
```
**In-Call Commands:**
- `/prenotazioni`: View reservations confirmed for today
- `/notifiche`: View real-time alerts in the CRM
- `/chiudi`: Hang up the phone manually
- `/reset`: Start a fresh call
- `/esci`: Exit simulator

### Option B: FastAPI Server (Telephony & REST API)
Start the REST API for Twilio voice webhooks, CRM dashboards, and chat:
```bash
uv run python main.py --serve
```
Interactive API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

**Key Endpoints:**
- `GET /health`: Healthcheck endpoint
- `POST /api/twilio/incoming-call`: TwiML webhook initiating bi-directional media stream
- `WEBSOCKET /api/twilio/stream`: Full-duplex audio stream (Twilio ↔ ElevenLabs ↔ VoiceAgent)
- `POST /api/chat`: Multi-turn conversational endpoint using native `VoiceAgent`
- `GET /api/reservations`: List reservations (protected by API key)
- `GET /api/crm/guests`: Guest 360 CRM profiles and preferences (protected by API key)
- `GET /api/room-bookings`: Hotel room bookings list (protected by API key)

---

## 🧪 Testing & Code Quality

### Unit & Integration Tests (113 passing tests)
Run unit and integration tests (eval tests are excluded by default):
```bash
uv run pytest
```

### LLM Evaluation Tests (7 passing scenarios)
Run live multi-turn conversational evaluations against Groq with native tool-calling:
```bash
uv run pytest tests/evals -m eval
```
**Scenarios Evaluated:**
- **Happy path**: Availability check → booking creation → confirmation code read-back.
- **Full slot curveball**: Fully booked slot → assistant offers available alternatives without hallucinating.
- **Modify with verification**: Caller phone mismatch rejects modification → valid phone updates booking.
- **Cancel flow**: Verified cancellation updates booking status to `CANCELLED` in repository.
- **Dietary notes**: Allergy request records note, generates immediate CRM `ALLERGY_ALERT`, and states safety disclaimer.
- **Unknown question refusal**: Unsupported amenities (e.g. heated rooftop Olympic pool) are declined without hallucination.
- **Escalation**: Large group (> 10) / human manager requests trigger `leave_message_for_owner` and log an owner notification.

### Linting & Formatting
```bash
uv run ruff check .
uv run ruff format --check .
```

---

## 📞 Real-Time Voice Pipeline (Twilio Media Streams + ElevenLabs)

```mermaid
sequenceDiagram
    autonumber
    actor Caller as 📞 Caller (Guest)
    participant Twilio as 🌐 Twilio Voice
    participant WS as ⚡ FastAPI (/api/twilio/stream)
    participant VAD as 🎙️ Two-Tier VAD (RMS + WebRTC)
    participant STT as 📝 Speech-to-Text (Groq Whisper / ElevenLabs)
    participant Agent as 🧠 VoiceAgent (Native Tool Loop)
    participant TTS as 🗣️ ElevenLabs TTS (8kHz µ-law)
    participant Comm as 📩 SMS & Email Services

    Caller->>Twilio: Inbound call to hotel number
    Twilio->>WS: POST /api/twilio/incoming-call
    WS-->>Twilio: TwiML <Connect><Stream url="wss://.../api/twilio/stream"/>
    Twilio->>WS: WebSocket Connect + start (caller phone)
    WS->>TTS: Initial Italian welcome greeting
    TTS-->>Twilio: Stream 8kHz µ-law audio chunks
    Twilio-->>Caller: Speaks warm luxury welcome
    
    Caller->>Twilio: "Vorrei prenotare una Deluxe dal 25 al 28 ottobre..."
    Twilio->>WS: 8kHz µ-law audio chunks (20ms)
    WS->>VAD: Filter noise & detect human vocal speech
    VAD-->>WS: Speech turn completed (after silence timeout)
    WS->>STT: Transcribe speech in Italian
    STT-->>WS: Final text transcript
    WS->>Agent: Run VoiceAgent turn with transcript & CallSession
    Agent->>Agent: Execute native tools (availability, booking, CRM)
    Agent-->>WS: Confirmation & reference code (SINA-XXXX)
    
    par Spoken Response
        WS->>TTS: Stream response text to 8kHz µ-law
        TTS-->>Twilio: Stream audio to caller
    and Automatic Confirmations
        Agent->>Comm: Send SMS to mobile + Email confirmation
    end
```

---

## 📂 Project Layout

```text
├── .github/
│   └── workflows/ci.yml       # GitHub Actions CI workflow (lint, format, test)
├── .pre-commit-config.yaml    # Pre-commit git hooks
├── AGENTS.md                  # Project constitution & specifications
├── IMPLEMENTATION_PLAN.md     # Production roadmap & status tracker
├── main.py                    # Application CLI / Server entrypoint
├── pyproject.toml             # uv dependencies, pytest, and ruff config
├── README.md                  # Project documentation
├── .env.example               # Environment variables template
├── supabase/
│   ├── schema.sql             # SQL schema for hotel rooms & CRM tables
│   └── migrations/            # Incremental SQL migrations
├── src/
│   ├── config.py              # Pydantic Settings configuration
│   ├── models/                # Pydantic Domain Schemas (hotel rooms, CRM, bookings)
│   ├── repositories/          # Supabase & In-Memory repository adapters
│   │   ├── base.py            # Abstract repository interfaces
│   │   ├── memory_repo.py     # Fast in-memory stores for tests
│   │   ├── supabase_hotel_room_repo.py
│   │   ├── supabase_guest_crm_repo.py
│   │   └── supabase_repo.py
│   ├── services/              # Deterministic business logic
│   │   ├── hotel_booking_service.py
│   │   ├── guest_crm_service.py
│   │   ├── booking_service.py
│   │   ├── availability_service.py
│   │   ├── restaurant_service.py
│   │   └── notification_service.py
│   ├── tools/                 # Tool classes wrapping business services
│   ├── voice/                 # Core voice & agent layer
│   │   ├── agent.py           # Native single-loop VoiceAgent (Groq function calling)
│   │   ├── pipeline.py        # TwilioMediaStreamPipeline (audio streaming, barge-in)
│   │   ├── vad.py             # Two-tier WebRTC Voice Activity Detection & RMS pre-filter
│   │   ├── session.py         # CallSession & SessionStore (identity injection)
│   │   ├── tools.py           # Native tool JSON schemas & guardrail dispatcher
│   │   ├── stt.py             # Speech-to-Text service (Groq Whisper / ElevenLabs)
│   │   ├── tts.py             # ElevenLabs streaming TTS service (8kHz mu-law)
│   │   └── audio_utils.py     # Audio format conversions (mu-law, PCM, RMS)
│   ├── agent/
│   │   └── prompts.py         # Dynamic Italian system prompts (hotel & restaurant)
│   └── api/                   # FastAPI routes & middleware
│       ├── main.py            # FastAPI app & lifespan pre-cached services
│       ├── middleware/auth.py # API key authentication
│       └── routes/            # Twilio, Chat, CRM, Room Bookings, Reservations
└── tests/
    ├── conftest.py            # Test fixtures and mock repositories
    ├── unit/                  # Deterministic service, tool, and VAD tests
    ├── agent/                 # VoiceAgent conversation turn & flow tests
    ├── integration/           # FastAPI HTTP endpoint tests
    └── evals/                 # Live Groq LLM evaluation scenarios (pytest.mark.eval)
```
