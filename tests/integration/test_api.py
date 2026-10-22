from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.models import BookingStatus, CreateReservationRequest
from src.repositories import get_booking_repository, get_notification_repository
from src.services import AvailabilityService, BookingService, NotificationService


@pytest.fixture
def client():
    return TestClient(app)


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
    from src.repositories import get_restaurant_repository

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
    resp = client.get(
        "/api/reservations", params={"booking_date": target_date.isoformat()}
    )
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
