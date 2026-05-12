"""Telemetry output sinks.

This console-first implementation intentionally avoids persistence and network
calls. Later database/PostHog sinks can implement the same small ``record`` seam.
"""

from __future__ import annotations

import json
from typing import Any


class ConsoleTelemetrySink:
    """Emit one-line JSON telemetry records to stdout."""

    def record(self, payload: dict[str, Any]) -> None:
        print(f"TELEMETRY {json.dumps(payload, default=str, sort_keys=True)}")


class NoopTelemetrySink:
    """Telemetry sink used when telemetry is disabled."""

    def record(self, payload: dict[str, Any]) -> None:
        return None
