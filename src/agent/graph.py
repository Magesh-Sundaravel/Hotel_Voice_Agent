from datetime import date
from typing import Any

from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from src.agent.prompts import format_date_italian, get_hotel_system_prompt
from src.agent.state import AgentState
from src.config import settings
from src.integrations.email_service import EmailService
from src.integrations.twilio_service import TwilioService
from src.repositories import (
    get_booking_repository,
    get_guest_crm_repository,
    get_hotel_room_repository,
    get_notification_repository,
    get_restaurant_repository,
)
from src.services.availability_service import AvailabilityService
from src.services.booking_service import BookingService
from src.services.guest_crm_service import GuestCRMService
from src.services.hotel_booking_service import HotelBookingService
from src.services.notification_service import NotificationService
from src.services.restaurant_service import RestaurantService
from src.tools.booking_tools import build_tools
from src.tools.communication_tools import build_communication_tools
from src.tools.crm_tools import build_crm_tools
from src.tools.hotel_room_tools import build_hotel_room_tools


def create_agent_graph(
    hotel_id: str = "sina_bernini_bristol",
    hotel_name: str = "Sina Bernini Bristol",
    restaurant_id: str | None = None,
    restaurant_name: str | None = None,
    llm=None,
    hotel_booking_service: HotelBookingService | None = None,
    guest_crm_service: GuestCRMService | None = None,
    availability_service: AvailabilityService | None = None,
    booking_service: BookingService | None = None,
    restaurant_service: RestaurantService | None = None,
    notification_service: NotificationService | None = None,
    email_service: EmailService | None = None,
    twilio_service: TwilioService | None = None,
    checkpointer: Any = None,
):
    # Repositories setup
    hotel_room_repo = get_hotel_room_repository()
    notification_repo = get_notification_repository()
    guest_crm_repo = get_guest_crm_repository()
    restaurant_repo = get_restaurant_repository()
    booking_repo = get_booking_repository()

    effective_hotel_id = hotel_id or restaurant_id or "sina_bernini_bristol"
    effective_hotel_name = hotel_name or restaurant_name or "Sina Bernini Bristol"

    e_svc = email_service or EmailService()
    t_svc = twilio_service or TwilioService()

    crm_svc = guest_crm_service or GuestCRMService(
        crm_repo=guest_crm_repo,
        notification_repo=notification_repo,
        default_hotel_id=effective_hotel_id,
    )

    h_booking_svc = hotel_booking_service or HotelBookingService(
        room_repo=hotel_room_repo,
        notification_repo=notification_repo,
        guest_crm_service=crm_svc,
        twilio_service=t_svc,
        email_service=e_svc,
        hotel_id=effective_hotel_id,
    )

    # Core Sina Hotel Room, CRM, and Communication Tools
    tools = (
        build_hotel_room_tools(h_booking_svc)
        + build_crm_tools(crm_svc)
        + build_communication_tools(email_service=e_svc, twilio_service=t_svc)
    )

    # Support legacy restaurant tools if services are passed in
    if availability_service or booking_service:
        avail_s = availability_service or AvailabilityService(restaurant_repo, booking_repo)
        notif_s = notification_service or NotificationService(notification_repo)
        rest_s = restaurant_service or RestaurantService(restaurant_repo)
        b_s = booking_service or BookingService(booking_repo, avail_s, notif_s)
        legacy_tools = build_tools(
            restaurant_id=restaurant_id or effective_hotel_id,
            availability_service=avail_s,
            booking_service=b_s,
            restaurant_service=rest_s,
            notification_service=notif_s,
        )
        tools += legacy_tools

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
        raw_date = state.get("current_date")
        if not raw_date:
            current_date = format_date_italian(date.today())
        elif "(" not in raw_date:
            try:
                parsed_d = date.fromisoformat(raw_date)
                current_date = format_date_italian(parsed_d)
            except (ValueError, TypeError):
                current_date = raw_date
        else:
            current_date = raw_date

        caller_phone = state.get("caller_phone") or "Non disponibile"

        sys_prompt = get_hotel_system_prompt(
            hotel_name=effective_hotel_name,
            current_date=current_date,
            caller_phone=caller_phone,
        )

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
