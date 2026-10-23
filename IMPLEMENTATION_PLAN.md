# 🛠️ Hotel Voice Agent — Implementation Plan

14 fixes across 3 priority tiers. Each item has the exact files to touch, what to change, and estimated effort.

---

## 🔴 P0 — Must Fix (Total: ~4 hours)

---

### Fix #1: Wire Owner Notifications to Email/SMS ✅ [COMPLETED]

**Problem:** `NotificationService` writes to the DB but never delivers anything to the owner.

**Files to modify:**
- `src/services/notification_service.py`
- `src/config.py`

**Steps:**
1. Add `OWNER_EMAIL` and `OWNER_PHONE` fields to `Settings` in `config.py`
2. Inject `EmailService` and `TwilioService` into `NotificationService.__init__`
3. Add a private `_deliver()` method that, after storing the notification in the repo, dispatches via email/SMS based on notification priority:
   - **Immediate (email + SMS):** `allergy_alert`, `owner_message`, `cancellation`
   - **Email only:** `new_booking`, `modification`, `vip_alert`
   - **Batched/skip:** `feedback`, `concierge_request`
4. Call `_deliver()` at the end of every `notify_*` method
5. Wrap delivery in try/except with `logger.warning` — never let a failed notification crash a booking

**New env vars:**
```
OWNER_EMAIL=owner@sinabernini.it
OWNER_PHONE=+39335XXXXXXX
```

**Tests to add in `tests/unit/test_notification_delivery.py`:**
- Mock `EmailService` and `TwilioService`, assert they're called with correct recipient/body for each notification type
- Assert delivery failure doesn't raise (graceful degradation)

**Effort:** ~1.5 hours

---

### Fix #2: Cache Agent Graph at App Startup

**Problem:** `create_agent_graph()` is called on every `/api/chat` POST and every Twilio WebSocket connection, creating fresh service/repo instances each time.

**Files to modify:**
- `src/api/main.py` — lifespan function
- `src/api/routes/chat.py`
- `src/api/routes/twilio_routes.py`
- `src/agent/graph.py`

**Steps:**
1. In `main.py` lifespan, call `create_agent_graph()` once and store on `app.state.agent_graph`
2. Also store shared service instances on `app.state` (needed for REST routes that query services directly)
3. In `chat.py`, replace the per-request `create_agent_graph()` call with `request.app.state.agent_graph`
4. In `twilio_routes.py`, do the same for the WebSocket handler
5. The checkpointer is already created in lifespan — pass it through to the graph

**Key consideration:** The graph itself is stateless (state lives in the checkpointer keyed by `thread_id`), so a single graph instance shared across requests is safe.

**Tests to update:**
- Integration tests in `tests/integration/` that use `TestClient` — ensure the lifespan creates the graph correctly
- Add a test that two concurrent `/api/chat` calls with different `session_id`s get isolated state

**Effort:** ~45 minutes

---

### Fix #3: Add Supabase Repos for Hotel Rooms & CRM

**Problem:** Only restaurant repos have Supabase implementations. Hotel rooms and guest CRM are in-memory only — data lost on restart.

**Files to create:**
- `src/repositories/supabase_hotel_room_repo.py` (new)
- `src/repositories/supabase_guest_crm_repo.py` (new)

**Files to modify:**
- `src/repositories/__init__.py` — add factory functions
- `src/repositories/hotel_room_repo.py` — extract abstract base if not already done
- `src/repositories/base.py` — add abstract interfaces for hotel room & CRM repos if missing

**Steps:**
1. Define abstract base classes in `base.py` (if not already there):
   - `HotelRoomRepository`: `get_rooms()`, `get_room()`, `update_room()`, `get_bookings()`, `get_booking()`, `save_booking()`, `update_booking()`
   - `GuestCRMRepository`: `get_guest_by_phone()`, `get_guest()`, `save_guest()`, `update_guest()`, `save_preference()`, `save_concierge_request()`, `save_feedback()`
2. Create `supabase_hotel_room_repo.py` implementing against Supabase tables: `hotel_rooms`, `hotel_bookings`
3. Create `supabase_guest_crm_repo.py` implementing against: `guests`, `guest_preferences`, `concierge_requests`, `guest_feedback`
4. Add factory functions `get_hotel_room_repository()` and `get_guest_crm_repository()` that try Supabase first, fall back to in-memory (same pattern as existing `get_repository()`)
5. Create the corresponding Supabase tables (provide SQL migration script)

**Supabase migration to create (`supabase/migrations/002_hotel_crm.sql`):**
```sql
-- Hotel rooms table
CREATE TABLE hotel_rooms (
    id TEXT PRIMARY KEY,
    hotel_id TEXT NOT NULL,
    room_number TEXT NOT NULL,
    category TEXT NOT NULL,
    floor INTEGER,
    is_available BOOLEAN DEFAULT true,
    current_booking_id TEXT
);

-- Hotel bookings table  
CREATE TABLE hotel_bookings (
    id TEXT PRIMARY KEY,
    hotel_id TEXT NOT NULL,
    reference_code TEXT UNIQUE NOT NULL,
    room_id TEXT REFERENCES hotel_rooms(id),
    guest_name TEXT NOT NULL,
    guest_phone TEXT,
    guest_email TEXT,
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    category TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'confirmed',
    total_price NUMERIC(10,2),
    special_requests TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Guests table
CREATE TABLE guests (
    id TEXT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    email TEXT,
    vip_tier TEXT DEFAULT 'standard',
    gender TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Guest preferences
CREATE TABLE guest_preferences (
    id TEXT PRIMARY KEY,
    guest_id TEXT REFERENCES guests(id),
    category TEXT NOT NULL,
    value TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

**Tests:**
- Unit tests with mocked Supabase client (same pattern as existing `supabase_repo.py` tests if any)
- Integration test: write a booking via Supabase repo, read it back, verify fields

**Effort:** ~2 hours

---

## 🟡 P1 — Pre-Production (Total: ~4 hours)

---

### Fix #4: Add API Authentication

**Files to create:**
- `src/api/middleware/auth.py` (new)

**Files to modify:**
- `src/api/main.py`
- `src/config.py`
- All route files in `src/api/routes/`

**Steps:**
1. Add `API_KEY` to `Settings` in `config.py`
2. Create a FastAPI `Depends` function in `auth.py` that checks `X-API-Key` header or `Authorization: Bearer` against `settings.API_KEY`
3. Apply the dependency to **internal routes** (CRM, reservations list, room bookings CRUD, outbound calls)
4. Leave `/api/chat` and `/api/twilio/*` unauthenticated (they're caller-facing / webhook endpoints)
5. For Twilio webhooks, add Twilio request signature validation using `twilio.request_validator`

**Effort:** ~1 hour

---

### Fix #5: Lock Down CORS

**File to modify:**
- `src/api/main.py`
- `src/config.py`

**Steps:**
1. Add `CORS_ORIGINS` (comma-separated string) to `Settings`, default `"http://localhost:3000"`
2. Parse into list and pass to `CORSMiddleware(allow_origins=settings.cors_origins_list)`
3. Remove `allow_credentials=True` unless you actually need cookie-based auth

**Effort:** ~15 minutes

---

### Fix #6: Fix Hotel Booking Reference Code Collisions

**File to modify:**
- `src/services/hotel_booking_service.py`

**Steps:**
1. Copy the `generate_reference_code()` loop pattern from `src/services/booking_service.py`
2. Or switch to `f"SINA-{uuid4().hex[:8].upper()}"` for near-zero collision probability
3. Add a uniqueness check against existing bookings before returning

**Effort:** ~15 minutes

---

### Fix #7: Stop Swallowing Exceptions Silently

**Files to modify:**
- `src/services/hotel_booking_service.py` — SMS/email `except Exception: pass`
- `src/repositories/supabase_repo.py` — generic `except Exception`
- `src/tools/hotel_room_tools.py` — unguarded `date.fromisoformat()`

**Steps:**
1. Add `import logging` and `logger = logging.getLogger(__name__)` to each file
2. Replace every `except Exception: pass` with `except Exception: logger.exception("Failed to ...")`
3. In `hotel_room_tools.py`, wrap `date.fromisoformat()` and `RoomCategory()` calls in try/except returning a user-friendly Italian error string (e.g., `"Formato data non valido. Utilizzare YYYY-MM-DD."`)
4. In `supabase_repo.py`, log the specific operation that failed before falling back

**Effort:** ~30 minutes

---

### Fix #8: Fix Gender Detection

**Files to modify:**
- `src/models/crm.py` — add field
- `src/services/guest_crm_service.py` — use field

**Steps:**
1. Add `title: str | None = None` field to `GuestProfile` (values: `"Signor"`, `"Signora"`, `None`)
2. In `guest_crm_service.py`, replace the hardcoded name list with: `title = guest.title or guest.first_name` — just use the first name without gendered prefix if title is unknown
3. Update sample data in `src/repositories/sample_data.py` to include `title` for existing guests
4. Optionally: add a CRM tool that lets the agent set the guest's preferred title during conversation

**Effort:** ~30 minutes

---

## 🟢 P2 — Quality & Polish (Total: ~5 hours)

---

### Fix #9: Add CI/CD + Ruff + Pre-commit

**Files to create:**
- `.github/workflows/ci.yml` (new)
- `.pre-commit-config.yaml` (new)

**Files to modify:**
- `pyproject.toml` — add `[tool.ruff]` section

**Steps:**
1. Add Ruff config to `pyproject.toml`:
   ```toml
   [tool.ruff]
   target-version = "py312"
   line-length = 100
   
   [tool.ruff.lint]
   select = ["E", "F", "W", "I", "UP", "B", "SIM"]
   ```
2. Create `.pre-commit-config.yaml` with ruff (lint + format) and ty hooks
3. Create `.github/workflows/ci.yml`:
   - Trigger on push/PR to main
   - Steps: checkout → setup Python 3.12 → `uv sync` → `ruff check` → `ruff format --check` → `pytest tests/unit tests/integration`
4. Run `ruff check --fix .` once to clean up existing code

**Effort:** ~1 hour

---

### Fix #10: Fix Config Mismatch

**Files to modify:**
- `src/config.py`
- `.env.example`

**Steps:**
1. Decide on the default model — likely `"llama-3.3-70b-versatile"` since that's Groq's best
2. Update `config.py` default to match
3. Ensure `.env.example` matches

**Effort:** ~5 minutes

---

### Fix #11: Deduplicate Room Rates (Prompt ↔ Model)

**Files to modify:**
- `src/agent/prompts.py`
- `src/models/hotel_booking.py`

**Steps:**
1. In `prompts.py`, create a helper function `_build_room_rates_section()` that reads from `ROOM_CATEGORY_DETAILS` and formats the Italian text
2. Inject the generated text into the system prompt template via string formatting
3. Single source of truth: only `hotel_booking.py` defines rates

**Effort:** ~30 minutes

---

### Fix #12: Add LLM Eval Tests

**Files to create:**
- `tests/evals/__init__.py` (new)
- `tests/evals/test_booking_scenarios.py` (new)
- `tests/evals/conftest.py` (new)

**Steps:**
1. Create a `conftest.py` that builds the real agent graph with a real Groq LLM (requires `GROQ_API_KEY`)
2. Mark all eval tests with `@pytest.mark.eval` so they're excluded from CI by default
3. Write scenario tests (multi-turn conversations):
   - **Happy path:** Check availability → book → confirm → verify reference code returned
   - **Full slot:** Request fully booked time → agent offers alternatives
   - **Modify with verification:** Create booking → modify with wrong phone → fails → correct phone → succeeds
   - **Cancel flow:** Create → cancel with verification → confirmed
   - **Dietary notes:** Book with "allergia al glutine" → verify allergy alert created
   - **Unknown question:** Ask about something not in FAQ → agent says it doesn't know
   - **Escalation:** Ask for human → agent offers to take message
4. Assert on tool calls made (not just text output) — e.g., the agent must have called `check_availability` before `create_booking`
5. Add `pytest.ini` marker:
   ```ini
   markers = eval: LLM evaluation tests (require GROQ_API_KEY)
   ```

**Effort:** ~2 hours

---

### Fix #13: Upgrade VAD

**Files to modify:**
- `src/voice/pipeline.py`
- `pyproject.toml` — add dependency

**Steps:**
1. Add `silero-vad` or `webrtcvad` to dependencies
2. Create a `src/voice/vad.py` module wrapping the chosen library
3. In `pipeline.py`, replace the RMS threshold check with the proper VAD model
4. Keep the RMS check as a fast pre-filter: if RMS < threshold, skip VAD entirely (saves compute)
5. Make VAD provider configurable in `config.py` (`VAD_PROVIDER: rms | silero | webrtc`)

**Effort:** ~1 hour

---

### Fix #14: Update AGENTS.md

**File to modify:**
- `AGENTS.md`

**Steps:**
1. Update the goal to reflect the hotel concierge scope (not just restaurant bookings)
2. Update MVP capabilities to include hotel room bookings, CRM, concierge services
3. Update the suggested structure to match the actual directory layout (add `voice/`, remove items that don't exist)
4. Add the hotel-specific reservation rules (room categories, early departure policy, etc.)
5. Keep the restaurant booking section but mark it as "legacy/secondary"

**Effort:** ~30 minutes

---

## Execution Roadmap

| Sprint | Focus | Fixes | Time |
|--------|-------|-------|------|
| **Week 1** | Functional Gaps | #2 → #1 → #6 → #7 → #8 | ~3.5h |
| **Week 2** | Security + Persistence | #5 → #4 → #3 → #10 | ~3.5h |
| **Week 3** | Quality & Polish | #9 → #11 → #12 → #13 → #14 | ~5h |

> **Total estimated effort: ~13 hours across 3 weeks.**  
> Week 1 fixes functional bugs in shipping code. Week 2 makes it production-safe. Week 3 adds long-term quality.
