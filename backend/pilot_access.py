"""Participant pilot-token resolution for the Glimpse backend.

This is the only runtime bridge from the existing Glimpse backend to the admin
pilot tables. It validates participant tokens and returns the stable pilot_id.
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


logger = logging.getLogger(__name__)


def _database_url() -> str | None:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    return os.getenv("ADMIN_DATABASE_URL") or os.getenv("TELEMETRY_DATABASE_URL")


def _hash_access_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _connect(database_url: str) -> Any:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("psycopg_unavailable") from exc

    return psycopg.connect(
        database_url,
        connect_timeout=2,
        options="-c statement_timeout=2000",
        row_factory=dict_row,
    )


def resolve_glimpse_pilot_id(access_token: str) -> str | None:
    """Return pilot_id for a valid active Glimpse participant token."""
    database_url = _database_url()
    if not database_url:
        logger.warning("Pilot token validation requested without a database URL.")
        return None

    conn = None
    try:
        conn = _connect(database_url)
        token_hash = _hash_access_token(access_token)
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, pilot_id
                FROM admin_access_tokens
                WHERE token_hash = %s
                  AND token_type = 'glimpse_app'
                  AND status = 'active'
                  AND (expires_at IS NULL OR expires_at > NOW())
                LIMIT 1
                """,
                (token_hash,),
            )
            row = cursor.fetchone()
            if row is None:
                conn.commit()
                return None

            cursor.execute(
                """
                UPDATE admin_access_tokens
                SET last_used_at = NOW(), updated_at = NOW()
                WHERE id = %s
                """,
                (row["id"],),
            )
            conn.commit()
            return str(row["pilot_id"])
    except Exception as exc:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        logger.warning(
            "Pilot token validation failed error_type=%s error=%s",
            type(exc).__name__,
            str(exc)[:300],
        )
        return None
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
