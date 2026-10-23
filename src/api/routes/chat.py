"""Chat route supporting real-time web chat with native VoiceAgent.

Maintains multi-turn sessions in SessionStore without LangGraph or Postgres checkpointer.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.voice.agent import VoiceAgent
from src.voice.session import SessionStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Voice & Chat Agent"])

# Global session store for chat/web sessions
chat_session_store = SessionStore(ttl_seconds=3600.0)


class ChatRequest(BaseModel):
    session_id: str = Field(
        description="Unique session ID per phone call or chat session"
    )
    message: str = Field(description="Caller input text in Italian")
    caller_phone: str | None = "+39 333 0000000"
    caller_name: str | None = None
    hotel_id: str = "sina_bernini_bristol"
    hotel_name: str = "Sina Bernini Bristol"


class ChatResponse(BaseModel):
    session_id: str
    response: str
    history_length: int
    call_ended: bool = Field(
        default=False,
        description="True if the conversation reached a natural wrap-up and end_call tool was executed.",
    )
    reservation_code: str | None = Field(
        default=None,
        description="Confirmed reservation reference code (e.g. 'SINA-4020') if created during call.",
    )


def _get_agent(request: Request, req: ChatRequest) -> VoiceAgent:
    """Gets agent from app state or instantiates one."""
    agent = getattr(getattr(request.app, "state", None), "voice_agent", None)
    if agent is None:
        agent = getattr(getattr(request.app, "state", None), "agent_graph", None)
    if agent is None:
        try:
            agent = VoiceAgent(
                hotel_id=req.hotel_id,
                hotel_name=req.hotel_name,
                hotel_booking_service=getattr(getattr(request.app, "state", None), "hotel_booking_service", None),
                guest_crm_service=getattr(getattr(request.app, "state", None), "crm_service", None),
                availability_service=getattr(getattr(request.app, "state", None), "availability_service", None),
                booking_service=getattr(getattr(request.app, "state", None), "booking_service", None),
                restaurant_service=getattr(getattr(request.app, "state", None), "restaurant_service", None),
                notification_service=getattr(getattr(request.app, "state", None), "notification_service", None),
                email_service=getattr(getattr(request.app, "state", None), "email_service", None),
                twilio_service=getattr(getattr(request.app, "state", None), "twilio_service", None),
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to initialize voice agent: {e!s}"
            ) from e
    return agent


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(req: ChatRequest, request: Request):
    agent = _get_agent(request, req)

    # Retrieve or create session with deterministic identity injection
    session = chat_session_store.get_or_create(
        session_id=req.session_id,
        caller_phone=req.caller_phone or "+39 333 0000000",
        caller_name=req.caller_name,
        hotel_id=req.hotel_id,
        hotel_name=req.hotel_name,
    )

    if not hasattr(agent, "run_turn"):
        raise HTTPException(status_code=500, detail="Incompatible agent interface.")

    result = await agent.run_turn(session=session, user_message=req.message)

    return ChatResponse(
        session_id=req.session_id,
        response=result.reply_text,
        history_length=len(session.messages),
        call_ended=result.call_ended,
        reservation_code=result.reservation_code,
    )


@router.delete("/chat/{session_id}")
async def reset_session(session_id: str, request: Request):
    # Reset in SessionStore
    deleted = chat_session_store.delete(session_id)
    return {
        "status": "ok",
        "message": f"Session {session_id} reset successfully (existed={deleted})",
    }
