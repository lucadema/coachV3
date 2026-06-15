"""Runtime configuration for the separate admin backend."""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


DEFAULT_GLIMPSE_ACCESS_URL_TEMPLATE = "http://localhost:5173/?t={token}"
DEFAULT_DASHBOARD_ACCESS_URL_TEMPLATE = "http://localhost:5175/?t={token}"
LOCAL_ADMIN_CORS_ORIGINS = (
    "http://localhost:5174",
    "http://127.0.0.1:5174",
)


@dataclass(frozen=True)
class AdminSettings:
    """Environment-backed settings for the admin API."""

    database_url: str | None
    admin_api_token: str | None
    environment_name: str
    glimpse_access_url_template: str
    dashboard_access_url_template: str
    cors_allow_origins: tuple[str, ...]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_env() -> None:
    load_dotenv(_repo_root() / ".env", override=False)


def _split_origins(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()

    return tuple(origin.strip() for origin in value.split(",") if origin.strip())


def _local_network_origins(port: int = 5174) -> tuple[str, ...]:
    """Return likely LAN origins for the local Vite dev server."""
    origins: list[str] = []
    try:
        hostnames = {socket.gethostname(), socket.getfqdn()}
        addresses: set[str] = set()
        for hostname in hostnames:
            try:
                addresses.update(socket.gethostbyname_ex(hostname)[2])
            except OSError:
                continue

        for address in addresses:
            if address and not address.startswith("127."):
                origins.append(f"http://{address}:{port}")
    except OSError:
        return ()

    return tuple(sorted(set(origins)))


def get_settings() -> AdminSettings:
    """Return current admin settings.

    This intentionally reads the environment each time so tests and local
    scripts can patch variables without fighting cached process state.
    """
    _load_env()
    configured_origins = _split_origins(os.getenv("ADMIN_CORS_ALLOW_ORIGINS"))
    cors_origins = tuple(
        dict.fromkeys(
            (
                *LOCAL_ADMIN_CORS_ORIGINS,
                *_local_network_origins(),
                *configured_origins,
            )
        )
    )

    return AdminSettings(
        database_url=os.getenv("ADMIN_DATABASE_URL") or os.getenv("TELEMETRY_DATABASE_URL"),
        admin_api_token=os.getenv("ADMIN_API_TOKEN"),
        environment_name=os.getenv("ADMIN_ENVIRONMENT", os.getenv("ENVIRONMENT", "local")),
        glimpse_access_url_template=(
            os.getenv("GLIMPSE_ACCESS_URL_TEMPLATE")
            or DEFAULT_GLIMPSE_ACCESS_URL_TEMPLATE
        ),
        dashboard_access_url_template=(
            os.getenv("DASHBOARD_ACCESS_URL_TEMPLATE")
            or DEFAULT_DASHBOARD_ACCESS_URL_TEMPLATE
        ),
        cors_allow_origins=cors_origins,
    )
