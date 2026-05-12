"""PostgreSQL telemetry sink.

This sink is deliberately best-effort. It catches all public ``record`` errors
so database availability can never affect the coaching flow.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any


logger = logging.getLogger(__name__)

DEFAULT_CONNECT_TIMEOUT_SECONDS = 2
DEFAULT_STATEMENT_TIMEOUT_MS = 2_000
DEFAULT_STAGE = "problem_submitted"


class PostgresTelemetrySink:
    """Persist safe telemetry records to PostgreSQL."""

    def __init__(
        self,
        database_url: str | None,
        *,
        connect_timeout_seconds: int = DEFAULT_CONNECT_TIMEOUT_SECONDS,
        statement_timeout_ms: int = DEFAULT_STATEMENT_TIMEOUT_MS,
    ) -> None:
        self.database_url = database_url
        self.connect_timeout_seconds = connect_timeout_seconds
        self.statement_timeout_ms = statement_timeout_ms

    def record(self, payload: dict[str, Any]) -> None:
        """Write a telemetry payload if possible, swallowing all failures."""
        try:
            if not self.database_url:
                logger.warning(
                    "Postgres telemetry sink requested without TELEMETRY_DATABASE_URL; "
                    "skipping telemetry write"
                )
                return None

            event = str(payload.get("event") or "")
            if event == "session_started":
                self._record_session_started(payload)
            elif event == "session_updated":
                self._record_session_updated(payload)
            elif event == "session_closed":
                self._record_session_closed(payload)
            elif event == "feedback_submitted":
                self._record_feedback_submitted(payload)
            elif event == "llm_call":
                self._record_llm_call(payload)
            else:
                logger.warning("Postgres telemetry skipped unsupported event=%s", event)
        except Exception as exc:
            logger.warning(
                "Postgres telemetry write failed event=%s error_type=%s error=%s",
                str(payload.get("event") or "unknown"),
                type(exc).__name__,
                _truncate(str(exc)),
            )
        return None

    def _connect(self) -> Any:
        try:
            import psycopg
        except Exception as exc:  # pragma: no cover - depends on environment
            raise RuntimeError("psycopg_unavailable") from exc

        return psycopg.connect(
            self.database_url,
            connect_timeout=self.connect_timeout_seconds,
            options=f"-c statement_timeout={self.statement_timeout_ms}",
        )

    def _write(self, writer: Callable[[Any], None]) -> None:
        conn = None
        try:
            conn = self._connect()
            with conn.cursor() as cursor:
                writer(cursor)
            conn.commit()
        except Exception:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
            raise
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def _ensure_session(self, cursor: Any, session_id: str, stage: str = DEFAULT_STAGE) -> None:
        cursor.execute(
            """
            INSERT INTO coach_sessions (app_session_id, current_stage)
            VALUES (%s, %s)
            ON CONFLICT (app_session_id) DO NOTHING
            """,
            (session_id, stage),
        )

    def _record_session_started(self, payload: dict[str, Any]) -> None:
        session_id = _safe_string(payload.get("session_id"))
        if not session_id:
            logger.warning("Postgres telemetry skipped session_started without session_id")
            return None

        stage = _stage(payload)
        turns_count = _nonnegative_int(payload.get("turns_count"), default=0)

        def writer(cursor: Any) -> None:
            cursor.execute(
                """
                INSERT INTO coach_sessions (
                    app_session_id,
                    started_at,
                    last_interaction_at,
                    status,
                    current_stage,
                    turns_count,
                    updated_at
                )
                VALUES (%s, NOW(), NOW(), 'active', %s, %s, NOW())
                ON CONFLICT (app_session_id) DO UPDATE SET
                    last_interaction_at = NOW(),
                    status = 'active',
                    current_stage = EXCLUDED.current_stage,
                    turns_count = EXCLUDED.turns_count,
                    updated_at = NOW()
                """,
                (session_id, stage, turns_count),
            )

        self._write(writer)
        return None

    def _record_session_updated(self, payload: dict[str, Any]) -> None:
        session_id = _safe_string(payload.get("session_id"))
        if not session_id:
            logger.warning("Postgres telemetry skipped session_updated without session_id")
            return None

        stage = _stage(payload)
        turns_count = _nonnegative_int(payload.get("turns_count"), default=0)
        status = _safe_string(payload.get("status"))

        assignments: list[str] = [
            "last_interaction_at = NOW()",
            "current_stage = %s",
            "turns_count = %s",
            "updated_at = NOW()",
        ]
        params: list[Any] = [stage, turns_count]

        if status:
            assignments.append("status = %s")
            params.append(status)

        for column, key in (
            ("synthesis_generated", "synthesis_generated"),
            ("pathways_generated", "pathways_generated"),
            ("pdf_downloaded", "pdf_downloaded"),
        ):
            value = _bool_or_none(payload.get(key))
            if value is not None:
                assignments.append(f"{column} = %s")
                params.append(value)

        params.append(session_id)

        def writer(cursor: Any) -> None:
            self._ensure_session(cursor, session_id, stage)
            cursor.execute(
                f"""
                UPDATE coach_sessions
                SET {", ".join(assignments)}
                WHERE app_session_id = %s
                """,
                params,
            )

        self._write(writer)
        return None

    def _record_session_closed(self, payload: dict[str, Any]) -> None:
        session_id = _safe_string(payload.get("session_id"))
        if not session_id:
            logger.warning("Postgres telemetry skipped session_closed without session_id")
            return None

        stage = _stage(payload)
        turns_count = _nonnegative_int(payload.get("turns_count"), default=0)
        status = _safe_string(payload.get("status")) or "completed"

        def writer(cursor: Any) -> None:
            self._ensure_session(cursor, session_id, stage)
            cursor.execute(
                """
                UPDATE coach_sessions
                SET
                    status = %s,
                    closed_at = NOW(),
                    last_interaction_at = NOW(),
                    current_stage = %s,
                    turns_count = %s,
                    updated_at = NOW()
                WHERE app_session_id = %s
                """,
                (status, stage, turns_count, session_id),
            )

        self._write(writer)
        return None

    def _record_feedback_submitted(self, payload: dict[str, Any]) -> None:
        session_id = _safe_string(payload.get("session_id"))
        if not session_id:
            logger.warning("Postgres telemetry skipped feedback_submitted without session_id")
            return None

        feedback_payload = _feedback_payload_json(payload)

        def writer(cursor: Any) -> None:
            self._ensure_session(cursor, session_id)
            cursor.execute(
                """
                UPDATE coach_sessions
                SET
                    feedback_submitted_at = NOW(),
                    feedback_answer_1 = %s,
                    feedback_answer_2 = %s,
                    feedback_dropdown_values = %s,
                    feedback_payload = %s::jsonb,
                    updated_at = NOW()
                WHERE app_session_id = %s
                """,
                (
                    _bool_or_none(payload.get("answer_1")),
                    _bool_or_none(payload.get("answer_2")),
                    _string_list_or_none(payload.get("dropdown_values")),
                    feedback_payload,
                    session_id,
                ),
            )

        self._write(writer)
        return None

    def _record_llm_call(self, payload: dict[str, Any]) -> None:
        session_id = _safe_string(payload.get("session_id"))
        if not session_id:
            logger.warning("Postgres telemetry skipped llm_call without session_id")
            return None

        metadata_json = _json_or_none(payload.get("metadata"))

        def writer(cursor: Any) -> None:
            self._ensure_session(cursor, session_id)
            cursor.execute(
                """
                INSERT INTO coach_llm_usage (
                    app_session_id,
                    llm_operation,
                    provider,
                    model,
                    input_tokens,
                    output_tokens,
                    total_tokens,
                    cached_input_tokens,
                    reasoning_tokens,
                    success,
                    latency_ms,
                    error_type,
                    error_message,
                    metadata
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb
                )
                """,
                (
                    session_id,
                    _safe_string(payload.get("llm_operation")) or "unknown",
                    _safe_string(payload.get("provider")) or "openai",
                    _safe_string(payload.get("model")),
                    _int_or_none(payload.get("input_tokens")),
                    _int_or_none(payload.get("output_tokens")),
                    _int_or_none(payload.get("total_tokens")),
                    _int_or_none(payload.get("cached_input_tokens")),
                    _int_or_none(payload.get("reasoning_tokens")),
                    _bool_or_default(payload.get("success"), default=True),
                    _int_or_none(payload.get("latency_ms")),
                    _safe_string(payload.get("error_type")),
                    _safe_string(payload.get("error_message")),
                    metadata_json,
                ),
            )

        self._write(writer)
        return None


def _stage(payload: dict[str, Any]) -> str:
    return _safe_string(payload.get("stage")) or DEFAULT_STAGE


def _safe_string(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _truncate(value: str, max_length: int = 300) -> str:
    if len(value) <= max_length:
        return value

    return f"{value[:max_length]}..."


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None

    if isinstance(value, int) and value >= 0:
        return value

    return None


def _nonnegative_int(value: Any, *, default: int) -> int:
    parsed = _int_or_none(value)
    return parsed if parsed is not None else default


def _bool_or_none(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value

    return None


def _bool_or_default(value: Any, *, default: bool) -> bool:
    parsed = _bool_or_none(value)
    return parsed if parsed is not None else default


def _string_list_or_none(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None

    strings = [str(item) for item in value if item is not None]
    return strings or None


def _json_or_none(value: Any) -> str | None:
    if value is None:
        return None

    return json.dumps(value, default=str)


def _feedback_payload_json(payload: dict[str, Any]) -> str | None:
    payload_keys = payload.get("payload_keys")
    if not payload_keys:
        return None

    return _json_or_none({"payload_keys": _string_list_or_none(payload_keys)})
