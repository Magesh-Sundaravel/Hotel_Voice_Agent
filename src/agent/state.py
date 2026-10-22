from typing import Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    hotel_id: str
    hotel_name: str
    restaurant_id: str
    restaurant_name: str
    caller_phone: str | None
    caller_name: str | None
    current_date: str  # YYYY-MM-DD in Europe/Rome
