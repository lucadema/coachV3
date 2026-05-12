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
            }
        )

        self.assertTrue(any("INSERT INTO coach_sessions" in sql for sql, _ in cursor.statements))
        connection.commit.assert_called_once()
        connection.rollback.assert_not_called()
        connection.close.assert_called_once()

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
