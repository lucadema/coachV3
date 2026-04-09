"""
SQLite-backed session state store for Coach V3.

This stays intentionally minimal while avoiding session loss on backend reloads
or process restarts.
"""

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from backend.models import Session


class StateStore:
    """Minimal persistent session storage."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
        resolved_path = db_path or os.getenv("COACHV3_STATE_DB_PATH")
        self.db_path = Path(
            resolved_path or Path(__file__).resolve().parents[1] / ".coachv3_state.sqlite3"
        )
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        """Create a SQLite connection for one short-lived store operation."""
        return sqlite3.connect(self.db_path, timeout=30.0)

    def _ensure_schema(self) -> None:
        """Create the sessions table on first use."""
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    session_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def save_session(self, session: Session) -> Session:
        """Insert or replace a session in the store."""
        session.updated_at = datetime.now(timezone.utc)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO sessions (session_id, session_json, updated_at)
                VALUES (?, ?, ?)
                """,
                (
                    session.session_id,
                    session.model_dump_json(),
                    session.updated_at.isoformat(),
                ),
            )
            connection.commit()
        return session

    def get_session(self, session_id: str) -> Session | None:
        """Return a session if it exists, otherwise None."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT session_json FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()

        if row is None:
            return None

        return Session.model_validate_json(row[0])

    def has_session(self, session_id: str) -> bool:
        """Return True if the session exists in the store."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return row is not None

    def delete_session(self, session_id: str) -> None:
        """Remove a session if it exists."""
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM sessions WHERE session_id = ?",
                (session_id,),
            )
            connection.commit()

    def clear(self) -> None:
        """Clear all sessions from the store."""
        with self._connect() as connection:
            connection.execute("DELETE FROM sessions")
            connection.commit()


state_store = StateStore()
