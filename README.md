# SINA HOTELS — AI Voice Receptionist & Room CRM

An Italian-first AI hotel voice receptionist and guest CRM built with a **native tool-calling VoiceAgent**, **Groq**, **Twilio Voice**, **ElevenLabs**, and **PostgreSQL/Supabase** for **Sina Bernini Bristol (Roma)**.

The agent handles hotel phone calls: checks real-time room availability across 4 room categories (Superior, Deluxe, Junior Suite, Suite Panoramica), creates and modifies room bookings, tracks early departures, captures guest CRM preferences (allergies, special habits, VIP status), and runs a full-duplex telephony stream with VAD and instant barge-in.

---

## 🏛️ Architecture & Session State

The system separates **in-memory conversational session state** from **long-term enterprise persistence**:

```mermaid
flowchart TD
    Caller[Caller / Phone / Terminal Simulator] -->|8kHz Audio or Text| Pipeline[FastAPI / TwilioMediaStreamPipeline / CLI]
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
        SupabaseDB --> RoomBookings[room_bookings]
        SupabaseDB --> GuestsTable[guests]
        SupabaseDB --> NotifTable[crm_notifications]
    end
```

---

## ⚡ Native Tool Calling (No LangGraph Overhead)

The agent uses a **single conversational LLM loop** with native OpenAI/Groq function calling (`groq.AsyncGroq`):
- **Zero Framework Bloat**: No LangGraph, LangChain, or external graph routers on the critical audio path.
- **Fast Turnaround (<150ms LLM overhead)**: Single-turn generation with parallel native tool dispatch.
- **Per-Call Session**: Each call maintains a clean [`CallSession`](file:///home/magesh/Magesh/Projects/Hotel_Voice_Agent/src/voice/session.py) holding message history, booking draft fields, and verification state.
- **No Checkpointer DB Latency**: Avoids saving conversational blobs to PostgreSQL on every speech turn.

---

## 🛡️ Security & Business Guardrails

1. **Deterministic Identity Injection**: The caller's phone number (`caller_phone`) and `user_id` are injected by our code from the Twilio telephony handshake or session context. They are **never LLM-fillable arguments**, preventing spoofing or unauthorized access to other guests' profiles.
2. **Date Validation**: Check-in dates must be today or in the future; check-out must be strictly after check-in; stays are limited to 30 consecutive nights. Invalid temporal requests are intercepted before touching booking services.
3. **Read-Back Confirmation**: Before room reservations are confirmed in the system, the assistant must read back the dates, category, and total pricing to obtain explicit guest agreement.
4. **Identity Verification Before Modifications**: Cancellation, early departures, and booking modifications strictly verify the caller's phone number against the booking record on file.
5. **Zero Hallucination Availability**: The LLM never invents rooms or prices. Real availability is calculated deterministically by [`HotelBookingService`](file:///home/magesh/Magesh/Projects/Hotel_Voice_Agent/src/services/hotel_booking_service.py).
6. **Allergen Disclaimer & Alerts**: Dietary notes and allergies trigger immediate staff alerts. Spoken disclaimer: *"Per la Sua sicurezza La preghiamo di ricordare l'allergia al personale di sala al Suo arrivo."*
7. **Direct Templated Delivery**: SMS confirmations via Twilio REST and luxury branded HTML confirmation emails via SMTP (`aiosmtplib`). No MCP on the voice call path.

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

# Supabase REST Credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres

# Twilio & ElevenLabs (Optional for local CLI simulation, required for phone calls)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
ELEVENLABS_API_KEY=...
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
- `GET /api/reservations`: List reservations
- `GET /api/crm/guests`: Guest 360 CRM profiles and preferences

---

## 🧪 Testing & Code Quality

Run the automated test suite (85 tests covering native agent flow, services, and API integration):
```bash
uv run pytest
```

Run code formatting and linting:
```bash
uv run ruff check .
```

---

## 📞 Real-Time Voice Pipeline (Twilio Media Streams + ElevenLabs)

```mermaid
sequenceDiagram
    autonumber
    actor Caller as 📞 Caller (Guest)
    participant Twilio as 🌐 Twilio Voice
    participant WS as ⚡ FastAPI (/api/twilio/stream)
    participant STT as 🎙️ Speech-to-Text (ElevenLabs/Groq)
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
    Twilio->>WS: 8kHz µ-law audio chunks
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
├── AGENTS.md                  # Project constitution & specifications
├── main.py                    # Application CLI / Server entrypoint
├── pyproject.toml             # uv dependencies, pytest, and ruff config
├── README.md                  # Project documentation
├── .env.example               # Environment variables template
├── supabase/
│   └── schema.sql             # SQL schema for hotel rooms & CRM tables
├── src/
│   ├── config.py              # Pydantic Settings configuration
│   ├── models/                # Pydantic Domain Schemas (hotel rooms, CRM, bookings)
│   ├── repositories/          # Supabase & In-Memory repository adapters
│   ├── services/              # Business logic (Hotel Booking, CRM, Notifications)
│   ├── tools/                 # Tool classes wrapping business services
│   ├── voice/                 # Core voice & agent layer
│   │   ├── agent.py           # Native single-loop VoiceAgent (Groq function calling)
│   │   ├── session.py         # CallSession & SessionStore (identity injection)
│   │   ├── tools.py           # Native tool JSON schemas & guardrail dispatcher
│   │   ├── pipeline.py        # TwilioMediaStreamPipeline (VAD, barge-in)
│   │   ├── stt.py             # Speech-to-Text service (Groq Whisper / ElevenLabs)
│   │   └── tts.py             # ElevenLabs streaming TTS service (8kHz mu-law)
│   ├── agent/
│   │   └── prompts.py         # Dynamic Italian system prompt & date formatting
│   └── api/                   # FastAPI routes (Twilio, Chat, CRM, Room Bookings)
└── tests/
    ├── conftest.py            # Test fixtures and mock repositories
    ├── unit/                  # Deterministic service & tool tests
    ├── agent/                 # VoiceAgent conversation turn & flow tests
    └── integration/           # FastAPI HTTP endpoint tests
```
