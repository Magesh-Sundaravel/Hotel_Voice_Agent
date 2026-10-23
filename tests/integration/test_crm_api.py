import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_caller_context_in_house_guest(client):
    response = client.get(
        "/api/crm/caller-context",
        params={"phone": "+39 333 1112233"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_known_guest"] is True
    assert data["guest"]["last_name"] == "Rossi"
    assert data["stage"] == "in_house"
    assert data["stay"]["room_number"] == "402"
    assert "camera 402" in data["suggested_greeting_it"].lower()


def test_get_caller_context_unknown_caller(client):
    response = client.get(
        "/api/crm/caller-context",
        params={"phone": "+39 000 0000000"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_known_guest"] is False
    assert data["stage"] == "non_resident"


def test_list_guests(client):
    response = client.get("/api/crm/guests")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3


def test_get_guest_profile(client):
    response = client.get("/api/crm/guests/+393359988776")
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Andrea"
    assert data["vip_tier"] == "sina_privilege_vip"


def test_update_guest_preferences(client):
    response = client.post(
        "/api/crm/guests/+393359988776/preferences",
        json={
            "room_preference": "cuscino ortopedico",
            "favorite_drink": "The verde biologico",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "cuscino ortopedico" in data["preferences"]["room_preferences"]
    assert "The verde biologico" in data["preferences"]["favorite_drinks"]


def test_create_concierge_request_api(client):
    response = client.post(
        "/api/crm/concierge/requests",
        json={
            "phone": "+39 333 1112233",
            "category": "dining",
            "title": "Tavolo per Anniversario Rooftop The Flair",
            "details": "Tavolo appartato all'esterno per 2 persone con vista su Piazza Barberini.",
            "scheduled_time": "20:30",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"].startswith("req_")
    assert data["category"] == "dining"


def test_get_recommendations_api(client):
    response = client.get(
        "/api/crm/recommendations",
        params={"phone": "+39 333 1112233"},
    )
    assert response.status_code == 200
    items = response.json()
    assert len(items) > 0
    assert any("The Flair" in item["title"] for item in items)


def test_submit_feedback_api(client):
    response = client.post(
        "/api/crm/feedback",
        json={
            "phone": "+39 340 5544332",
            "nps_score": 9,
            "comments": "Soggiorno impeccabile, personale squisito.",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nps_score"] == 9
