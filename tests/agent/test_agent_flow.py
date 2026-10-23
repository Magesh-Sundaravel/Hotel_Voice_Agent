from datetime import date, timedelta
from typing import Any

import pytest

from src.models import CreateReservationRequest
from src.voice.agent import VoiceAgent
from src.voice.session import CallSession


class ScriptedMockLLM:
    """Deterministic Mock LLM that returns a sequence of predetermined responses."""

    def __init__(self, responses: list[dict[str, Any]]):
        self.responses = list(responses)
        self.idx = 0

    async def ainvoke(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        if self.idx < len(self.responses):
            resp = self.responses[self.idx]
            self.idx += 1
            return resp
        return {"content": "Come posso aiutarLa ulteriormente?", "tool_calls": []}


@pytest.mark.asyncio
async def test_agent_graph_full_booking_flow(
    restaurant_repo,
    booking_repo,
    notification_repo,
    availability_service,
    booking_service,
    restaurant_service,
    notification_service,
):
    target_date = (date.today() + timedelta(days=2)).isoformat()

    responses = [
        {
            "content": "",
            "tool_calls": [
                {
                    "name": "check_table_availability",
                    "args": {
                        "booking_date": target_date,
                        "booking_time": "20:00",
                        "party_size": 2,
                    },
                    "id": "call_check_avail",
                }
            ],
        },
        {
            "content": "",
            "tool_calls": [
                {
                    "name": "create_reservation",
                    "args": {
                        "customer_name": "Mario Rossi",
                        "customer_phone": "+39 333 1234567",
                        "party_size": 2,
                        "booking_date": target_date,
                        "booking_time": "20:00",
                        "dietary_notes": None,
                    },
                    "id": "call_create_res",
                }
            ],
        },
        {
            "content": "Perfetto Signor Rossi, la Sua prenotazione per 2 persone è confermata per il 20:00. Il codice è BV-1234. A presto!",
            "tool_calls": [],
        },
    ]

    mock_llm = ScriptedMockLLM(responses)

    agent = VoiceAgent(
        hotel_id="default_trattoria",
        hotel_name="Trattoria Bella Vista",
        llm=mock_llm,
        availability_service=availability_service,
        booking_service=booking_service,
        restaurant_service=restaurant_service,
        notification_service=notification_service,
    )

    session = CallSession(
        call_id="call_trattoria_1",
        user_id="user_3331234567",
        caller_phone="+39 333 1234567",
        caller_name="Mario Rossi",
        hotel_id="default_trattoria",
        hotel_name="Trattoria Bella Vista",
    )

    result = await agent.run_turn(
        session,
        f"Vorrei prenotare un tavolo per 2 persone per il {target_date} alle 20:00 a nome Mario Rossi, telefono +39 333 1234567",
    )

    tool_messages = [m for m in session.messages if m.get("role") == "tool"]
    assert len(tool_messages) == 2

    # Check availability tool result
    assert "DISPONIBILE" in str(tool_messages[0].get("content"))

    # Check create reservation tool result
    assert "confermata con successo" in str(tool_messages[1].get("content"))

    # Final assistant reply
    assert "confermata" in result.reply_text


@pytest.mark.asyncio
async def test_agent_graph_full_slot_curveball_handling(
    restaurant_repo,
    booking_repo,
    notification_repo,
    availability_service,
    booking_service,
    restaurant_service,
    notification_service,
):
    target_date = date.today() + timedelta(days=3)

    # Pre-book both 4-person tables at 20:00 to simulate fully booked slot
    await booking_service.create_booking(
        restaurant_id="default_trattoria",
        request=CreateReservationRequest(
            customer_name="Ospite 1",
            customer_phone="+39 333 1111111",
            party_size=4,
            booking_date=target_date,
            booking_time="20:00",
        ),
    )
    await booking_service.create_booking(
        restaurant_id="default_trattoria",
        request=CreateReservationRequest(
            customer_name="Ospite 2",
            customer_phone="+39 333 2222222",
            party_size=4,
            booking_date=target_date,
            booking_time="20:00",
        ),
    )

    responses = [
        {
            "content": "",
            "tool_calls": [
                {
                    "name": "check_table_availability",
                    "args": {
                        "booking_date": target_date.isoformat(),
                        "booking_time": "20:00",
                        "party_size": 4,
                    },
                    "id": "call_full_slot",
                }
            ],
        },
        {
            "content": "Mi dispiace, alle 20:00 siamo al completo per 4 persone. Abbiamo però disponibilità alle 19:30 o alle 21:30. Preferisce uno di questi orari?",
            "tool_calls": [],
        },
    ]

    mock_llm = ScriptedMockLLM(responses)

    agent = VoiceAgent(
        hotel_id="default_trattoria",
        hotel_name="Trattoria Bella Vista",
        llm=mock_llm,
        availability_service=availability_service,
        booking_service=booking_service,
        restaurant_service=restaurant_service,
        notification_service=notification_service,
    )

    session = CallSession(
        call_id="call_trattoria_2",
        user_id="user_3335555555",
        caller_phone="+39 333 5555555",
        caller_name="Paolo Neri",
        hotel_id="default_trattoria",
        hotel_name="Trattoria Bella Vista",
    )

    result = await agent.run_turn(
        session,
        f"Avete un tavolo per 4 per il {target_date.isoformat()} alle 20:00?",
    )
    tool_messages = [m for m in session.messages if m.get("role") == "tool"]
    assert len(tool_messages) == 1
    assert "NON DISPONIBILE" in str(tool_messages[0].get("content"))
    assert "Orari alternativi disponibili" in str(tool_messages[0].get("content"))
    assert "al completo" in result.reply_text


@pytest.mark.asyncio
async def test_agent_graph_faq_handling(
    restaurant_repo,
    booking_repo,
    notification_repo,
    availability_service,
    booking_service,
    restaurant_service,
    notification_service,
):
    responses = [
        {
            "content": "",
            "tool_calls": [
                {
                    "name": "get_restaurant_faq_or_hours",
                    "args": {"query": "parcheggio"},
                    "id": "call_faq",
                }
            ],
        },
        {
            "content": "Certamente! Abbiamo una convenzione con il Garage Garibaldi a 50 metri dal ristorante, con la prima ora gratuita.",
            "tool_calls": [],
        },
    ]

    mock_llm = ScriptedMockLLM(responses)

    agent = VoiceAgent(
        hotel_id="default_trattoria",
        hotel_name="Trattoria Bella Vista",
        llm=mock_llm,
        availability_service=availability_service,
        booking_service=booking_service,
        restaurant_service=restaurant_service,
        notification_service=notification_service,
    )

    session = CallSession(
        call_id="call_trattoria_3",
        user_id="user_3337777777",
        caller_phone="+39 333 7777777",
        caller_name="Elena",
        hotel_id="default_trattoria",
        hotel_name="Trattoria Bella Vista",
    )

    result = await agent.run_turn(
        session,
        "Buonasera, c'è un parcheggio vicino al locale?",
    )
    tool_messages = [m for m in session.messages if m.get("role") == "tool"]
    assert len(tool_messages) == 1
    assert "Garage Garibaldi" in str(tool_messages[0].get("content"))
    assert "Garage Garibaldi" in result.reply_text


@pytest.mark.asyncio
async def test_agent_graph_end_call_flow(
    restaurant_repo,
    booking_repo,
    notification_repo,
    availability_service,
    booking_service,
    restaurant_service,
    notification_service,
):
    responses = [
        {
            "content": "",
            "tool_calls": [
                {
                    "name": "end_call",
                    "args": {"farewell_message": "Grazie mille e buona serata!"},
                    "id": "call_end",
                }
            ],
        },
        {
            "content": "Grazie mille e buona serata! Arrivederci.",
            "tool_calls": [],
        },
    ]

    mock_llm = ScriptedMockLLM(responses)

    agent = VoiceAgent(
        hotel_id="default_trattoria",
        hotel_name="Trattoria Bella Vista",
        llm=mock_llm,
        availability_service=availability_service,
        booking_service=booking_service,
        restaurant_service=restaurant_service,
        notification_service=notification_service,
    )

    session = CallSession(
        call_id="call_trattoria_4",
        user_id="user_3337777777",
        caller_phone="+39 333 7777777",
        caller_name="Elena",
        hotel_id="default_trattoria",
        hotel_name="Trattoria Bella Vista",
    )

    result = await agent.run_turn(
        session,
        "No grazie, a posto così. Buona serata!",
    )
    tool_messages = [m for m in session.messages if m.get("role") == "tool"]
    assert len(tool_messages) == 1
    assert "CHIAMATA_TERMINATA" in str(tool_messages[0].get("content"))
    assert result.call_ended is True
