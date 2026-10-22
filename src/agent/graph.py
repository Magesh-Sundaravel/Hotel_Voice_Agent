from datetime import date
from typing import Any

from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from src.agent.prompts import get_system_prompt
from src.agent.state import AgentState
from src.config import settings
from src.repositories import (
    get_booking_repository,
    get_notification_repository,
    get_restaurant_repository,
)
from src.services.availability_service import AvailabilityService
from src.services.booking_service import BookingService
from src.services.notification_service import NotificationService
from src.services.restaurant_service import RestaurantService
from src.tools.booking_tools import build_tools


def create_agent_graph(
    restaurant_id: str = "default_trattoria",
    restaurant_name: str | None = None,
    llm=None,
    availability_service: AvailabilityService | None = None,
    booking_service: BookingService | None = None,
    restaurant_service: RestaurantService | None = None,
    notification_service: NotificationService | None = None,
    checkpointer: Any = None,
):
    # Repositories & Services setup
    restaurant_repo = get_restaurant_repository()
    booking_repo = get_booking_repository()
    notification_repo = get_notification_repository()

    avail_svc = availability_service or AvailabilityService(
        restaurant_repo, booking_repo
    )
    notif_svc = notification_service or NotificationService(notification_repo)
    rest_svc = restaurant_service or RestaurantService(restaurant_repo)
    book_svc = booking_service or BookingService(booking_repo, avail_svc, notif_svc)

    rest_name = restaurant_name or settings.DEFAULT_RESTAURANT_NAME

    # Tools
    tools = build_tools(
        restaurant_id=restaurant_id,
        availability_service=avail_svc,
        booking_service=book_svc,
        restaurant_service=rest_svc,
        notification_service=notif_svc,
    )

    # LLM setup
    if llm is None:
        if not settings.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is not set. Please provide it in .env or pass a mock LLM for testing."
            )
        llm = ChatGroq(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0.2,
        )

    llm_with_tools = llm.bind_tools(tools)

    async def call_model(state: AgentState):
        messages = list(state.get("messages", []))
        current_date = state.get("current_date") or date.today().isoformat()
        caller_phone = state.get("caller_phone") or "Non disponibile"

        sys_prompt = get_system_prompt(
            restaurant_name=rest_name,
            current_date=current_date,
            caller_phone=caller_phone,
        )

        # Prepend or update system message
        formatted_messages = [SystemMessage(content=sys_prompt)] + [
            m for m in messages if not isinstance(m, SystemMessage)
        ]

        response = await llm_with_tools.ainvoke(formatted_messages)
        return {"messages": [response]}

    # Graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")

    return workflow.compile(checkpointer=checkpointer)
