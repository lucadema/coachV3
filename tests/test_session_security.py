import os
import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.api import app
from backend.controller import handle_user_msg, init_session
from backend.enums import Stage
from backend.models import Session
from backend.session_security import DEBUG_DISABLED_MESSAGE, short_session_ref
from backend.state_store import StateStore, state_store


class StateStoreSecurityTests(unittest.TestCase):
    def test_session_initialization_persists_session(self) -> None:
        with patch.dict(os.environ, {"GLIMPSE_DEBUG_PERSISTENCE": "false"}):
            state_store.clear()
            session = init_session(session_id="persisted-session")

            restored = state_store.get_session(session.session_id)

            self.assertIsNotNone(restored)
            self.assertEqual(restored.session_id, "persisted-session")
            self.assertEqual(restored.stage, Stage.CLASSIFICATION.value)
            state_store.clear()

    def test_separate_session_ids_remain_isolated(self) -> None:
        with patch.dict(os.environ, {"GLIMPSE_DEBUG_PERSISTENCE": "false"}):
            state_store.clear()
            first = init_session(session_id="session-a")
            second = init_session(session_id="session-b")

            self.assertNotEqual(first.session_id, second.session_id)
            self.assertEqual(state_store.get_session("session-a").session_id, "session-a")
            self.assertEqual(state_store.get_session("session-b").session_id, "session-b")
            state_store.clear()

    def test_delete_session_removes_row(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = StateStore(Path(temp_dir) / "state.sqlite3")
            store.save_session(
                Session(
                    session_id="delete-me",
                    stage=Stage.CLASSIFICATION.value,
                    state="evaluating",
                )
            )

            deleted = store.delete_session("delete-me")

            self.assertEqual(deleted, 1)
            self.assertIsNone(store.get_session("delete-me"))
            self.assertEqual(store.delete_session("delete-me"), 0)

    def test_cleanup_expired_sessions_removes_old_rows_only(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = StateStore(Path(temp_dir) / "state.sqlite3")
            now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
            store.save_session(
                Session(
                    session_id="old-session",
                    stage=Stage.CLASSIFICATION.value,
                    state="evaluating",
                )
            )
            store.save_session(
                Session(
                    session_id="active-session",
                    stage=Stage.CLASSIFICATION.value,
                    state="evaluating",
                )
            )

            with closing(store._connect()) as connection:
                connection.execute(
                    "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                    ((now - timedelta(minutes=300)).isoformat(), "old-session"),
                )
                connection.execute(
                    "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                    ((now - timedelta(minutes=30)).isoformat(), "active-session"),
                )
                connection.commit()

            deleted = store.cleanup_expired_sessions(240, now=now)

            self.assertEqual(deleted, 1)
            self.assertIsNone(store.get_session("old-session"))
            self.assertIsNotNone(store.get_session("active-session"))


class DebugSecurityTests(unittest.TestCase):
    def tearDown(self) -> None:
        state_store.clear()

    def test_default_debug_persistence_does_not_store_full_prompt_debug(self) -> None:
        raw_user_text = "I need to resolve a decision with my team at work."
        with patch.dict(os.environ, {"GLIMPSE_DEBUG_PERSISTENCE": "false"}):
            state_store.clear()
            session = init_session(session_id="debug-session")

            handle_user_msg(session.session_id, raw_user_text)
            stored = state_store.get_session(session.session_id)

            self.assertIsNotNone(stored)
            self.assertEqual(stored.debug_message, DEBUG_DISABLED_MESSAGE)
            self.assertNotIn(raw_user_text, stored.debug_message or "")
            self.assertNotIn("prompt_full", stored.debug_message or "")
            self.assertNotIn("llm_reply_raw", stored.debug_message or "")

    def test_debug_trace_is_sanitized_by_default(self) -> None:
        with patch.dict(os.environ, {"GLIMPSE_DEBUG_PERSISTENCE": "false"}):
            state_store.clear()
            state_store.save_session(
                Session(
                    session_id="debug-trace-session",
                    stage=Stage.COACHING.value,
                    state="guiding",
                    user_message="raw user text",
                    evaluation_message="raw evaluation",
                    coach_message="raw coach text",
                    debug_message="evaluation_prompt_full_begin\nraw user text",
                    stage_context={"sensitive": "raw context"},
                )
            )
            client = TestClient(app)

            response = client.get("/debug_trace/debug-trace-session")

            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertIsNone(body["user_message"])
            self.assertIsNone(body["evaluation_message"])
            self.assertIsNone(body["coach_message"])
            self.assertEqual(body["debug_message"], DEBUG_DISABLED_MESSAGE)
            self.assertEqual(body["stage_context"], {})

    def test_short_session_ref_does_not_expose_full_session_id(self) -> None:
        session_id = "session-with-a-long-sensitive-identifier"

        session_ref = short_session_ref(session_id)

        self.assertNotEqual(session_ref, session_id)
        self.assertNotIn(session_id, session_ref)
        self.assertEqual(len(session_ref), 12)


if __name__ == "__main__":
    unittest.main()
