from datetime import date, timedelta
from typing import Any

import pytest

from src.repositories.hotel_room_repo import InMemoryHotelRoomRepository
from src.repositories.memory_repo import (
    InMemoryGuestCRMRepository,
    InMemoryNotificationRepository,
)
from src.services.guest_crm_service import GuestCRMService
from src.services.hotel_booking_service import HotelBookingService
from src.voice.agent import VoiceAgent
from src.voice.session import CallSession


class ScriptedMockLLM:
    def __init__(self, responses: list[dict[str, Any]]):
        self.responses = list(responses)
        self.idx = 0

    async def ainvoke(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        if self.idx < len(self.responses):
            resp = self.responses[self.idx]
            self.idx += 1
            return resp
        return {"content": "Posso esserLe utile con qualcos'altro da Sina Hotels?", "tool_calls": []}


@pytest.mark.asyncio
async def test_hotel_room_booking_agent_flow():
    room_repo = InMemoryHotelRoomRepository()
    notif_repo = InMemoryNotificationRepository()
    crm_repo = InMemoryGuestCRMRepository()
    crm_svc = GuestCRMService(crm_repo, notif_repo)
    booking_svc = HotelBookingService(room_repo, notif_repo, crm_svc)

    d_in = (date.today() + timedelta(days=7)).isoformat()
    d_out = (date.today() + timedelta(days=9)).isoformat()

    responses = [
        {
            "content": "",
            "tool_calls": [
                {
                    "name": "check_room_availability",
                    "args": {
                        "check_in_date": d_in,
                        "check_out_date": d_out,
                        "guests_count": 2,
                        "category": "deluxe",
                    },
                    "id": "call_avail_1",
                }
            ],
        },
        {
            "content": "",
            "tool_calls": [
                {
                    "name": "create_hotel_room_booking",
                    "args": {
                        "guest_name": "Laura Pausini",
                        "guest_phone": "+39 333 5556677",
                        "category": "deluxe",
                        "check_in_date": d_in,
                        "check_out_date": d_out,
                        "guests_count": 2,
                        "special_requests": "Letto matrimoniale King",
                    },
                    "id": "call_book_1",
                }
            ],
        },
        {
            "content": "Gentile Signora Pausini, la Sua prenotazione per la Camera Deluxe è confermata! Codice SINA-2025. Arrivederci!",
            "tool_calls": [],
        },
    ]

    mock_llm = ScriptedMockLLM(responses)
    agent = VoiceAgent(
        hotel_id="sina_bernini_bristol",
        hotel_name="Sina Bernini Bristol",
        llm=mock_llm,
        hotel_booking_service=booking_svc,
        guest_crm_service=crm_svc,
    )

    session = CallSession(
        call_id="call_test_1",
        user_id="user_3335556677",
        caller_phone="+39 333 5556677",
        caller_name="Laura Pausini",
        hotel_id="sina_bernini_bristol",
        hotel_name="Sina Bernini Bristol",
    )

    result = await agent.run_turn(
        session,
        f"Buongiorno, vorrei prenotare una camera Deluxe per 2 persone dal {d_in} al {d_out} a nome Laura Pausini, telefono +39 333 5556677.",
    )

    tool_messages = [m for m in session.messages if m.get("role") == "tool"]
    assert len(tool_messages) == 2
    assert "Deluxe" in str(tool_messages[0].get("content"))
    assert "reference_code" in str(tool_messages[1].get("content"))
    assert "confermata" in result.reply_text


@pytest.mark.asyncio
async def test_hotel_early_departure_agent_flow():
    room_repo = InMemoryHotelRoomRepository()
    notif_repo = InMemoryNotificationRepository()
    crm_repo = InMemoryGuestCRMRepository()
    crm_svc = GuestCRMService(crm_repo, notif_repo)
    booking_svc = HotelBookingService(room_repo, notif_repo, crm_svc)

    responses = [
        {
            "content": "",
            "tool_calls": [
                {
                    "name": "report_early_departure",
                    "args": {
                        "reference_code": "SINA-1018",
                        "guest_phone": "+39 347 1234567",
                        "reason": "Rientro urgente per lavoro",
                    },
                    "id": "call_early_dep_1",
                }
            ],
        },
        {
            "content": "Gentile Signor Ferri, abbiamo registrato la Sua partenza anticipata. Il conto è stato aggiornato. La ringraziamo per aver soggiornato a Sina Hotels.",
            "tool_calls": [],
        },
    ]

    mock_llm = ScriptedMockLLM(responses)
    agent = VoiceAgent(
        hotel_id="sina_bernini_bristol",
        hotel_name="Sina Bernini Bristol",
        llm=mock_llm,
        hotel_booking_service=booking_svc,
        guest_crm_service=crm_svc,
    )

    session = CallSession(
        call_id="call_test_2",
        user_id="user_3471234567",
        caller_phone="+39 347 1234567",
        caller_name="Roberto Ferri",
        hotel_id="sina_bernini_bristol",
        hotel_name="Sina Bernini Bristol",
    )

    result = await agent.run_turn(
        session,
        "Buongiorno, sono Roberto Ferri dalla camera 101, prenotazione SINA-1018. Purtroppo devo partire oggi in anticipo per un'urgenza di lavoro.",
    )

    tool_messages = [m for m in session.messages if m.get("role") == "tool"]
    assert len(tool_messages) == 1
    assert "partenza anticipata" in str(tool_messages[0].get("content"))
    assert "partenza anticipata" in result.reply_text
