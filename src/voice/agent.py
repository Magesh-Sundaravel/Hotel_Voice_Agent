"""Native voice agent running a single conversational LLM loop with native tool calling.

Replaces LangGraph StateGraph, ToolNode, and checkpointer with a single, fast async agent loop.
Runs inside the voice layer (src/voice) with zero dependencies on LangChain or LangGraph.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import Any

from src.agent.prompts import (
    format_date_italian,
    get_hotel_system_prompt,
    get_restaurant_system_prompt,
)
from src.config import settings
from src.integrations.email_service import EmailService
from src.integrations.twilio_service import TwilioService
from src.services.availability_service import AvailabilityService
from src.services.booking_service import BookingService
from src.services.guest_crm_service import GuestCRMService
from src.services.hotel_booking_service import HotelBookingService
from src.services.notification_service import NotificationService
from src.services.restaurant_service import RestaurantService
from src.voice.session import CallSession
from src.voice.tools import execute_tool_call, get_all_tool_schemas

logger = logging.getLogger(__name__)


class AgentTurnResult:
    """Outcome of a single conversational turn."""

    def __init__(
        self,
        reply_text: str,
        session: CallSession,
        call_ended: bool = False,
        reservation_code: str | None = None,
        tool_calls_executed: list[str] | None = None,
    ) -> None:
        self.reply_text = reply_text
        self.session = session
        self.call_ended = call_ended
        self.reservation_code = reservation_code
        self.tool_calls_executed = tool_calls_executed or []


class VoiceAgent:
    """Single LLM agent with native tool calling for voice telephony & chat."""

    def __init__(
        self,
        hotel_id: str = "sina_bernini_bristol",
        hotel_name: str = "Sina Bernini Bristol",
        llm: Any = None,
        hotel_booking_service: HotelBookingService | None = None,
        guest_crm_service: GuestCRMService | None = None,
        email_service: EmailService | None = None,
        twilio_service: TwilioService | None = None,
        availability_service: AvailabilityService | None = None,
        booking_service: BookingService | None = None,
        restaurant_service: RestaurantService | None = None,
        notification_service: NotificationService | None = None,
        max_tool_hops: int = 5,
    ) -> None:
        self.hotel_id = hotel_id
        self.hotel_name = hotel_name
        self.llm = llm
        self.hotel_booking_service = hotel_booking_service
        self.guest_crm_service = guest_crm_service
        self.email_service = email_service or EmailService()
        self.twilio_service = twilio_service or TwilioService()
        self.availability_service = availability_service
        self.booking_service = booking_service
        self.restaurant_service = restaurant_service
        self.notification_service = notification_service
        self.max_tool_hops = max_tool_hops

        is_restaurant_only = bool(
            (availability_service or booking_service) and not hotel_booking_service
        )
        self._tools = get_all_tool_schemas(
            include_restaurant=bool(availability_service or booking_service),
            include_hotel=not is_restaurant_only,
        )
        self._groq_client = None

    def _get_groq_client(self):
        """Initializes or returns cached native Groq client."""
        if self._groq_client is None:
            from groq import AsyncGroq

            if not settings.GROQ_API_KEY:
                raise ValueError(
                    "GROQ_API_KEY is not set. Please provide it in .env or pass a mock LLM."
                )
            self._groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        return self._groq_client

    async def _invoke_llm(self, formatted_messages: list[dict[str, Any]]) -> Any:
        """Invokes either a custom LLM (e.g. test mock) or native Groq AsyncGroq."""
        if self.llm is not None:
            # Handle mock LLM passed for testing
            if hasattr(self.llm, "ainvoke"):
                return await self.llm.ainvoke(formatted_messages)
            if callable(self.llm):
                return await self.llm(formatted_messages)
            return self.llm

        client = self._get_groq_client()
        return await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=formatted_messages,
            tools=self._tools,
            temperature=0.2,
        )

    def _extract_response_data(self, response: Any) -> tuple[str, list[dict[str, Any]]]:
        """Normalizes content string and tool calls across Groq API and test mock LLMs."""
        content = ""
        tool_calls: list[dict[str, Any]] = []

        # Groq native ChatCompletion
        if hasattr(response, "choices") and response.choices:
            msg = response.choices[0].message
            content = msg.content or ""
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    fn_name = getattr(tc.function, "name", "")
                    fn_args = getattr(tc.function, "arguments", "{}")
                    tool_calls.append(
                        {
                            "id": getattr(tc, "id", f"call_{fn_name}"),
                            "name": fn_name,
                            "args": fn_args,
                        }
                    )
            return content, tool_calls

        # Mock object with content and tool_calls attributes
        if hasattr(response, "content"):
            content = response.content or ""
        elif isinstance(response, dict) and "content" in response:
            content = response["content"] or ""

        raw_calls = getattr(response, "tool_calls", None)
        if raw_calls is None and isinstance(response, dict):
            raw_calls = response.get("tool_calls")

        if raw_calls:
            for tc in raw_calls:
                if isinstance(tc, dict):
                    name = tc.get("name") or tc.get("function", {}).get("name", "")
                    args = tc.get("args") or tc.get("function", {}).get("arguments", {})
                    call_id = tc.get("id", f"call_{name}")
                    tool_calls.append({"id": call_id, "name": name, "args": args})
                elif hasattr(tc, "function"):
                    tool_calls.append(
                        {
                            "id": getattr(tc, "id", f"call_{tc.function.name}"),
                            "name": tc.function.name,
                            "args": tc.function.arguments,
                        }
                    )

        return content, tool_calls

    async def run_turn(self, session: CallSession, user_message: str) -> AgentTurnResult:
        """Executes a single conversational turn in the voice/chat reception loop."""
        # 1. Append incoming caller message
        session.add_message(role="user", content=user_message)

        # 2. Format dynamic system prompt
        current_date = format_date_italian(date.today())
        is_restaurant = bool(
            (self.booking_service and not self.hotel_booking_service)
            or (session.hotel_id and "trattoria" in session.hotel_id.lower())
            or ("trattoria" in (session.hotel_name or self.hotel_name).lower())
            or ("ristorante" in (session.hotel_name or self.hotel_name).lower())
        )
        if is_restaurant:
            sys_prompt = get_restaurant_system_prompt(
                restaurant_name=session.hotel_name or self.hotel_name,
                current_date=current_date,
                caller_phone=session.caller_phone or "Non disponibile",
            )
        else:
            sys_prompt = get_hotel_system_prompt(
                hotel_name=session.hotel_name or self.hotel_name,
                current_date=current_date,
                caller_phone=session.caller_phone or "Non disponibile",
            )

        executed_tools: list[str] = []
        final_reply = "Certamente."

        # 3. Agent Tool Calling Loop
        for _hop in range(self.max_tool_hops):
            # Assemble full message history starting with system prompt
            formatted_messages = [{"role": "system", "content": sys_prompt}] + list(
                session.messages
            )

            try:
                llm_response = await self._invoke_llm(formatted_messages)
            except Exception as e:  # noqa: BLE001
                logger.error("LLM invocation error: %s", e)
                final_reply = "Mi scusi, si è verificato un errore di connessione. Può ripetere?"
                session.add_message(role="assistant", content=final_reply)
                return AgentTurnResult(
                    reply_text=final_reply,
                    session=session,
                    call_ended=session.call_ended,
                    reservation_code=session.last_reservation_code,
                    tool_calls_executed=executed_tools,
                )

            content, tool_calls = self._extract_response_data(llm_response)

            # If no tool calls, model provided conversational answer
            if not tool_calls:
                if content and content.strip():
                    final_reply = content.strip()
                session.add_message(role="assistant", content=final_reply)
                break

            # If tool calls are requested, execute them deterministically
            executed_any_tool = False
            session.add_message(
                role="assistant",
                content=content or None,
                tool_calls=[
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": tc["args"]
                            if isinstance(tc["args"], str)
                            else json.dumps(tc["args"]),
                        },
                    }
                    for tc in tool_calls
                ],
            )

            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                tool_id = tc["id"]
                executed_tools.append(tool_name)
                executed_any_tool = True

                logger.info("Executing native tool '%s' with args %s", tool_name, tool_args)
                tool_output = await execute_tool_call(
                    tool_name=tool_name,
                    raw_args=tool_args,
                    session=session,
                    hotel_booking_service=self.hotel_booking_service,
                    guest_crm_service=self.guest_crm_service,
                    email_service=self.email_service,
                    twilio_service=self.twilio_service,
                    availability_service=self.availability_service,
                    booking_service=self.booking_service,
                    restaurant_service=self.restaurant_service,
                    notification_service=self.notification_service,
                )

                session.add_message(
                    role="tool",
                    tool_call_id=tool_id,
                    name=tool_name,
                    content=tool_output,
                )

            if not executed_any_tool:
                break

        return AgentTurnResult(
            reply_text=final_reply,
            session=session,
            call_ended=session.call_ended,
            reservation_code=session.last_reservation_code,
            tool_calls_executed=executed_tools,
        )
