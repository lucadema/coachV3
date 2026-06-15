"""Behavioural smoke test for the separate admin control panel.

This runs without a live database by using the same service boundary as the
admin API with an in-memory repository. It is intended as a fast Codex-friendly
regression check for enterprise, pilot, token, rotation, and revocation flows.
"""

from __future__ import annotations

from datetime import datetime, timezone

from admin_backend.config import AdminSettings
from admin_backend.models import EnterpriseCreate, EnterpriseUpdate, PilotCreate, PilotUpdate, TokenType
from admin_backend.service import AdminService


def now() -> datetime:
    return datetime.now(timezone.utc)


class InMemoryAdminRepository:
    def __init__(self) -> None:
        self.enterprises: dict[str, dict] = {}
        self.pilots: dict[str, dict] = {}
        self.tokens: dict[str, dict] = {}

    def list_enterprises(self) -> list[dict]:
        return list(self.enterprises.values())

    def create_enterprise(self, enterprise: dict) -> dict:
        row = {**enterprise, "created_at": now(), "updated_at": now()}
        self.enterprises[row["id"]] = row
        return row

    def get_enterprise(self, enterprise_id: str) -> dict | None:
        return self.enterprises.get(enterprise_id)

    def update_enterprise(self, enterprise_id: str, updates: dict) -> dict | None:
        row = self.enterprises.get(enterprise_id)
        if row is None:
            return None
        row.update(updates)
        row["updated_at"] = now()
        return row

    def update_pilots_status_for_enterprise(
        self,
        enterprise_id: str,
        *,
        from_status: str,
        to_status: str,
    ) -> int:
        updated_count = 0
        for row in self.pilots.values():
            if row["enterprise_id"] == enterprise_id and row["status"] == from_status:
                row["status"] = to_status
                row["updated_at"] = now()
                updated_count += 1
        return updated_count

    def delete_enterprise(self, enterprise_id: str) -> bool:
        if enterprise_id not in self.enterprises:
            return False

        pilot_ids = [
            pilot_id for pilot_id, row in self.pilots.items()
            if row["enterprise_id"] == enterprise_id
        ]
        for pilot_id in pilot_ids:
            self.delete_pilot(pilot_id)
        del self.enterprises[enterprise_id]
        return True

    def list_pilots_for_enterprise(self, enterprise_id: str) -> list[dict]:
        return [
            row for row in self.pilots.values()
            if row["enterprise_id"] == enterprise_id
        ]

    def create_pilot(self, pilot: dict) -> dict:
        row = {**pilot, "created_at": now(), "updated_at": now()}
        self.pilots[row["id"]] = row
        return row

    def get_pilot(self, pilot_id: str) -> dict | None:
        return self.pilots.get(pilot_id)

    def update_pilot(self, pilot_id: str, updates: dict) -> dict | None:
        row = self.pilots.get(pilot_id)
        if row is None:
            return None
        row.update(updates)
        row["updated_at"] = now()
        return row

    def delete_pilot(self, pilot_id: str) -> bool:
        if pilot_id not in self.pilots:
            return False

        del self.pilots[pilot_id]
        token_ids = [
            token_id for token_id, row in self.tokens.items()
            if row["pilot_id"] == pilot_id
        ]
        for token_id in token_ids:
            del self.tokens[token_id]
        return True

    def find_active_token(self, pilot_id: str, token_type: str) -> dict | None:
        rows = [
            row for row in self.tokens.values()
            if row["pilot_id"] == pilot_id
            and row["token_type"] == token_type
            and row["status"] == "active"
        ]
        return rows[-1] if rows else None

    def list_latest_tokens_for_pilot(self, pilot_id: str) -> list[dict]:
        latest_by_type: dict[str, dict] = {}
        for row in self.tokens.values():
            if row["pilot_id"] == pilot_id:
                latest_by_type[row["token_type"]] = row
        return list(latest_by_type.values())

    def create_access_token(self, token: dict) -> dict:
        row = {
            **token,
            "created_at": now(),
            "last_used_at": None,
            "revoked_at": None,
            "updated_at": now(),
        }
        self.tokens[row["id"]] = row
        return row

    def get_access_token(self, token_id: str) -> dict | None:
        return self.tokens.get(token_id)

    def find_token_by_hash(self, token_hash: str) -> dict | None:
        for row in self.tokens.values():
            if row["token_hash"] == token_hash:
                return row
        return None

    def revoke_access_token(self, token_id: str) -> dict | None:
        row = self.tokens.get(token_id)
        if row is None:
            return None
        row["status"] = "revoked"
        row["revoked_at"] = now()
        row["updated_at"] = now()
        return row

    def mark_token_used(self, token_id: str) -> None:
        self.tokens[token_id]["last_used_at"] = now()

    def get_pilot_summary_counts(self, _pilot_id: str) -> dict:
        return {
            "sessions_count": 1,
            "last_activity_at": now(),
            "feedback_records_count": 0,
        }


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"OK: {message}")


def main() -> None:
    service = AdminService(
        InMemoryAdminRepository(),
        AdminSettings(
            database_url="postgresql://example",
            admin_api_token="test-admin-token",
            environment_name="smoke",
            glimpse_access_url_template="https://pilot.example/start?t={token}",
            dashboard_access_url_template="https://dashboard.example/view?t={token}",
            cors_allow_origins=("http://localhost:5174",),
        ),
    )

    enterprise = service.create_enterprise(EnterpriseCreate(name="Test Enterprise"))
    check(enterprise.name == "Test Enterprise", "enterprise can be created")

    pilot = service.create_pilot(PilotCreate(enterprise_id=enterprise.id, name="Test Pilot"))
    check(pilot.enterprise_id == enterprise.id, "pilot belongs to enterprise")

    glimpse_link = service.generate_link(pilot.id, TokenType.GLIMPSE_APP)
    dashboard_link = service.generate_link(pilot.id, TokenType.DASHBOARD)
    check("https://pilot.example/start?t=" in (glimpse_link.full_access_link or ""), "Glimpse link is full URL")
    check("https://dashboard.example/view?t=" in (dashboard_link.full_access_link or ""), "dashboard link is full URL")

    repository = service.repository
    glimpse_token = repository.tokens[glimpse_link.token_id]["token_recoverable"]
    dashboard_token = repository.tokens[dashboard_link.token_id]["token_recoverable"]

    check(service.validate_token(glimpse_token, TokenType.GLIMPSE_APP).valid, "Glimpse token validates")
    check(service.validate_token(dashboard_token, TokenType.DASHBOARD).valid, "dashboard token validates")
    check(
        not service.validate_token(dashboard_token, TokenType.GLIMPSE_APP).valid,
        "dashboard token is rejected for Glimpse",
    )

    rotated = service.rotate_link(glimpse_link.token_id)
    rotated_token = repository.tokens[rotated.token_id]["token_recoverable"]
    check(
        not service.validate_token(glimpse_token, TokenType.GLIMPSE_APP).valid,
        "old rotated Glimpse token is invalid",
    )
    check(service.validate_token(rotated_token, TokenType.GLIMPSE_APP).valid, "new rotated Glimpse token works")

    service.revoke_link(dashboard_link.token_id)
    check(
        not service.validate_token(dashboard_token, TokenType.DASHBOARD).valid,
        "revoked dashboard token is invalid",
    )

    summary = service.get_pilot_summary(pilot.id)
    check(summary.sessions_count == 1, "pilot summary returns filtered session count")

    service.update_pilot(pilot.id, PilotUpdate(status="closed"))
    service.update_enterprise(enterprise.id, EnterpriseUpdate(status="closed"))
    service.delete_enterprise(enterprise.id)
    check(repository.get_enterprise(enterprise.id) is None, "enterprise cleanup delete works")
    check(repository.get_pilot(pilot.id) is None, "enterprise cleanup deletes child pilot")


if __name__ == "__main__":
    main()
