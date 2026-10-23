"""Per-call session state for voice receptionists and chat sessions.

Holds caller identity, conversational messages, and booking state
without relying on LangGraph or external checkpointers.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CallSession:
    """Represents the context and state of an active caller or chat session."""

    call_id: str
    user_id: str
    caller_phone: str
    caller_name: str | None = None
    hotel_id: str = "sina_bernini_bristol"
    hotel_name: str = "Sina Bernini Bristol"
    messages: list[dict[str, Any]] = field(default_factory=list)
    collected_booking_fields: dict[str, Any] = field(default_factory=dict)
    read_back_confirmed: bool = False
    call_ended: bool = False
    last_reservation_code: str | None = None
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)

    def add_message(self, role: str, content: str | None = None, **kwargs: Any) -> None:
        """Appends a message to the conversation history in standard OpenAI format."""
        msg: dict[str, Any] = {"role": role, "content": content}
        for k, v in kwargs.items():
            if v is not None:
                msg[k] = v
        self.messages.append(msg)
        self.last_activity = time.time()

    def update_activity(self) -> None:
        """Refreshes the timestamp of last activity."""
        self.last_activity = time.time()


class SessionStore:
    """Thread-safe in-memory session manager for ongoing calls and chat sessions."""

    def __init__(self, ttl_seconds: float = 3600.0) -> None:
        self._sessions: dict[str, CallSession] = {}
        self._ttl_seconds = ttl_seconds

    def get_or_create(
        self,
        session_id: str,
        caller_phone: str | None = None,
        caller_name: str | None = None,
        hotel_id: str = "sina_bernini_bristol",
        hotel_name: str = "Sina Bernini Bristol",
        user_id: str | None = None,
    ) -> CallSession:
        """Retrieves an existing session or initializes a new one.

        Injects deterministic user_id and caller_phone that cannot be modified by the LLM.
        """
        self._cleanup_expired()
        session = self._sessions.get(session_id)
        if session is None:
            phone = caller_phone or "+39 000 0000000"
            computed_user_id = user_id or f"user_{phone.replace(' ', '').replace('+', '')}"
            session = CallSession(
                call_id=session_id,
                user_id=computed_user_id,
                caller_phone=phone,
                caller_name=caller_name,
                hotel_id=hotel_id,
                hotel_name=hotel_name,
            )
            self._sessions[session_id] = session
        else:
            if caller_phone and session.caller_phone == "+39 000 0000000":
                session.caller_phone = caller_phone
            if caller_name and not session.caller_name:
                session.caller_name = caller_name
            session.update_activity()
        return session

    def get(self, session_id: str) -> CallSession | None:
        """Retrieves a session if present and not expired."""
        session = self._sessions.get(session_id)
        if session and (time.time() - session.last_activity > self._ttl_seconds):
            self._sessions.pop(session_id, None)
            return None
        return session

    def delete(self, session_id: str) -> bool:
        """Removes a session from store."""
        return self._sessions.pop(session_id, None) is not None

    def _cleanup_expired(self) -> None:
        """Evicts sessions that exceeded the time-to-live."""
        now = time.time()
        expired = [
            sid
            for sid, s in self._sessions.items()
            if (now - s.last_activity) > self._ttl_seconds
        ]
        for sid in expired:
            self._sessions.pop(sid, None)
