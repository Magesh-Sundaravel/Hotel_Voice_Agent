from datetime import date, timedelta
import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.agent.graph import create_agent_graph
from src.agent.state import AgentState
from src.repositories.hotel_room_repo import InMemoryHotelRoomRepository
from src.repositories.memory_repo import (
    InMemoryGuestCRMRepository,
    InMemoryNotificationRepository,
)
from src.services.guest_crm_service import GuestCRMService
from src.services.hotel_booking_service import HotelBookingService


class ScriptedMockLLM:
    def __init__(self, responses):
        self.responses = list(responses)
        self.idx = 0

    def bind_tools(self, tools):
        return self

    async def ainvoke(self, messages):
        if self.idx < len(self.responses):
            resp = self.responses[self.idx]
            self.idx += 1
            return resp
        return AIMessage(content="Posso esserLe utile con qualcos'altro da Sina Hotels?")


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
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "check_room_availability",
                    "args": {
                        "check_in_date": d_in,
                        "check_out_date": d_out,
                        "guests_count": 2,
                        "category": "deluxe",
                    },
                    "id": "call_avail_1",
                    "type": "tool_call",
                }
            ],
        ),
        AIMessage(
            content="",
            tool_calls=[
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
                    "type": "tool_call",
                }
            ],
        ),
        AIMessage(
            content="Gentile Signora Pausini, la Sua prenotazione per la Camera Deluxe è confermata! Codice SINA-2025. Arrivederci!"
        ),
    ]

    mock_llm = ScriptedMockLLM(responses)
    agent = create_agent_graph(
        hotel_id="sina_bernini_bristol",
        hotel_name="Sina Bernini Bristol",
        llm=mock_llm,
        hotel_booking_service=booking_svc,
        guest_crm_service=crm_svc,
    )

    state: AgentState = {
        "messages": [
            HumanMessage(
                content=f"Buongiorno, vorrei prenotare una camera Deluxe per 2 persone dal {d_in} al {d_out} a nome Laura Pausini, telefono +39 333 5556677."
            )
        ],
        "caller_phone": "+39 333 5556677",
        "caller_name": "Laura Pausini",
        "current_date": date.today().isoformat(),
    }

    result = await agent.ainvoke(state)
    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 2
    assert "Deluxe" in tool_messages[0].content
    assert "confermata con codice" in tool_messages[1].content


@pytest.mark.asyncio
async def test_hotel_early_departure_agent_flow():
    room_repo = InMemoryHotelRoomRepository()
    notif_repo = InMemoryNotificationRepository()
    crm_repo = InMemoryGuestCRMRepository()
    crm_svc = GuestCRMService(crm_repo, notif_repo)
    booking_svc = HotelBookingService(room_repo, notif_repo, crm_svc)

    responses = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "report_early_departure",
                    "args": {
                        "reference_code": "SINA-1018",
                        "guest_phone": "+39 347 1234567",
                        "reason": "Rientro urgente per lavoro",
                    },
                    "id": "call_early_dep_1",
                    "type": "tool_call",
                }
            ],
        ),
        AIMessage(
            content="Gentile Signor Ferri, abbiamo registrato la Sua partenza anticipata. Il conto è stato aggiornato. La ringraziamo per aver soggiornato a Sina Hotels."
        ),
    ]

    mock_llm = ScriptedMockLLM(responses)
    agent = create_agent_graph(
        hotel_id="sina_bernini_bristol",
        hotel_name="Sina Bernini Bristol",
        llm=mock_llm,
        hotel_booking_service=booking_svc,
        guest_crm_service=crm_svc,
    )

    state: AgentState = {
        "messages": [
            HumanMessage(
                content="Buongiorno, sono Roberto Ferri dalla camera 101, prenotazione SINA-1018. Purtroppo devo partire oggi in anticipo per un'urgenza di lavoro."
            )
        ],
        "caller_phone": "+39 347 1234567",
        "caller_name": "Roberto Ferri",
        "current_date": date.today().isoformat(),
    }

    result = await agent.ainvoke(state)
    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 1
    assert "partenza anticipata" in tool_messages[0].content
