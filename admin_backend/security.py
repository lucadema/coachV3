"""Admin authentication helpers."""

from __future__ import annotations

from hmac import compare_digest

from fastapi import Header, HTTPException

from admin_backend.config import get_settings


def _bearer_value(authorization: str | None) -> str | None:
    if not authorization:
        return None

    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        return None

    return value.strip()


def require_admin_auth(
    authorization: str | None = Header(default=None),
    x_admin_token: str | None = Header(default=None),
) -> None:
    """Reject requests that do not present the configured admin secret."""
    expected = get_settings().admin_api_token
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Admin authentication is not configured.",
        )

    provided = _bearer_value(authorization) or x_admin_token
    if not provided or not compare_digest(provided, expected):
        raise HTTPException(status_code=403, detail="Forbidden.")

    return None

