"""Tests for API Key authentication and Twilio signature verification."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from twilio.request_validator import RequestValidator

from src.api.main import app
from src.config import settings


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# ============================================================================
# API Key Authentication Tests
# ============================================================================


def test_internal_crm_route_requires_api_key_when_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", "super-secret-key-1234")

    # Request without API key
    res = client.get("/api/crm/guests")
    assert res.status_code == 401
    assert "Invalid or missing API key" in res.json()["detail"]

    # Request with wrong API key in X-API-Key
    res_wrong = client.get("/api/crm/guests", headers={"X-API-Key": "wrong-key"})
    assert res_wrong.status_code == 401

    # Request with wrong Bearer token
    res_wrong_bearer = client.get(
        "/api/crm/guests", headers={"Authorization": "Bearer wrong-key"}
    )
    assert res_wrong_bearer.status_code == 401

    # Request with valid X-API-Key header
    res_valid_header = client.get(
        "/api/crm/guests", headers={"X-API-Key": "super-secret-key-1234"}
    )
    assert res_valid_header.status_code == 200

    # Request with valid Bearer token
    res_valid_bearer = client.get(
        "/api/crm/guests",
        headers={"Authorization": "Bearer super-secret-key-1234"},
    )
    assert res_valid_bearer.status_code == 200


def test_internal_room_bookings_routes_require_api_key(client, monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", "super-secret-key-1234")

    # /api/room-bookings requires auth
    res_no_auth = client.get("/api/room-bookings")
    assert res_no_auth.status_code == 401

    res_auth = client.get(
        "/api/room-bookings", headers={"X-API-Key": "super-secret-key-1234"}
    )
    assert res_auth.status_code == 200

    # /api/rooms requires auth
    res_rooms_no_auth = client.get("/api/rooms")
    assert res_rooms_no_auth.status_code == 401

    res_rooms_auth = client.get(
        "/api/rooms", headers={"X-API-Key": "super-secret-key-1234"}
    )
    assert res_rooms_auth.status_code == 200

    # /api/hotel-stats requires auth
    res_stats_no_auth = client.get("/api/hotel-stats")
    assert res_stats_no_auth.status_code == 401

    res_stats_auth = client.get(
        "/api/hotel-stats", headers={"X-API-Key": "super-secret-key-1234"}
    )
    assert res_stats_auth.status_code == 200


def test_internal_reservations_and_notifications_require_api_key(client, monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", "super-secret-key-1234")

    # /api/reservations
    res = client.get("/api/reservations")
    assert res.status_code == 401

    res_ok = client.get(
        "/api/reservations", headers={"X-API-Key": "super-secret-key-1234"}
    )
    assert res_ok.status_code == 200

    # /api/notifications
    res_notif = client.get("/api/notifications")
    assert res_notif.status_code == 401

    res_notif_ok = client.get(
        "/api/notifications", headers={"X-API-Key": "super-secret-key-1234"}
    )
    assert res_notif_ok.status_code == 200


def test_outbound_call_requires_api_key(client, monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", "super-secret-key-1234")

    # Outbound call without key -> 401
    res = client.post("/api/twilio/call", json={"to_phone": "+393331112233"})
    assert res.status_code == 401

    # Outbound call with valid key (may fail on twilio credentials, but passes auth)
    res_auth = client.post(
        "/api/twilio/call",
        json={"to_phone": "+393331112233"},
        headers={"X-API-Key": "super-secret-key-1234"},
    )
    # Auth passed: status is not 401
    assert res_auth.status_code != 401


def test_unauthenticated_endpoints_remain_accessible_without_api_key(client, monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", "super-secret-key-1234")

    # /health is unauthenticated
    res_health = client.get("/health")
    assert res_health.status_code == 200

    # /api/availability is unauthenticated
    from datetime import date, timedelta
    target_date = (date.today() + timedelta(days=2)).isoformat()
    res_avail = client.get(
        "/api/availability",
        params={
            "booking_date": target_date,
            "booking_time": "20:00",
            "party_size": 2,
        },
    )
    assert res_avail.status_code == 200

    # /api/chat reset is accessible
    res_del = client.delete("/api/chat/some_session_123")
    assert res_del.status_code == 200


def test_unconfigured_api_key_allows_access_in_dev_mode(client, monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", "")

    # When API_KEY is unset, requests pass through without error
    res = client.get("/api/crm/guests")
    assert res.status_code == 200


# ============================================================================
# Twilio Signature Verification Tests
# ============================================================================


def test_twilio_webhook_rejects_missing_signature_when_enforced(client, monkeypatch):
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "mock_auth_token_xyz")
    monkeypatch.setattr(settings, "TWILIO_VALIDATE_SIGNATURE", True)

    res = client.post(
        "/api/twilio/incoming-call",
        data={"From": "+393331234567", "CallSid": "CA123456"},
    )
    assert res.status_code == 403
    assert "Missing Twilio signature" in res.json()["detail"]


def test_twilio_webhook_rejects_invalid_signature(client, monkeypatch):
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "mock_auth_token_xyz")
    monkeypatch.setattr(settings, "TWILIO_VALIDATE_SIGNATURE", True)

    res = client.post(
        "/api/twilio/incoming-call",
        data={"From": "+393331234567", "CallSid": "CA123456"},
        headers={"X-Twilio-Signature": "invalid_signature_hash"},
    )
    assert res.status_code == 403
    assert "Invalid Twilio signature" in res.json()["detail"]


def test_twilio_webhook_accepts_valid_signature(client, monkeypatch):
    auth_token = "mock_auth_token_xyz"
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", auth_token)
    monkeypatch.setattr(settings, "TWILIO_VALIDATE_SIGNATURE", True)
    monkeypatch.setattr(settings, "PUBLIC_URL", "https://api.sinahotels.com")

    validator = RequestValidator(auth_token)
    post_data = {"From": "+393331234567", "CallSid": "CA123456"}
    url = "https://api.sinahotels.com/api/twilio/incoming-call"
    valid_sig = validator.compute_signature(url, post_data)

    res = client.post(
        "/api/twilio/incoming-call",
        data=post_data,
        headers={"X-Twilio-Signature": valid_sig},
    )
    assert res.status_code == 200
    assert "application/xml" in res.headers["content-type"]


def test_twilio_status_webhook_signature_verification(client, monkeypatch):
    auth_token = "mock_auth_token_xyz"
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", auth_token)
    monkeypatch.setattr(settings, "TWILIO_VALIDATE_SIGNATURE", True)
    monkeypatch.setattr(settings, "PUBLIC_URL", "https://api.sinahotels.com")

    validator = RequestValidator(auth_token)
    post_data = {"CallSid": "CA123456", "CallStatus": "completed", "CallDuration": "30"}
    url = "https://api.sinahotels.com/api/twilio/status"
    valid_sig = validator.compute_signature(url, post_data)

    # Valid signature
    res = client.post(
        "/api/twilio/status",
        data=post_data,
        headers={"X-Twilio-Signature": valid_sig},
    )
    assert res.status_code == 200
    assert res.json() == {"status": "received"}

    # Invalid signature on status callback
    res_bad = client.post(
        "/api/twilio/status",
        data=post_data,
        headers={"X-Twilio-Signature": "bad_sig"},
    )
    assert res_bad.status_code == 403


def test_twilio_webhook_bypasses_signature_when_disabled_and_no_sig_header(client, monkeypatch):
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "mock_auth_token_xyz")
    monkeypatch.setattr(settings, "TWILIO_VALIDATE_SIGNATURE", False)

    res = client.post(
        "/api/twilio/incoming-call",
        data={"From": "+393331234567", "CallSid": "CA123456"},
    )
    assert res.status_code == 200
