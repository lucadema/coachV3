import io
import json
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from backend.telemetry import service


class TelemetryServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        service._WARNED_KEYS.clear()

    def test_console_sink_emits_prefixed_json(self) -> None:
        with patch.dict(
            os.environ,
            {"TELEMETRY_ENABLED": "true", "TELEMETRY_SINK": "console"},
            clear=True,
        ):
            output = io.StringIO()
            with redirect_stdout(output):
                service.record_session_started(
                    session_id="session-1",
                    stage="classification",
                    state="evaluating",
                    turns_count=0,
                )

        line = output.getvalue().strip()
        self.assertTrue(line.startswith("TELEMETRY "))
        payload = json.loads(line.removeprefix("TELEMETRY "))
        self.assertEqual(payload["event"], "session_started")
        self.assertEqual(payload["session_id"], "session-1")
        self.assertEqual(payload["stage"], "classification")
        self.assertEqual(payload["turns_count"], 0)
        self.assertIn("timestamp", payload)

    def test_console_sink_emits_session_label_when_present(self) -> None:
        with patch.dict(
            os.environ,
            {"TELEMETRY_ENABLED": "true", "TELEMETRY_SINK": "console"},
            clear=True,
        ):
            output = io.StringIO()
            with redirect_stdout(output):
                service.record_session_started(
                    session_id="session-1",
                    stage="classification",
                    state="evaluating",
                    turns_count=0,
                    session_label="luca",
                )

        payload = json.loads(output.getvalue().strip().removeprefix("TELEMETRY "))
        self.assertEqual(payload["session_label"], "luca")

    def test_disabled_telemetry_emits_nothing(self) -> None:
        with patch.dict(os.environ, {"TELEMETRY_ENABLED": "false"}, clear=True):
            output = io.StringIO()
            with redirect_stdout(output):
                service.record_session_started(
                    session_id="session-1",
                    stage="classification",
                    state="evaluating",
                    turns_count=0,
                )

        self.assertEqual(output.getvalue(), "")

    def test_noop_sink_emits_nothing(self) -> None:
        with patch.dict(
            os.environ,
            {"TELEMETRY_ENABLED": "true", "TELEMETRY_SINK": "noop"},
            clear=True,
        ):
            output = io.StringIO()
            with redirect_stdout(output):
                service.record_session_started(
                    session_id="session-1",
                    stage="classification",
                    state="evaluating",
                    turns_count=0,
                )

        self.assertEqual(output.getvalue(), "")

    def test_postgres_sink_without_database_url_is_safe_noop(self) -> None:
        with patch.dict(
            os.environ,
            {"TELEMETRY_ENABLED": "true", "TELEMETRY_SINK": "postgres"},
            clear=True,
        ):
            output = io.StringIO()
            with self.assertLogs("backend.telemetry.service", level="WARNING") as logs:
                with redirect_stdout(output):
                    service.record_session_started(
                        session_id="session-1",
                        stage="classification",
                        state="evaluating",
                        turns_count=0,
                    )

        self.assertEqual(output.getvalue(), "")
        self.assertIn("TELEMETRY_DATABASE_URL", "\n".join(logs.output))

    def test_llm_metadata_drops_blocked_content_keys(self) -> None:
        with patch.dict(
            os.environ,
            {"TELEMETRY_ENABLED": "true", "TELEMETRY_SINK": "console"},
            clear=True,
        ):
            output = io.StringIO()
            with redirect_stdout(output):
                service.record_llm_call(
                    session_id="session-1",
                    llm_operation="coaching.guiding.coaching",
                    metadata={
                        "prompt": "do not emit",
                        "raw_output": "do not emit",
                        "safe_count": 2,
                    },
                )

        payload = json.loads(output.getvalue().strip().removeprefix("TELEMETRY "))
        self.assertEqual(payload["metadata"], {"safe_count": 2})


if __name__ == "__main__":
    unittest.main()
