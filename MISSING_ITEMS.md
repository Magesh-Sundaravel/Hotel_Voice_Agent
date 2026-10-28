# 📋 Project Gaps & Missing Items Audit

This document outlines all identified bugs, missing features, evaluation gaps, architectural inconsistencies, and production readiness requirements for the **Sina Hotels AI Voice Receptionist & CRM** project.

---

## 📑 Table of Contents
1. [Active Test Failures & Logic Bugs (P0)](#1-active-test-failures--logic-bugs-p0)
2. [Primary Hotel Scope Missing from LLM Evals (P1)](#2-primary-hotel-scope-missing-from-llm-evals-p1)
3. [Voice Telephony Inbound Caller Personalization (P1)](#3-voice-telephony-inbound-caller-personalization-p1)
4. [Frontend & Security Integration Gaps (P1)](#4-frontend--security-integration-gaps-p1)
5. [Database Schema & Migration Inconsistencies (P2)](#5-database-schema--migration-inconsistencies-p2)
6. [Configuration & Outdated References (P2)](#6-configuration--outdated-references-p2)
7. [DevOps & Production Deployment Scaffolding (P2)](#7-devops--production-deployment-scaffolding-p2)
8. [Actionable Implementation Checklist](#8-actionable-implementation-checklist)

---

## 1. Active Test Failures & Logic Bugs (P0)

### 1.1 ElevenLabs Mock TTS Assertion Failure
- **File:** `tests/unit/test_voice_audio.py` (lines 48–56) & `src/voice/tts.py` (line 21)
- **Problem:** `test_elevenlabs_mock_tts` fails with HTTP 401 Unauthorized (`assert 0 >= 3`).
- **Root Cause:**
  ```python
  # src/voice/tts.py:21
  self.api_key = api_key or settings.ELEVENLABS_API_KEY
  ```
  When the test passes `api_key=""`, Python treats `""` as falsy and falls back to `settings.ELEVENLABS_API_KEY` from `.env`, sending a real request with an invalid placeholder key rather than falling back to mock audio generator.
- **Resolution:**
  ```python
  self.api_key = api_key if api_key is not None else settings.ELEVENLABS_API_KEY
  ```

### 1.2 Supabase Restaurant Empty-Data Fallback Failure
- **File:** `src/repositories/supabase_repo.py` (lines 72–105) & `tests/integration/test_api.py`
- **Problem:** `test_availability_endpoint` and `test_reservations_and_notifications_endpoints` fail when `.env` contains Supabase credentials because availability returns `False` (*"Non disponiamo di tavoli per 2 persone"*).
- **Root Cause:** In `SupabaseRestaurantRepository.get_tables()` and `get_faqs()`, executing a query against an unseeded or clean Supabase table returns `res.data = []`. Unlike `get_settings()` and `SupabaseHotelRoomRepository`, the methods do not check `if not res.data:`, returning 0 tables instead of falling back to sample in-memory seed tables.
- **Resolution:**
  ```python
  if not res.data:
      return await _fallback_restaurant_repo.get_tables(restaurant_id)
  ```

---

## 2. Primary Hotel Scope Missing from LLM Evals (P1)

- **Files:** `tests/evals/test_booking_scenarios.py` & `tests/evals/conftest.py`
- **Problem:** The live LLM evaluation suite (`pytest -m eval`) **only evaluates legacy restaurant table bookings** (*"Trattoria Bella Vista"*, `BV-XXXX`, `check_table_availability`, `create_reservation`).
- **Missing Coverage:** The primary hotel reception and concierge capabilities defined in `AGENTS.md` have **zero live LLM evaluation tests**:
  1. Room availability queries across the 4 luxury tiers (*Superior €250*, *Deluxe €350*, *Junior Suite €480*, *Suite Panoramica Barberini €750*).
  2. Multi-turn booking flow with required read-back confirmation and reference code generation (`SINA-XXXX`).
  3. Booking modifications and cancellation with identity verification (`caller_phone` matching reservation).
  4. Early departure reporting (`report_early_departure`): recalculating room nights/billing, releasing room inventory, and triggering housekeeping alerts.
  5. Guest 360 CRM recognition: VIP tier recognition (Standard, Silver, Gold, Platinum, VIP) and persistent dietary/allergy alerts.
  6. Official hotel service FAQs: check-in (15:00), check-out (12:00), gourmet breakfast, Rooftop "The Flair", spa appointments, and private valet parking.

---

## 3. Voice Telephony Inbound Caller Personalization (P1)

- **File:** `src/voice/pipeline.py` (lines 117–121)
- **Problem:** When an inbound call starts on Twilio Media Streams (`event == "start"`), the pipeline greets the caller with a static generic message:
  ```python
  greeting = (
      "Buongiorno, sono l'assistente virtuale di Sina Bernini Bristol. "
      "Come posso aiutarLa oggi?"
  )
  self._start_tts_task(greeting)
  ```
- **Missing:**
  - The pipeline does not consult `guest_crm_service.get_guest_context(self.caller_phone)` upon call connection.
  - Recognized in-house guests (e.g. *"Bentornato Signor Rossi, come sta trascorrendo il Suo soggiorno nella camera 402?"*) or VIP members are never greeted by name or stay stage on call pickup.

---

## 4. Frontend & Security Integration Gaps (P1)

### 4.1 Missing API Key Authentication in Frontend Requests
- **File:** `frontend/src/App.jsx` (lines 66–71, 96–100, 113–117, 130–132)
- **Problem:** All internal backend routes (`/api/rooms`, `/api/room-bookings`, `/api/hotel-stats`, `/api/notifications`, `/api/crm/*`) enforce API key protection via `verify_api_key`. However, the React frontend issues raw `fetch()` calls without providing `X-API-Key` or `Authorization: Bearer <key>`.
- **Impact:** As soon as `API_KEY` is configured in production, the entire PMS dashboard fails with `401 Unauthorized`.

### 4.2 Polling Instead of Real-Time Streams
- **File:** `frontend/src/App.jsx` (line 89)
- **Problem:** Real-time synchronization is simulated using `setInterval(fetchData, 6000)` (HTTP polling every 6 seconds).
- **Missing:** Native Supabase Realtime subscriptions or a backend Server-Sent Events (SSE) / WebSocket endpoint for instant room status and notification dispatch.

### 4.3 Missing In-Browser WebRTC/Audio Tester
- **Problem:** The web UI only manages PMS records. There is no web-based audio interface to test the voice agent directly from the browser (developers must rely on real Twilio phone calls or the CLI text simulator).

---

## 5. Database Schema & Migration Inconsistencies (P2)

### 5.1 Omission of Restaurant Tables in Master SQL Schema
- **File:** `supabase/schema.sql`
- **Problem:** The master schema initializes hotel rooms, room bookings, CRM guests, and notifications, but **completely omits the restaurant tables** (`restaurants`, `tables`, `faqs`, `reservations`).
- **Impact:** Running `supabase/schema.sql` on a fresh Supabase instance breaks `SupabaseRestaurantRepository` and `SupabaseBookingRepository` unless they fall back to in-memory mode.

### 5.2 Missing Baseline Migration
- **Directory:** `supabase/migrations/`
- **Problem:** Only `002_hotel_crm.sql` exists; `001_initial_schema.sql` is missing.

### 5.3 Missing Row Level Security (RLS) Policies
- **Problem:** `supabase/schema.sql` does not enable or define RLS policies or PostgreSQL roles for production database security.

---

## 6. Configuration & Outdated References (P2)

### 6.1 Invalid Groq Default Model
- **Files:** `src/config.py` (line 14), `.env.example` (line 3), `README.md` (line 97)
- **Problem:** Default model is set to `openai/gpt-oss-20b`, which is not a valid Groq production model.
- **Resolution:** Change default to `llama-3.3-70b-versatile` across `config.py`, `.env.example`, and documentation.

### 6.2 Obsolete LangGraph References
- **File:** `.env.example` (lines 8–10)
- **Problem:** Comments still mention *"Postgres URI for LangGraph PostgresSaver checkpointer"*, even though LangGraph was eliminated in favor of the native single-loop `VoiceAgent`.

---

## 7. DevOps & Production Deployment Scaffolding (P2)

- **Missing Containerization:** No `Dockerfile` (multi-stage build for React frontend + FastAPI backend) or `docker-compose.yml`.
- **Missing Process Management:** No production ASGI server configuration (e.g. Gunicorn + Uvicorn workers).
- **Missing Deep Health Checks:** `/health` only returns static strings; it does not verify connectivity to external services (Twilio, ElevenLabs, Groq, Supabase).

---

## 8. Actionable Implementation Checklist

| Priority | Task | Target Files |
| :---: | :--- | :--- |
| 🔴 **P0** | Fix falsy `api_key=""` check in `ElevenLabsTTSService` | `src/voice/tts.py` |
| 🔴 **P0** | Add empty-data fallback in `SupabaseRestaurantRepository` | `src/repositories/supabase_repo.py` |
| 🟡 **P1** | Add Hotel Room & CRM eval scenarios to test suite | `tests/evals/test_booking_scenarios.py`, `tests/evals/conftest.py` |
| 🟡 **P1** | Wire caller CRM lookup to initial Twilio stream greeting | `src/voice/pipeline.py` |
| 🟡 **P1** | Add API key support to React frontend fetch client | `frontend/src/App.jsx` |
| 🟢 **P2** | Add restaurant schema and RLS policies to master SQL | `supabase/schema.sql` |
| 🟢 **P2** | Update `GROQ_MODEL` default to `llama-3.3-70b-versatile` | `src/config.py`, `.env.example`, `README.md` |
| 🟢 **P2** | Add multi-stage `Dockerfile` and `docker-compose.yml` | `Dockerfile`, `docker-compose.yml` |
