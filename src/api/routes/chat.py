import re
from datetime import date

from fastapi import APIRouter, HTTPException, Request
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import BaseModel, Field

from src.agent.checkpointer import get_memory_checkpointer
from src.agent.graph import create_agent_graph
from src.agent.prompts import format_date_italian
from src.agent.state import AgentState

router = APIRouter(prefix="/api", tags=["Voice & Chat Agent"])


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


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(req: ChatRequest, request: Request):
    checkpointer = (
        getattr(getattr(request.app, "state", None), "checkpointer", None)
        or get_memory_checkpointer()
    )

    try:
        agent = create_agent_graph(
            hotel_id=req.hotel_id,
            hotel_name=req.hotel_name,
            checkpointer=checkpointer,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to initialize agent: {e!s}"
        ) from e

    input_state: AgentState = {
        "messages": [HumanMessage(content=req.message)],
        "hotel_id": req.hotel_id,
        "hotel_name": req.hotel_name,
        "caller_phone": req.caller_phone,
        "caller_name": req.caller_name,
        "current_date": format_date_italian(date.today()),
    }

    config = {"configurable": {"thread_id": req.session_id}}
    result = await agent.ainvoke(input_state, config=config)
    updated_messages = result.get("messages", [])

    call_ended = False
    reservation_code = None
    last_ai = None

    for m in reversed(updated_messages):
        if last_ai is None and isinstance(m, AIMessage) and m.content:
            last_ai = m.content

    for m in updated_messages:
        if isinstance(m, ToolMessage):
            if m.name == "end_call":
                call_ended = True
            if m.name in ["create_hotel_room_booking", "create_reservation"] and m.content:
                match = re.search(r"SINA-\d{4}", m.content)
                if match:
                    reservation_code = match.group(0)

    return ChatResponse(
        session_id=req.session_id,
        response=last_ai or "Come posso esserLe utile da Sina Hotels?",
        history_length=len(updated_messages),
        call_ended=call_ended,
        reservation_code=reservation_code,
    )


@router.delete("/chat/{session_id}")
async def reset_session(session_id: str, request: Request):
    checkpointer = (
        getattr(getattr(request.app, "state", None), "checkpointer", None)
        or get_memory_checkpointer()
    )
    if hasattr(checkpointer, "adelete_thread"):
        await checkpointer.adelete_thread(session_id)
    elif hasattr(checkpointer, "delete_thread"):
        checkpointer.delete_thread(session_id)
    return {
        "status": "ok",
        "message": f"Session {session_id} reset successfully",
    }
