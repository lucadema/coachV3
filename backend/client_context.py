"""Safe parsing for optional frontend launch context.

The React app passes this as generic request metadata. The backend sanitises it
again before any telemetry code sees it because request payloads are untrusted.
"""

from __future__ import annotations

import re
from typing import Any


SESSION_LABEL_PATTERN = re.compile(r"^[a-z0-9_.-]{1,64}$")


def sanitize_session_label(value: Any) -> str | None:
    """Return a conservative session label or ``None`` for invalid input."""
    try:
        if not isinstance(value, str):
            return None

        normalized = value.strip().lower()
        if not SESSION_LABEL_PATTERN.fullmatch(normalized):
            return None

        return normalized
    except Exception:
        return None


def extract_session_label(client_context: Any) -> str | None:
    """Extract session_label/sessionLabel from optional client context."""
    try:
        if not isinstance(client_context, dict):
            return None

        return sanitize_session_label(
            client_context.get("session_label") or client_context.get("sessionLabel")
        )
    except Exception:
        return None
