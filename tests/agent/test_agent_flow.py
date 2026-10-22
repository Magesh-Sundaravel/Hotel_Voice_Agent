from datetime import date, timedelta

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.agent.graph import create_agent_graph
from src.agent.state import AgentState
from src.models import CreateReservationRequest


class ScriptedMockLLM:
    """Deterministic Mock LLM that returns a sequence of predetermined AIMessages."""

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
        return AIMessage(content="Come posso aiutarLa ulteriormente?")


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

    # Step 1: User says: "Vorrei prenotare un tavolo per 2 persone stasera alle 20:00 a nome Mario Rossi"
    # LLM decides to call check_table_availability first
    # Then after tool returns DISPONIBILE, LLM calls create_reservation
    # Then LLM confirms to user
    responses = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "check_table_availability",
                    "args": {
                        "booking_date": target_date,
                        "booking_time": "20:00",
                        "party_size": 2,
                    },
                    "id": "call_check_avail",
                    "type": "tool_call",
                }
            ],
        ),
        AIMessage(
            content="",
            tool_calls=[
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
                    "type": "tool_call",
                }
            ],
        ),
        AIMessage(
            content="Perfetto Signor Rossi, la Sua prenotazione per 2 persone è confermata per il 20:00. Il codice è BV-1234. A presto!"
        ),
    ]

    mock_llm = ScriptedMockLLM(responses)

    agent = create_agent_graph(
        restaurant_id="default_trattoria",
        restaurant_name="Trattoria Bella Vista",
        llm=mock_llm,
        availability_service=availability_service,
        booking_service=booking_service,
        restaurant_service=restaurant_service,
        notification_service=notification_service,
    )

    initial_state: AgentState = {
        "messages": [
            HumanMessage(
                content=f"Vorrei prenotare un tavolo per 2 persone per il {target_date} alle 20:00 a nome Mario Rossi, telefono +39 333 1234567"
            )
        ],
        "restaurant_id": "default_trattoria",
        "restaurant_name": "Trattoria Bella Vista",
        "caller_phone": "+39 333 1234567",
        "caller_name": "Mario Rossi",
        "current_date": date.today().isoformat(),
    }

    result = await agent.ainvoke(initial_state)

    messages = result["messages"]
    tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 2

    # Check availability tool result
    assert "DISPONIBILE" in tool_messages[0].content

    # Check create reservation tool result
    assert "confermata con successo" in tool_messages[1].content

    # Final assistant reply
    last_message = messages[-1]
    assert isinstance(last_message, AIMessage)
    assert "confermata" in last_message.content


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

    # Caller asks for 4 people at 20:00
    responses = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "check_table_availability",
                    "args": {
                        "booking_date": target_date.isoformat(),
                        "booking_time": "20:00",
                        "party_size": 4,
                    },
                    "id": "call_full_slot",
                    "type": "tool_call",
                }
            ],
        ),
        AIMessage(
            content="Mi dispiace, alle 20:00 siamo al completo per 4 persone. Abbiamo però disponibilità alle 19:30 o alle 21:30. Preferisce uno di questi orari?"
        ),
    ]

    mock_llm = ScriptedMockLLM(responses)

    agent = create_agent_graph(
        restaurant_id="default_trattoria",
        restaurant_name="Trattoria Bella Vista",
        llm=mock_llm,
        availability_service=availability_service,
        booking_service=booking_service,
        restaurant_service=restaurant_service,
        notification_service=notification_service,
    )

    state: AgentState = {
        "messages": [
            HumanMessage(
                content=f"Avete un tavolo per 4 per il {target_date.isoformat()} alle 20:00?"
            )
        ],
        "restaurant_id": "default_trattoria",
        "restaurant_name": "Trattoria Bella Vista",
        "caller_phone": "+39 333 5555555",
        "caller_name": "Paolo Neri",
        "current_date": date.today().isoformat(),
    }

    result = await agent.ainvoke(state)
    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 1
    assert "NON DISPONIBILE" in tool_messages[0].content
    assert "Orari alternativi disponibili" in tool_messages[0].content


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
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "get_restaurant_faq_or_hours",
                    "args": {"query": "parcheggio"},
                    "id": "call_faq",
                    "type": "tool_call",
                }
            ],
        ),
        AIMessage(
            content="Certamente! Abbiamo una convenzione con il Garage Garibaldi a 50 metri dal ristorante, con la prima ora gratuita."
        ),
    ]

    mock_llm = ScriptedMockLLM(responses)

    agent = create_agent_graph(
        restaurant_id="default_trattoria",
        restaurant_name="Trattoria Bella Vista",
        llm=mock_llm,
        availability_service=availability_service,
        booking_service=booking_service,
        restaurant_service=restaurant_service,
        notification_service=notification_service,
    )

    state: AgentState = {
        "messages": [
            HumanMessage(content="Buonasera, c'è un parcheggio vicino al locale?")
        ],
        "restaurant_id": "default_trattoria",
        "restaurant_name": "Trattoria Bella Vista",
        "caller_phone": "+39 333 7777777",
        "caller_name": "Elena",
        "current_date": date.today().isoformat(),
    }

    result = await agent.ainvoke(state)
    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 1
    assert "Garage Garibaldi" in tool_messages[0].content


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
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "end_call",
                    "args": {"farewell_message": "Grazie mille e buona serata!"},
                    "id": "call_end",
                    "type": "tool_call",
                }
            ],
        ),
        AIMessage(content="Grazie mille e buona serata! Arrivederci."),
    ]

    mock_llm = ScriptedMockLLM(responses)

    agent = create_agent_graph(
        restaurant_id="default_trattoria",
        restaurant_name="Trattoria Bella Vista",
        llm=mock_llm,
        availability_service=availability_service,
        booking_service=booking_service,
        restaurant_service=restaurant_service,
        notification_service=notification_service,
    )

    state: AgentState = {
        "messages": [HumanMessage(content="No grazie, a posto così. Buona serata!")],
        "restaurant_id": "default_trattoria",
        "restaurant_name": "Trattoria Bella Vista",
        "caller_phone": "+39 333 7777777",
        "caller_name": "Elena",
        "current_date": date.today().isoformat(),
    }

    result = await agent.ainvoke(state)
    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 1
    assert "CHIAMATA_TERMINATA" in tool_messages[0].content
