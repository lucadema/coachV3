"""Pure backend HTTP client helpers for the Streamlit frontend."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class ApiResponse:
    """Structured result for one backend HTTP request."""

    data: dict[str, Any] | None
    error_message: str | None
    status_code: int | None
    not_found: bool


def request_json(
    base_url: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    timeout_seconds: int = 20,
) -> ApiResponse:
    """Execute one JSON request against the backend."""
    try:
        if method == "GET":
            response = requests.get(f"{base_url}{path}", timeout=timeout_seconds)
        else:
            response = requests.post(
                f"{base_url}{path}",
                json=payload,
                timeout=timeout_seconds,
            )

        status_code = response.status_code
        response.raise_for_status()
        return ApiResponse(
            data=response.json(),
            error_message=None,
            status_code=status_code,
            not_found=False,
        )
    except requests.RequestException as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        return ApiResponse(
            data=None,
            error_message=str(exc),
            status_code=status_code,
            not_found=status_code == 404,
        )
