from datetime import date

from fastapi import APIRouter, HTTPException, Request
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field

from src.agent.checkpointer import get_memory_checkpointer
from src.agent.graph import create_agent_graph
from src.agent.state import AgentState

router = APIRouter(prefix="/api", tags=["Voice & Chat Agent"])


class ChatRequest(BaseModel):
    session_id: str = Field(
        description="Unique session ID per phone call or chat session"
    )
    message: str = Field(description="Caller input text in Italian")
    caller_phone: str | None = "+39 333 0000000"
    caller_name: str | None = None
    restaurant_id: str = "default_trattoria"


class ChatResponse(BaseModel):
    session_id: str
    response: str
    history_length: int


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(req: ChatRequest, request: Request):
    checkpointer = (
        getattr(getattr(request.app, "state", None), "checkpointer", None)
        or get_memory_checkpointer()
    )

    try:
        agent = create_agent_graph(
            restaurant_id=req.restaurant_id,
            checkpointer=checkpointer,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to initialize agent: {e!s}"
        ) from e

    input_state: AgentState = {
        "messages": [HumanMessage(content=req.message)],
        "restaurant_id": req.restaurant_id,
        "restaurant_name": "Trattoria Bella Vista",
        "caller_phone": req.caller_phone,
        "caller_name": req.caller_name,
        "current_date": date.today().isoformat(),
    }

    config = {"configurable": {"thread_id": req.session_id}}
    result = await agent.ainvoke(input_state, config=config)
    updated_messages = result.get("messages", [])

    last_ai = None
    for m in reversed(updated_messages):
        if isinstance(m, AIMessage) and m.content:
            last_ai = m.content
            break

    return ChatResponse(
        session_id=req.session_id,
        response=last_ai or "Come posso esserLe utile?",
        history_length=len(updated_messages),
    )


@router.delete("/chat/{session_id}")
async def reset_session(session_id: str):
    return {"status": "ok", "message": "Session reset"}
