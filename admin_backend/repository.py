"""PostgreSQL repository for admin control panel data."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from admin_backend.errors import AdminConfigurationError, AdminNotFoundError


ENTERPRISE_COLUMNS = "id, name, status, notes, created_at, updated_at"
PILOT_COLUMNS = """
    id,
    enterprise_id,
    name,
    status,
    start_at,
    end_at,
    notes,
    feedback_pack_id,
    created_at,
    updated_at
"""
TOKEN_COLUMNS = """
    id,
    pilot_id,
    token_type,
    token_hash,
    token_recoverable,
    token_prefix,
    status,
    created_at,
    expires_at,
    last_used_at,
    revoked_at,
    updated_at
"""


class AdminPostgresRepository:
    """Small SQL repository used only by the admin backend."""

    def __init__(self, database_url: str | None) -> None:
        self.database_url = database_url

    def _connect(self) -> Any:
        if not self.database_url:
            raise AdminConfigurationError("Admin database URL is not configured.")

        try:
            import psycopg
            from psycopg.rows import dict_row
        except Exception as exc:  # pragma: no cover - environment dependent
            raise AdminConfigurationError("psycopg is not available.") from exc

        return psycopg.connect(self.database_url, row_factory=dict_row)

    def _fetch_one(self, sql: str, params: Sequence[Any]) -> dict[str, Any] | None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                row = cursor.fetchone()
                connection.commit()
                return dict(row) if row is not None else None

    def _fetch_all(self, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                connection.commit()
                return [dict(row) for row in rows]

    def list_enterprises(self) -> list[dict[str, Any]]:
        return self._fetch_all(
            f"""
            SELECT {ENTERPRISE_COLUMNS}
            FROM admin_enterprises
            ORDER BY created_at DESC, name ASC
            """
        )

    def create_enterprise(self, enterprise: dict[str, Any]) -> dict[str, Any]:
        row = self._fetch_one(
            f"""
            INSERT INTO admin_enterprises (id, name, status, notes)
            VALUES (%s, %s, %s, %s)
            RETURNING {ENTERPRISE_COLUMNS}
            """,
            (
                enterprise["id"],
                enterprise["name"],
                enterprise["status"],
                enterprise["notes"],
            ),
        )
        if row is None:
            raise AdminNotFoundError("Enterprise was not created.")
        return row

    def get_enterprise(self, enterprise_id: str) -> dict[str, Any] | None:
        return self._fetch_one(
            f"""
            SELECT {ENTERPRISE_COLUMNS}
            FROM admin_enterprises
            WHERE id = %s
            """,
            (enterprise_id,),
        )

    def update_enterprise(self, enterprise_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        if not updates:
            return self.get_enterprise(enterprise_id)

        assignments = [f"{column} = %s" for column in updates]
        params = [*updates.values(), enterprise_id]
        return self._fetch_one(
            f"""
            UPDATE admin_enterprises
            SET {", ".join(assignments)}, updated_at = NOW()
            WHERE id = %s
            RETURNING {ENTERPRISE_COLUMNS}
            """,
            params,
        )

    def update_pilots_status_for_enterprise(
        self,
        enterprise_id: str,
        *,
        from_status: str,
        to_status: str,
    ) -> int:
        row = self._fetch_one(
            """
            WITH updated AS (
                UPDATE admin_pilots
                SET status = %s,
                    updated_at = NOW()
                WHERE enterprise_id = %s
                  AND status = %s
                RETURNING id
            )
            SELECT COUNT(*)::integer AS updated_count
            FROM updated
            """,
            (to_status, enterprise_id, from_status),
        )
        return int((row or {}).get("updated_count") or 0)

    def delete_enterprise(self, enterprise_id: str) -> bool:
        """Hard-delete an enterprise and its pilots for admin cleanup."""
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM admin_pilots
                    WHERE enterprise_id = %s
                    """,
                    (enterprise_id,),
                )
                cursor.execute(
                    """
                    DELETE FROM admin_enterprises
                    WHERE id = %s
                    RETURNING id
                    """,
                    (enterprise_id,),
                )
                row = cursor.fetchone()
                connection.commit()
                return row is not None

    def list_pilots_for_enterprise(self, enterprise_id: str) -> list[dict[str, Any]]:
        return self._fetch_all(
            f"""
            SELECT {PILOT_COLUMNS}
            FROM admin_pilots
            WHERE enterprise_id = %s
            ORDER BY created_at DESC, name ASC
            """,
            (enterprise_id,),
        )

    def create_pilot(self, pilot: dict[str, Any]) -> dict[str, Any]:
        row = self._fetch_one(
            f"""
            INSERT INTO admin_pilots (
                id, enterprise_id, name, status, start_at, end_at, notes, feedback_pack_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING {PILOT_COLUMNS}
            """,
            (
                pilot["id"],
                pilot["enterprise_id"],
                pilot["name"],
                pilot["status"],
                pilot["start_at"],
                pilot["end_at"],
                pilot["notes"],
                pilot["feedback_pack_id"],
            ),
        )
        if row is None:
            raise AdminNotFoundError("Pilot was not created.")
        return row

    def get_pilot(self, pilot_id: str) -> dict[str, Any] | None:
        return self._fetch_one(
            f"""
            SELECT {PILOT_COLUMNS}
            FROM admin_pilots
            WHERE id = %s
            """,
            (pilot_id,),
        )

    def update_pilot(self, pilot_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        if not updates:
            return self.get_pilot(pilot_id)

        assignments = [f"{column} = %s" for column in updates]
        params = [*updates.values(), pilot_id]
        return self._fetch_one(
            f"""
            UPDATE admin_pilots
            SET {", ".join(assignments)}, updated_at = NOW()
            WHERE id = %s
            RETURNING {PILOT_COLUMNS}
            """,
            params,
        )

    def delete_pilot(self, pilot_id: str) -> bool:
        row = self._fetch_one(
            """
            DELETE FROM admin_pilots
            WHERE id = %s
            RETURNING id
            """,
            (pilot_id,),
        )
        return row is not None

    def find_active_token(self, pilot_id: str, token_type: str) -> dict[str, Any] | None:
        return self._fetch_one(
            f"""
            SELECT {TOKEN_COLUMNS}
            FROM admin_access_tokens
            WHERE pilot_id = %s
              AND token_type = %s
              AND status = 'active'
              AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (pilot_id, token_type),
        )

    def list_latest_tokens_for_pilot(self, pilot_id: str) -> list[dict[str, Any]]:
        return self._fetch_all(
            f"""
            SELECT DISTINCT ON (token_type) {TOKEN_COLUMNS}
            FROM admin_access_tokens
            WHERE pilot_id = %s
            ORDER BY token_type, created_at DESC
            """,
            (pilot_id,),
        )

    def create_access_token(self, token: dict[str, Any]) -> dict[str, Any]:
        row = self._fetch_one(
            f"""
            INSERT INTO admin_access_tokens (
                id,
                pilot_id,
                token_type,
                token_hash,
                token_recoverable,
                token_prefix,
                status,
                expires_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING {TOKEN_COLUMNS}
            """,
            (
                token["id"],
                token["pilot_id"],
                token["token_type"],
                token["token_hash"],
                token["token_recoverable"],
                token["token_prefix"],
                token["status"],
                token["expires_at"],
            ),
        )
        if row is None:
            raise AdminNotFoundError("Access token was not created.")
        return row

    def get_access_token(self, token_id: str) -> dict[str, Any] | None:
        return self._fetch_one(
            f"""
            SELECT {TOKEN_COLUMNS}
            FROM admin_access_tokens
            WHERE id = %s
            """,
            (token_id,),
        )

    def find_token_by_hash(self, token_hash: str) -> dict[str, Any] | None:
        return self._fetch_one(
            f"""
            SELECT {TOKEN_COLUMNS}
            FROM admin_access_tokens
            WHERE token_hash = %s
            """,
            (token_hash,),
        )

    def find_dashboard_token_context(self, token_hash: str) -> dict[str, Any] | None:
        return self._fetch_one(
            """
            SELECT
                tokens.id AS token_id,
                tokens.pilot_id AS pilot_id,
                tokens.status AS token_status,
                tokens.expires_at AS token_expires_at,
                pilots.name AS pilot_name,
                pilots.status AS pilot_status,
                enterprises.name AS enterprise_name
            FROM admin_access_tokens AS tokens
            JOIN admin_pilots AS pilots
              ON pilots.id = tokens.pilot_id
            JOIN admin_enterprises AS enterprises
              ON enterprises.id = pilots.enterprise_id
            WHERE tokens.token_hash = %s
              AND tokens.token_type = 'dashboard'
            LIMIT 1
            """,
            (token_hash,),
        )

    def get_problem_category_counts(self, pilot_id: str) -> dict[str, int]:
        rows = self._fetch_all(
            """
            SELECT problem_category AS value, COUNT(*)::integer AS count
            FROM coach_sessions
            WHERE pilot_id = %s
              AND problem_category IS NOT NULL
              AND problem_category <> ''
            GROUP BY problem_category
            """,
            (pilot_id,),
        )
        return {str(row["value"]): int(row["count"] or 0) for row in rows}

    def get_engagement_signal_counts(self, pilot_id: str) -> dict[str, int]:
        rows = self._fetch_all(
            """
            SELECT engagement_signal AS value, COUNT(*)::integer AS count
            FROM coach_sessions
            WHERE pilot_id = %s
              AND engagement_signal IS NOT NULL
              AND engagement_signal <> ''
            GROUP BY engagement_signal
            """,
            (pilot_id,),
        )
        return {str(row["value"]): int(row["count"] or 0) for row in rows}

    def list_feedback_responses_for_pilot(self, pilot_id: str) -> list[Any]:
        rows = self._fetch_all(
            """
            SELECT feedback_responses
            FROM coach_sessions
            WHERE pilot_id = %s
              AND feedback_responses IS NOT NULL
            """,
            (pilot_id,),
        )
        return [row.get("feedback_responses") for row in rows]

    def revoke_access_token(self, token_id: str) -> dict[str, Any] | None:
        return self._fetch_one(
            f"""
            UPDATE admin_access_tokens
            SET status = 'revoked',
                revoked_at = COALESCE(revoked_at, NOW()),
                updated_at = NOW()
            WHERE id = %s
            RETURNING {TOKEN_COLUMNS}
            """,
            (token_id,),
        )

    def mark_token_used(self, token_id: str) -> None:
        self._fetch_one(
            """
            UPDATE admin_access_tokens
            SET last_used_at = NOW(), updated_at = NOW()
            WHERE id = %s
            RETURNING id
            """,
            (token_id,),
        )

    def get_pilot_summary_counts(self, pilot_id: str) -> dict[str, Any]:
        row = self._fetch_one(
            """
            SELECT
                COUNT(*)::integer AS sessions_count,
                MAX(last_interaction_at) AS last_activity_at,
                COUNT(*) FILTER (
                    WHERE feedback_responses IS NOT NULL
                )::integer AS feedback_records_count
            FROM coach_sessions
            WHERE pilot_id = %s
            """,
            (pilot_id,),
        )
        return row or {
            "sessions_count": 0,
            "last_activity_at": None,
            "feedback_records_count": 0,
        }
