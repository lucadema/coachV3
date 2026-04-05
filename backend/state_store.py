"""
Simple in-memory session state store for Coach V3.

This is intentionally minimal for the POC.
"""

from datetime import datetime, timezone

from backend.models import Session


class StateStore:
    """Simple in-memory session storage."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def save_session(self, session: Session) -> Session:
        """Insert or replace a session in the store."""
        session.updated_at = datetime.now(timezone.utc)
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Session | None:
        """Return a session if it exists, otherwise None."""
        return self._sessions.get(session_id)

    def has_session(self, session_id: str) -> bool:
        """Return True if the session exists in the store."""
        return session_id in self._sessions

    def delete_session(self, session_id: str) -> None:
        """Remove a session if it exists."""
        self._sessions.pop(session_id, None)

    def clear(self) -> None:
        """Clear all sessions from the store."""
        self._sessions.clear()


state_store = StateStore()
