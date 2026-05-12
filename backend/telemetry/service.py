"""Safe telemetry service facade for CoachV3.

Telemetry is deliberately non-critical. Every public function in this module
catches all exceptions and returns ``None`` so instrumentation cannot affect the
coaching flow.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from backend.telemetry.postgres_sink import PostgresTelemetrySink
from backend.telemetry.sinks import ConsoleTelemetrySink, NoopTelemetrySink


logger = logging.getLogger(__name__)
TRUTHY_VALUES = {"1", "true", "yes", "on"}
FALSY_VALUES = {"0", "false", "no", "off"}
MAX_ERROR_MESSAGE_LENGTH = 300
BLOCKED_METADATA_KEYS = {
    "context",
    "coach_message",
    "debug_message",
    "evaluation_message",
    "history",
    "output_instruction",
    "prompt",
    "raw_output",
    "user_message",
}
_WARNED_KEYS: set[str] = set()


def _telemetry_enabled() -> bool:
    value = os.getenv("TELEMETRY_ENABLED")

    if value is None:
        return True

    normalized = value.strip().lower()

    if normalized in FALSY_VALUES:
        return False

    if normalized in TRUTHY_VALUES:
        return True

    return True


def _warn_once(key: str, message: str) -> None:
    if key in _WARNED_KEYS:
        return None

    _WARNED_KEYS.add(key)
    logger.warning(message)
    return None


def _get_sink() -> ConsoleTelemetrySink | NoopTelemetrySink | PostgresTelemetrySink:
    if not _telemetry_enabled():
        return NoopTelemetrySink()

    sink_name = os.getenv("TELEMETRY_SINK", "console").strip().lower()

    if sink_name == "noop":
        return NoopTelemetrySink()

    if sink_name == "console":
        return ConsoleTelemetrySink()

    if sink_name == "postgres":
        database_url = os.getenv("TELEMETRY_DATABASE_URL")
        if not database_url:
            _warn_once(
                "postgres_missing_database_url",
                "Postgres telemetry requested without TELEMETRY_DATABASE_URL; using no-op sink",
            )
            return NoopTelemetrySink()

        return PostgresTelemetrySink(database_url=database_url)

    # Unsupported sinks are treated as console so deployments remain observable
    # without failing startup.
    _warn_once(
        f"unsupported_sink_{sink_name}",
        f"Unsupported TELEMETRY_SINK={sink_name!r}; using console telemetry sink",
    )
    return ConsoleTelemetrySink()


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _truncate(value: str | None, max_length: int = MAX_ERROR_MESSAGE_LENGTH) -> str | None:
    if value is None:
        return None

    text = str(value)
    if len(text) <= max_length:
        return text

    return f"{text[:max_length]}..."


def _safe_payload_keys(payload: dict[str, Any] | None) -> list[str] | None:
    if not payload:
        return None

    return sorted(str(key) for key in payload.keys())


def _safe_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    if not metadata:
        return None

    safe_metadata: dict[str, Any] = {}
    for key, value in metadata.items():
        normalized_key = str(key)
        if normalized_key.lower() in BLOCKED_METADATA_KEYS:
            continue

        if isinstance(value, str):
            safe_metadata[normalized_key] = _truncate(value)
            continue

        if value is None or isinstance(value, bool | int | float):
            safe_metadata[normalized_key] = value

    return safe_metadata or None


def _emit(payload: dict[str, Any]) -> None:
    payload_with_timestamp = {
        **payload,
        "timestamp": _utc_timestamp(),
    }
    _get_sink().record(payload_with_timestamp)


def record_session_started(
    *,
    session_id: str,
    stage: str | None,
    state: str | None,
    turns_count: int | None,
) -> None:
    try:
        _emit(
            {
                "event": "session_started",
                "session_id": session_id,
                "stage": stage,
                "state": state,
                "turns_count": turns_count,
            }
        )
    except Exception:
        return None


def record_session_updated(
    *,
    session_id: str,
    stage: str | None,
    state: str | None,
    turns_count: int | None,
    synthesis_generated: bool | None = None,
    pathways_generated: bool | None = None,
    pdf_downloaded: bool | None = None,
    status: str | None = None,
) -> None:
    try:
        _emit(
            {
                "event": "session_updated",
                "session_id": session_id,
                "stage": stage,
                "state": state,
                "turns_count": turns_count,
                "synthesis_generated": synthesis_generated,
                "pathways_generated": pathways_generated,
                "pdf_downloaded": pdf_downloaded,
                "status": status,
            }
        )
    except Exception:
        return None


def record_session_closed(
    *,
    session_id: str,
    stage: str | None,
    state: str | None,
    turns_count: int | None,
    status: str = "completed",
) -> None:
    try:
        _emit(
            {
                "event": "session_closed",
                "session_id": session_id,
                "stage": stage,
                "state": state,
                "turns_count": turns_count,
                "status": status,
            }
        )
    except Exception:
        return None


def record_feedback_submitted(
    *,
    session_id: str,
    answer_1: bool | None = None,
    answer_2: bool | None = None,
    dropdown_values: list[str] | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    try:
        _emit(
            {
                "event": "feedback_submitted",
                "session_id": session_id,
                "answer_1": answer_1,
                "answer_2": answer_2,
                "dropdown_values": dropdown_values,
                # Do not emit arbitrary payload content; keys are enough for
                # future schema debugging without risking personal data.
                "payload_keys": _safe_payload_keys(payload),
            }
        )
    except Exception:
        return None


def record_llm_call(
    *,
    session_id: str | None,
    llm_operation: str,
    provider: str = "openai",
    model: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    total_tokens: int | None = None,
    cached_input_tokens: int | None = None,
    reasoning_tokens: int | None = None,
    success: bool = True,
    latency_ms: int | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    try:
        _emit(
            {
                "event": "llm_call",
                "session_id": session_id,
                "llm_operation": llm_operation,
                "provider": provider,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cached_input_tokens": cached_input_tokens,
                "reasoning_tokens": reasoning_tokens,
                "success": success,
                "latency_ms": latency_ms,
                "error_type": error_type,
                "error_message": _truncate(error_message),
                "metadata": _safe_metadata(metadata),
            }
        )
    except Exception:
        return None
