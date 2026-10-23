# SINA HOTELS — AI Voice Receptionist & Room CRM

An Italian-first AI hotel voice receptionist and guest CRM built with **LangGraph**, **Groq**, **React + Vite**, and **PostgreSQL/Supabase** for **Sina Bernini Bristol (Roma)**.

The agent handles hotel phone calls: checks real-time room availability across 4 room categories (Superior, Deluxe, Junior Suite, Suite Panoramica), creates and modifies room bookings, tracks early departures, captures guest CRM preferences (allergies, special habits, VIP status), and presents a live React management dashboard.

---

## 🏛️ Architecture & Memory Management

The system separates **short-term conversational state** from **long-term enterprise persistence**:

```mermaid
flowchart TD
    Caller[Caller / Terminal Simulator / VoIP Webhook] -->|Italian speech or text| API[FastAPI / CLI Simulator]
    API --> Agent[LangGraph Conversation Agent]
    Agent --> Prompts[English System Prompt / Italian Tone 'dare del Lei']
    Agent --> Tools[Typed LangChain Tools]
    Tools --> Services[Deterministic Business Rules]

    subgraph "Short-Term Conversational Memory (Supabase Checkpointer)"
        Agent --> Checkpointer[AsyncPostgresSaver / MemorySaver]
        Checkpointer --> Checkpoints[(checkpoints & blobs)]
    end

    subgraph "Long-Term Enterprise Memory (Supabase CRM)"
        Services --> Repositories[Repository Layer]
        Repositories --> SupabaseDB[(Supabase PostgreSQL)]
        SupabaseDB --> ResTable[reservations]
        SupabaseDB --> TableTable[tables]
        SupabaseDB --> NotifTable[crm_notifications]
        SupabaseDB --> FAQTable[faqs]
        SupabaseDB --> RestTable[restaurants]
    end
```

---

## 📊 Supabase Database Schema (9 Tables)

The database schema is organized into two distinct sets of tables:

### 1. LangGraph Checkpoint Tables (Conversational State)
Managed automatically by [`AsyncPostgresSaver`](file:///home/magesh/Magesh/Projects/Hotel_Voice_Agent/src/agent/checkpointer.py):
- **`checkpoints`**: Stores state snapshots at every dialogue turn and tool invocation.
- **`checkpoint_blobs`**: Stores the binary serialized message history, caller ID, and parameters.
- **`checkpoint_writes`**: Append-only log of intermediate writes for rollback and crash recovery.
- **`checkpoint_migrations`**: Tracks internal checkpointer library schema versions.

### 2. Business & CRM Tables (Permanent Enterprise Truth)
Defined in [`supabase/schema.sql`](file:///home/magesh/Magesh/Projects/Hotel_Voice_Agent/supabase/schema.sql):
- **`restaurants`**: Operating hours, shifts (lunch/dinner), timezone (`Europe/Rome`), and booking limits.
- **`tables`**: Physical dining room tables with capacities (`min_capacity`, `max_capacity`).
- **`reservations`**: Confirmed customer reservations with human-friendly reference codes (`BV-XXXX`), cover count, time slot, and guest notes.
- **`crm_notifications`**: Actionable alerts for restaurant staff (`new_booking`, `cancellation`, `allergy_alert`, `owner_message`).
- **`faqs`**: Official restaurant answers (parking garage partnership, dress code, pet policy, location, gluten-free safety).

---

## 🎯 Golden Business Rules (Deterministic Core)

1. **Zero Hallucination Availability**: The LLM never invents tables or open slots. Real availability is calculated by [`AvailabilityService`](file:///home/magesh/Magesh/Projects/Hotel_Voice_Agent/src/services/availability_service.py) based on active shifts and existing reservations.
2. **Deterministic Alternatives**: If a requested time is fully booked (e.g. 20:00), the system dynamically calculates and presents open alternative times (e.g. 19:30 or 21:30).
3. **Allergen Disclaimer & Alerts**: Dietary notes are recorded into the booking and trigger an immediate high-priority `ALLERGY_ALERT` in `crm_notifications`. The agent reminds the caller: *"Per la Sua sicurezza La preghiamo di ricordare l'allergia al personale di sala al Suo arrivo."*
4. **Caller Verification**: Modifications and cancellations require verifying the caller's phone number along with their booking reference code or surname.
5. **Polite Italian Hospitality Dialogue**: Prompts instruct the model to speak concise, warm Italian using formal address (*"dare del Lei"*).
6. **Smooth Call Wrap-Up**: After completing a task, the agent asks: *"Posso aiutarLa con qualcos'altro o è a posto così?"*. If the caller indicates they are done (*"No grazie"*, *"A posto così"*), the agent delivers a warm farewell and executes the `end_call` tool to hang up.

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

# Supabase PostgreSQL URI (for LangGraph AsyncPostgresSaver Checkpointer)
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

> [!TIP]
> **Password URL Encoding**: If your database password contains special characters like `@`, percent-encode it as `%40` (e.g. `Hotel@123` becomes `Hotel%40123`). The application also includes automatic URL password normalization.

### 2. (Optional) Seed Business Tables in Supabase
Run [`supabase/schema.sql`](file:///home/magesh/Magesh/Projects/Hotel_Voice_Agent/supabase/schema.sql) in your **Supabase Dashboard → SQL Editor** to initialize the master hotel rooms, room bookings, and guest CRM tables for *Sina Bernini Bristol*.

---

## 📞 Running the Application

### Option A: Interactive Phone Call Simulator (Terminal)
Simulate an incoming telephone call directly from your terminal:
```bash
uv run python main.py
```
**In-Call Commands:**
- `/prenotazioni`: View reservations confirmed for today
- `/notifiche`: View real-time alerts in the CRM
- `/chiudi`: Hang up the phone manually
- `/reset`: Start a fresh call
- `/esci`: Exit simulator

### Option B: FastAPI Server (Production REST API & Webhooks)
Start the REST API for CRM dashboards, frontends, or telephony gateways (Twilio, LiveKit, Vapi):
```bash
uv run python main.py --serve
```
Interactive API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

**Key Endpoints:**
- `GET /health`: Healthcheck endpoint
- `GET /api/availability?booking_date=YYYY-MM-DD&booking_time=HH:MM&party_size=N`: Real-time availability check
- `GET /api/reservations?booking_date=YYYY-MM-DD`: List daily reservations
- `GET /api/notifications`: List unread CRM alerts
- `POST /api/notifications/{id}/read`: Mark notification as read
- `POST /api/chat`: Multi-turn conversational endpoint with Supabase checkpointing

---

## 🧪 Testing & Code Quality

Run the automated test suite (unit tests, multi-turn LangGraph evals, and API integration tests):
```bash
uv run pytest
```

Run code formatting and linting:
```bash
uv run ruff check .
uv run ruff format --check .
```

---

## 📞 Real-Time Voice Pipeline (Twilio Media Streams + ElevenLabs)

The system supports live telephone calls using **Twilio Media Streams** with bidirectional WebSockets, **ElevenLabs** for expressive Italian TTS/STT, and deterministic **LangGraph** orchestration:

```mermaid
sequenceDiagram
    autonumber
    actor Caller as 📞 Caller (Guest)
    participant Twilio as 🌐 Twilio Voice
    participant WS as ⚡ FastAPI (/api/twilio/stream)
    participant STT as 🎙️ Speech-to-Text (ElevenLabs/Groq)
    participant Agent as 🧠 LangGraph Agent
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
    WS->>Agent: Run StateGraph with transcript & caller phone
    Agent->>Agent: Execute tools (availability, room booking, CRM)
    Agent-->>WS: Confirmation & reference code (SINA-XXXX)
    
    par Spoken Response
        WS->>TTS: Stream response text to 8kHz µ-law
        TTS-->>Twilio: Stream audio to caller
    and Automatic Confirmations
        Agent->>Comm: Send SMS to mobile + Email confirmation
    end
```

### Key Voice Features:
- **Twilio Media Streams**: Raw 8kHz $\mu$-law audio streaming over WebSocket with zero transcoding.
- **Barge-in Support**: Voice Activity Detection (VAD) detects caller interruptions and dispatches a Twilio `clear` control frame to instantly silence ongoing bot speech.
- **ElevenLabs Italian Voice**: Ultra-natural luxury Italian tone ("dare del Lei").
- **Automated Multi-Channel Confirmations**:
  - `send_booking_confirmation_sms`: Dispatches booking reference (e.g. `SINA-4020`), dates, and room category to the caller's mobile via Twilio REST.
  - `send_booking_confirmation_email`: Sends a luxury branded HTML confirmation email with check-in/out guidelines and hotel policies.

---

## 📂 Project Layout

```text
├── AGENTS.md                  # Project constitution & specifications
├── main.py                    # Application CLI / Server entrypoint
├── pyproject.toml             # uv dependencies, pytest, and ruff config
├── README.md                  # Project documentation
├── .env.example               # Environment variables template
├── supabase/
│   └── schema.sql             # SQL schema for business tables & initial seed
├── src/
│   ├── config.py              # Pydantic Settings configuration
│   ├── models/                # Pydantic Domain Schemas (booking, restaurant, notification)
│   ├── repositories/          # Supabase & In-Memory repository adapters
│   ├── services/              # Deterministic business logic (Availability, Booking, FAQ, Notifications)
│   ├── tools/                 # LangChain typed tools for LangGraph
│   ├── agent/                 # LangGraph state machine, prompts, and checkpointer
│   │   ├── checkpointer.py    # AsyncPostgresSaver & MemorySaver factory
│   │   ├── graph.py           # StateGraph definition and compilation
│   │   ├── prompts.py         # English system prompt & Italian dialogue rules
│   │   └── state.py           # AgentState definition with message reducer
│   ├── api/                   # FastAPI routes (reservations, chat, health)
│   └── cli.py                 # Interactive terminal phone call simulator
└── tests/
    ├── conftest.py            # Test fixtures and mock repositories
    ├── unit/                  # Deterministic service tests (availability, conflicts, shifts)
    ├── agent/                 # LangGraph multi-turn conversation tests (curveballs, end_call)
    └── integration/           # FastAPI HTTP endpoint tests
```
