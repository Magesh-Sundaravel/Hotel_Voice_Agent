from fastapi.testclient import TestClient

from src.api.main import app


def test_twilio_incoming_call_webhook():
    client = TestClient(app)
    response = client.post(
        "/api/twilio/incoming-call",
        data={
            "From": "+393331234567",
            "To": "+39064883051",
            "CallSid": "CA1234567890abcdef",
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    xml_text = response.text
    assert "<Connect>" in xml_text
    assert "<Stream" in xml_text
    assert "/api/twilio/stream" in xml_text
    assert "caller_phone" in xml_text
    assert "+393331234567" in xml_text


def test_twilio_call_status():
    client = TestClient(app)
    response = client.post(
        "/api/twilio/status",
        data={
            "CallSid": "CA1234567890abcdef",
            "CallStatus": "completed",
            "CallDuration": "45",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"status": "received"}


def test_twilio_websocket_connection(monkeypatch):
    async def mock_stream_speech(self, text, chunk_size=320):
        yield b"\xff" * chunk_size

    monkeypatch.setattr(
        "src.voice.tts.ElevenLabsTTSService.stream_speech",
        mock_stream_speech,
    )

    client = TestClient(app)
    with client.websocket_connect("/api/twilio/stream") as websocket:
        # Send connected event
        websocket.send_json({"event": "connected", "protocol": "Call"})

        # Send start event
        websocket.send_json(
            {
                "event": "start",
                "start": {
                    "streamSid": "MZ123456",
                    "callSid": "CA123456",
                    "customParameters": {
                        "caller_phone": "+393331234567",
                        "hotel_name": "Sina Bernini Bristol",
                    },
                },
            }
        )

        # Expect greeting media event from bot
        received = websocket.receive_json()
        assert received.get("event") == "media"
        assert received.get("streamSid") == "MZ123456"
        assert "payload" in received.get("media", {})

        # Send stop event
        websocket.send_json({"event": "stop", "stop": {"callSid": "CA123456"}})


def test_twilio_outbound_call_endpoint_missing_creds(monkeypatch):
    from src.api.routes import twilio_routes

    monkeypatch.setattr(twilio_routes.twilio_service, "_client", None)
    monkeypatch.setattr(twilio_routes.twilio_service, "phone_number", None)

    client = TestClient(app)
    # When Twilio credentials are not set, it should return 400 Bad Request
    response = client.post("/api/twilio/call", json={"to_phone": "+393331234567"})
    assert response.status_code == 400
    assert "Twilio credentials" in response.json()["detail"]


def test_twilio_outbound_call_endpoint_with_mocked_client(monkeypatch):
    from unittest.mock import MagicMock

    from src.api.routes import twilio_routes

    mock_client = MagicMock()
    mock_call = MagicMock()
    mock_call.sid = "CA_MOCK_12345"
    mock_client.calls.create.return_value = mock_call

    monkeypatch.setattr(twilio_routes.twilio_service, "_client", mock_client)
    monkeypatch.setattr(twilio_routes.twilio_service, "phone_number", "+39064883051")
    monkeypatch.setattr(twilio_routes.settings, "PUBLIC_URL", "https://mock-domain.ngrok-free.app")

    client = TestClient(app)
    response = client.post("/api/twilio/call", json={"to_phone": "+393339998877"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "initiated"
    assert data["call_sid"] == "CA_MOCK_12345"
    assert data["to"] == "+393339998877"
    mock_client.calls.create.assert_called_once_with(
        to="+393339998877",
        from_="+39064883051",
        url="https://mock-domain.ngrok-free.app/api/twilio/incoming-call",
    )
