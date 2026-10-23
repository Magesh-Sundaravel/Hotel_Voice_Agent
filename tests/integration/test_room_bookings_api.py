from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client


def test_list_rooms_endpoint(client):
    response = client.get("/api/rooms")
    assert response.status_code == 200
    rooms = response.json()
    assert len(rooms) >= 9
    assert any(r["room_number"] == "402" for r in rooms)


def test_hotel_stats_endpoint(client):
    response = client.get("/api/hotel-stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["hotel_name"] == "Sina Bernini Bristol"
    assert stats["total_rooms"] >= 9
    assert "early_departures_count" in stats
    assert stats["early_departures_count"] >= 1  # Roberto Ferri seeded


def test_list_bookings_filtered_by_early_departure(client):
    response = client.get("/api/room-bookings", params={"status": "early_departure"})
    assert response.status_code == 200
    bookings = response.json()
    assert len(bookings) >= 1
    assert any(b["reference_code"] == "SINA-1018" for b in bookings)
    assert bookings[0]["is_early_departure"] is True


def test_check_availability_api(client):
    d_in = (date.today() + timedelta(days=30)).isoformat()
    d_out = (date.today() + timedelta(days=33)).isoformat()
    response = client.post(
        "/api/room-bookings/check-availability",
        json={
            "check_in_date": d_in,
            "check_out_date": d_out,
            "guests_count": 2,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_available"] is True
    assert data["nights"] == 3
    assert len(data["options"]) >= 3


def test_create_and_cancel_room_booking_api(client):
    d_in = (date.today() + timedelta(days=40)).isoformat()
    d_out = (date.today() + timedelta(days=42)).isoformat()
    # Create
    create_resp = client.post(
        "/api/room-bookings",
        json={
            "guest_name": "Valerio Mastandrea",
            "guest_phone": "+39 333 7778899",
            "category": "junior_suite",
            "check_in_date": d_in,
            "check_out_date": d_out,
            "guests_count": 2,
            "special_requests": "Vista panoramica",
        },
    )
    assert create_resp.status_code == 200
    create_data = create_resp.json()
    assert create_data["success"] is True
    ref = create_data["booking"]["reference_code"]

    # Cancel
    cancel_resp = client.post(
        "/api/room-bookings/cancel",
        json={
            "reference_code": ref,
            "guest_phone": "+39 333 7778899",
            "reason": "Imprevisto personale",
        },
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["success"] is True
