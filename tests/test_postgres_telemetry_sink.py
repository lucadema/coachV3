import unittest
from unittest.mock import Mock

from backend.telemetry.postgres_sink import PostgresTelemetrySink


class FakeCursor:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.statements: list[tuple[str, tuple[object, ...] | list[object] | None]] = []

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(self, sql: str, params: tuple[object, ...] | list[object] | None = None) -> None:
        if self.fail:
            raise RuntimeError("database unavailable")

        self.statements.append((sql, params))


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self._cursor = cursor
        self.commit = Mock()
        self.rollback = Mock()
        self.close = Mock()

    def cursor(self) -> FakeCursor:
        return self._cursor


class PostgresTelemetrySinkTests(unittest.TestCase):
    def test_session_started_write_commits(self) -> None:
        cursor = FakeCursor()
        connection = FakeConnection(cursor)
        sink = PostgresTelemetrySink("postgresql://example")
        sink._connect = Mock(return_value=connection)  # type: ignore[method-assign]

        sink.record(
            {
                "event": "session_started",
                "session_id": "session-1",
                "stage": "classification",
                "turns_count": 0,
                "session_label": "luca",
                "pilot_id": "pilot-1",
            }
        )

        self.assertTrue(any("INSERT INTO coach_sessions" in sql for sql, _ in cursor.statements))
        session_insert = next(
            params for sql, params in cursor.statements if "INSERT INTO coach_sessions" in sql
        )
        self.assertIn("luca", session_insert or ())
        self.assertIn("pilot-1", session_insert or ())
        connection.commit.assert_called_once()
        connection.rollback.assert_not_called()
        connection.close.assert_called_once()

    def test_session_update_sets_missing_session_label_only(self) -> None:
        cursor = FakeCursor()
        connection = FakeConnection(cursor)
        sink = PostgresTelemetrySink("postgresql://example")
        sink._connect = Mock(return_value=connection)  # type: ignore[method-assign]

        sink.record(
            {
                "event": "session_updated",
                "session_id": "session-1",
                "stage": "coaching",
                "turns_count": 1,
                "session_label": "luca",
                "pilot_id": "pilot-1",
            }
        )

        update_sql = next(sql for sql, _ in cursor.statements if "UPDATE coach_sessions" in sql)
        self.assertIn("session_label = COALESCE(session_label, %s)", update_sql)
        self.assertIn("pilot_id = COALESCE(pilot_id, %s)", update_sql)
        connection.commit.assert_called_once()

    def test_session_update_sets_assessment_fields_without_overwrite(self) -> None:
        cursor = FakeCursor()
        connection = FakeConnection(cursor)
        sink = PostgresTelemetrySink("postgresql://example")
        sink._connect = Mock(return_value=connection)  # type: ignore[method-assign]

        sink.record(
            {
                "event": "session_updated",
                "session_id": "session-1",
                "stage": "synthesis",
                "turns_count": 4,
                "problem_category": "lack_of_clarity_alignment",
                "engagement_signal": "no_visible_risk",
            }
        )

        update_sql, update_params = next(
            (sql, params)
            for sql, params in cursor.statements
            if "UPDATE coach_sessions" in sql
        )
        self.assertIn("problem_category = COALESCE(problem_category, %s)", update_sql)
        self.assertIn("engagement_signal = COALESCE(engagement_signal, %s)", update_sql)
        self.assertIn("lack_of_clarity_alignment", update_params or ())
        self.assertIn("no_visible_risk", update_params or ())
        connection.commit.assert_called_once()

    def test_llm_call_write_inserts_usage_row(self) -> None:
        cursor = FakeCursor()
        connection = FakeConnection(cursor)
        sink = PostgresTelemetrySink("postgresql://example")
        sink._connect = Mock(return_value=connection)  # type: ignore[method-assign]

        sink.record(
            {
                "event": "llm_call",
                "session_id": "session-1",
                "llm_operation": "coaching.guiding.coaching",
                "provider": "openai",
                "success": True,
                "latency_ms": 123,
                "metadata": {"safe": True},
            }
        )

        self.assertTrue(any("INSERT INTO coach_llm_usage" in sql for sql, _ in cursor.statements))
        connection.commit.assert_called_once()
        connection.rollback.assert_not_called()
        connection.close.assert_called_once()

    def test_completed_session_close_sets_generated_output_flags(self) -> None:
        cursor = FakeCursor()
        connection = FakeConnection(cursor)
        sink = PostgresTelemetrySink("postgresql://example")
        sink._connect = Mock(return_value=connection)  # type: ignore[method-assign]

        sink.record(
            {
                "event": "session_closed",
                "session_id": "session-1",
                "stage": "closure",
                "turns_count": 8,
                "status": "completed",
            }
        )

        update_sql, update_params = next(
            (sql, params)
            for sql, params in cursor.statements
            if "closed_at = NOW()" in sql
        )
        self.assertIn("synthesis_generated = synthesis_generated OR", update_sql)
        self.assertIn("pathways_generated = pathways_generated OR", update_sql)
        self.assertEqual(
            update_params,
            ("completed", "closure", 8, "completed", "completed", None, "session-1"),
        )
        connection.commit.assert_called_once()

    def test_feedback_submitted_updates_feedback_columns(self) -> None:
        cursor = FakeCursor()
        connection = FakeConnection(cursor)
        sink = PostgresTelemetrySink("postgresql://example")
        sink._connect = Mock(return_value=connection)  # type: ignore[method-assign]

        sink.record(
            {
                "event": "feedback_submitted",
                "session_id": "session-1",
                "answer_1": True,
                "answer_2": False,
                "dropdown_values": ["Structured pathways"],
                "payload_keys": ["answer_1", "answer_2", "dropdown_values"],
            }
        )

        update_sql, update_params = next(
            (sql, params)
            for sql, params in cursor.statements
            if "feedback_submitted_at = NOW()" in sql
        )
        self.assertIn("feedback_answer_1 = %s", update_sql)
        self.assertEqual(update_params[0], True)
        self.assertEqual(update_params[1], False)
        self.assertEqual(update_params[2], ["Structured pathways"])
        self.assertEqual(
            update_params[3],
            '{"payload_keys": ["answer_1", "answer_2", "dropdown_values"]}',
        )
        connection.commit.assert_called_once()

    def test_database_errors_are_swallowed_and_rolled_back(self) -> None:
        cursor = FakeCursor(fail=True)
        connection = FakeConnection(cursor)
        sink = PostgresTelemetrySink("postgresql://example")
        sink._connect = Mock(return_value=connection)  # type: ignore[method-assign]

        with self.assertLogs("backend.telemetry.postgres_sink", level="WARNING"):
            sink.record(
                {
                    "event": "session_started",
                    "session_id": "session-1",
                    "stage": "classification",
                    "turns_count": 0,
                }
            )

        connection.commit.assert_not_called()
        connection.rollback.assert_called_once()
        connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
