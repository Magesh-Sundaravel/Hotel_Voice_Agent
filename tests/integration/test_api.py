import asyncio
from datetime import date, timedelta
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.models import BookingStatus, CreateReservationRequest
from src.repositories import (
    get_booking_repository,
    get_notification_repository,
    get_restaurant_repository,
)
from src.services import AvailabilityService, BookingService, NotificationService
from src.voice.agent import VoiceAgent


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Sina" in data["hotel"]


def test_availability_endpoint(client):
    target_date = (date.today() + timedelta(days=2)).isoformat()
    response = client.get(
        "/api/availability",
        params={
            "booking_date": target_date,
            "booking_time": "20:00",
            "party_size": 4,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_available"] is True
    assert data["party_size"] == 4


@pytest.mark.asyncio
async def test_reservations_and_notifications_endpoints(client):
    # Seed a reservation
    book_repo = get_booking_repository()
    notif_repo = get_notification_repository()
    rest_repo = get_restaurant_repository()

    avail_svc = AvailabilityService(rest_repo, book_repo)
    notif_svc = NotificationService(notif_repo)
    booking_svc = BookingService(book_repo, avail_svc, notif_svc)

    target_date = date.today() + timedelta(days=5)

    # Cancel any previous test reservations for this customer to ensure clean slot
    for old_res in await book_repo.get_by_customer_phone("+39 333 8888888"):
        old_res.status = BookingStatus.CANCELLED
        await book_repo.update_reservation(old_res)

    res = await booking_svc.create_booking(
        restaurant_id="default_trattoria",
        request=CreateReservationRequest(
            customer_name="Chiara Mancini",
            customer_phone="+39 333 8888888",
            party_size=2,
            booking_date=target_date,
            booking_time="13:00",
            dietary_notes="Allergia ai crostacei",
        ),
    )
    assert res.success is True

    # Test GET /api/reservations
    resp = client.get("/api/reservations", params={"booking_date": target_date.isoformat()})
    assert resp.status_code == 200
    reservations = resp.json()
    assert len(reservations) >= 1
    assert any(r["customer_name"] == "Chiara Mancini" for r in reservations)

    # Test GET /api/notifications
    notif_resp = client.get("/api/notifications")
    assert notif_resp.status_code == 200
    notifs = notif_resp.json()
    assert len(notifs) >= 1

    # Test POST /api/notifications/{id}/read
    notif_id = notifs[0]["id"]
    read_resp = client.post(f"/api/notifications/{notif_id}/read")
    assert read_resp.status_code == 200
    assert read_resp.json()["status"] == "ok"


def test_availability_past_date_rejected(client):
    response = client.get(
        "/api/availability",
        params={
            "booking_date": "2020-01-01",
            "booking_time": "20:00",
            "party_size": 2,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_available"] is False
    assert "data passata" in data["reason"]


def test_chat_and_reset_endpoints(client):
    session_id = "test_session_12345"

    # Reset endpoint
    del_resp = client.delete(f"/api/chat/{session_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "ok"


def test_lifespan_caches_agent_and_services(client):
    # Verify shared services and VoiceAgent are stored on app.state
    assert hasattr(app.state, "crm_service")
    assert hasattr(app.state, "hotel_booking_service")
    assert hasattr(app.state, "notification_service")
    assert hasattr(app.state, "availability_service")
    assert hasattr(app.state, "booking_service")
    assert hasattr(app.state, "restaurant_service")
    assert hasattr(app.state, "voice_agent")
    assert hasattr(app.state, "agent_graph")


class EchoMockLLM:
    async def ainvoke(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        last_human = next(
            (
                m.get("content", "")
                for m in reversed(messages)
                if isinstance(m, dict) and m.get("role") == "user"
            ),
            "default",
        )
        return {"content": f"Risposta: {last_human}", "tool_calls": []}


@pytest.mark.asyncio
async def test_concurrent_chat_sessions_have_isolated_state(client):
    mock_agent = VoiceAgent(
        llm=EchoMockLLM(),
    )
    original_agent = getattr(app.state, "voice_agent", None)
    app.state.voice_agent = mock_agent

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as ac:
            session_1 = "session_isolated_1"
            session_2 = "session_isolated_2"

            # Execute two calls concurrently across different sessions
            resp_1, resp_2 = await asyncio.gather(
                ac.post(
                    "/api/chat",
                    json={"session_id": session_1, "message": "Ciao da Roma"},
                ),
                ac.post(
                    "/api/chat",
                    json={"session_id": session_2, "message": "Ciao da Milano"},
                ),
            )

            assert resp_1.status_code == 200
            assert resp_2.status_code == 200

            data_1 = resp_1.json()
            data_2 = resp_2.json()

            assert data_1["session_id"] == session_1
            assert "Risposta: Ciao da Roma" in data_1["response"]
            assert data_1["history_length"] == 2

            assert data_2["session_id"] == session_2
            assert "Risposta: Ciao da Milano" in data_2["response"]
            assert data_2["history_length"] == 2

            # Now send turn 2 for session 1 only
            resp_1_turn2 = await ac.post(
                "/api/chat",
                json={"session_id": session_1, "message": "Richiesta 2 Roma"},
            )
            assert resp_1_turn2.status_code == 200
            data_1_turn2 = resp_1_turn2.json()

            # Session 1 should now have 4 messages (2 user + 2 ai)
            assert data_1_turn2["history_length"] == 4
            assert "Risposta: Richiesta 2 Roma" in data_1_turn2["response"]

            # Reset both sessions
            await ac.delete(f"/api/chat/{session_1}")
            await ac.delete(f"/api/chat/{session_2}")

    finally:
        app.state.voice_agent = original_agent
