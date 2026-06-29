"""Pilot-grade safeguards for temporary live session storage."""

from __future__ import annotations

import hashlib
import os


TRUTHY_VALUES = {"1", "true", "yes", "on"}
DEFAULT_SESSION_TTL_MINUTES = 240
DEBUG_DISABLED_MESSAGE = "debug_persistence=disabled"


def debug_persistence_enabled() -> bool:
    """Return whether unsafe full debug persistence is explicitly enabled."""
    return os.getenv("GLIMPSE_DEBUG_PERSISTENCE", "false").strip().lower() in TRUTHY_VALUES


def configured_session_ttl_minutes() -> int:
    """Return the live-session TTL, falling back to the pilot-safe default."""
    raw_value = os.getenv("GLIMPSE_SESSION_TTL_MINUTES")
    if raw_value is None:
        return DEFAULT_SESSION_TTL_MINUTES

    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        return DEFAULT_SESSION_TTL_MINUTES

    return parsed if parsed > 0 else DEFAULT_SESSION_TTL_MINUTES


def sanitize_debug_message(debug_message: str | None) -> str | None:
    """Strip persisted debug details unless explicitly enabled for development."""
    if debug_persistence_enabled():
        return debug_message

    if not debug_message:
        return debug_message

    return DEBUG_DISABLED_MESSAGE


def short_session_ref(session_id: str | None) -> str:
    """Return a non-reversible short reference for logs."""
    text = str(session_id or "").strip()
    if not text:
        return "missing"

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
