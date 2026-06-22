import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from admin_backend.app import app
from admin_backend.config import AdminSettings, get_settings
from admin_backend.errors import AdminConfigurationError
from admin_backend.models import (
    EnterpriseCreate,
    EnterpriseUpdate,
    PilotCreate,
    PilotUpdate,
    TokenStatus,
    TokenType,
)
from admin_backend.routes import get_service
from admin_backend.service import AdminService, hash_access_token


def _now() -> datetime:
    return datetime.now(timezone.utc)


class InMemoryAdminRepository:
    def __init__(self) -> None:
        self.enterprises: dict[str, dict] = {}
        self.pilots: dict[str, dict] = {}
        self.tokens: dict[str, dict] = {}
        self.summary_counts: dict[str, dict] = {}

    def list_enterprises(self) -> list[dict]:
        return list(self.enterprises.values())

    def create_enterprise(self, enterprise: dict) -> dict:
        row = {
            **enterprise,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.enterprises[row["id"]] = row
        return row

    def get_enterprise(self, enterprise_id: str) -> dict | None:
        return self.enterprises.get(enterprise_id)

    def update_enterprise(self, enterprise_id: str, updates: dict) -> dict | None:
        row = self.enterprises.get(enterprise_id)
        if row is None:
            return None
        row.update(updates)
        row["updated_at"] = _now()
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
                row["updated_at"] = _now()
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
        row = {
            **pilot,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.pilots[row["id"]] = row
        return row

    def get_pilot(self, pilot_id: str) -> dict | None:
        return self.pilots.get(pilot_id)

    def update_pilot(self, pilot_id: str, updates: dict) -> dict | None:
        row = self.pilots.get(pilot_id)
        if row is None:
            return None
        row.update(updates)
        row["updated_at"] = _now()
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
        matching = [
            row for row in self.tokens.values()
            if row["pilot_id"] == pilot_id
            and row["token_type"] == token_type
            and row["status"] == "active"
        ]
        return matching[-1] if matching else None

    def list_latest_tokens_for_pilot(self, pilot_id: str) -> list[dict]:
        latest_by_type: dict[str, dict] = {}
        for row in self.tokens.values():
            if row["pilot_id"] == pilot_id:
                latest_by_type[row["token_type"]] = row
        return list(latest_by_type.values())

    def create_access_token(self, token: dict) -> dict:
        row = {
            **token,
            "created_at": _now(),
            "last_used_at": None,
            "revoked_at": None,
            "updated_at": _now(),
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
        row["revoked_at"] = _now()
        row["updated_at"] = _now()
        return row

    def mark_token_used(self, token_id: str) -> None:
        self.tokens[token_id]["last_used_at"] = _now()

    def get_pilot_summary_counts(self, pilot_id: str) -> dict:
        return self.summary_counts.get(
            pilot_id,
            {
                "sessions_count": 0,
                "last_activity_at": None,
                "feedback_records_count": 0,
            },
        )


def make_settings() -> AdminSettings:
    return AdminSettings(
        database_url="postgresql://example",
        admin_api_token="test-admin-token",
        environment_name="test",
        glimpse_access_url_template="https://glimpse.example/start?t={token}",
        dashboard_access_url_template="https://dashboard.example/view?t={token}",
        cors_allow_origins=("http://localhost:5174",),
    )


class AdminConfigTests(unittest.TestCase):
    def test_get_settings_reads_glimpse_url_template_from_environment(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "ADMIN_ENVIRONMENT": "production",
                "GLIMPSE_ACCESS_URL_TEMPLATE": "https://glimpse.intheaether.io/?t={token}",
                "DASHBOARD_ACCESS_URL_TEMPLATE": "https://dashboard.intheaether.io/?t={token}",
            },
            clear=False,
        ):
            settings = get_settings()

        self.assertEqual(
            settings.glimpse_access_url_template,
            "https://glimpse.intheaether.io/?t={token}",
        )
        self.assertTrue(settings.require_configured_url_templates)


class AdminServiceBehaviourTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryAdminRepository()
        self.service = AdminService(self.repository, make_settings())
        self.enterprise = self.service.create_enterprise(
            EnterpriseCreate(name="Test Enterprise", notes="Pilot customer")
        )
        self.pilot = self.service.create_pilot(
            PilotCreate(enterprise_id=self.enterprise.id, name="Test Pilot")
        )

    def test_create_enterprise_and_pilot(self) -> None:
        pilots = self.service.list_pilots_for_enterprise(self.enterprise.id)

        self.assertEqual(self.enterprise.name, "Test Enterprise")
        self.assertEqual(pilots[0].enterprise_id, self.enterprise.id)
        self.assertEqual(pilots[0].name, "Test Pilot")
        self.assertIsNone(pilots[0].feedback_pack_id)

    def test_pilot_feedback_pack_id_can_be_created_and_updated(self) -> None:
        pilot = self.service.create_pilot(
            PilotCreate(
                enterprise_id=self.enterprise.id,
                name="Feedback Pilot",
                feedback_pack_id=" glimpse_default ",
            )
        )

        self.assertEqual(pilot.feedback_pack_id, "glimpse_default")

        updated = self.service.update_pilot(
            pilot.id,
            PilotUpdate(feedback_pack_id=" pilot_impact_questions "),
        )

        self.assertEqual(updated.feedback_pack_id, "pilot_impact_questions")

    def test_generate_glimpse_and_dashboard_links(self) -> None:
        glimpse_link = self.service.generate_link(self.pilot.id, TokenType.GLIMPSE_APP)
        dashboard_link = self.service.generate_link(self.pilot.id, TokenType.DASHBOARD)

        self.assertEqual(glimpse_link.token_type, TokenType.GLIMPSE_APP)
        self.assertIn("https://glimpse.example/start?t=", glimpse_link.full_access_link or "")
        self.assertEqual(dashboard_link.token_type, TokenType.DASHBOARD)
        self.assertIn("https://dashboard.example/view?t=", dashboard_link.full_access_link or "")
        self.assertNotEqual(glimpse_link.token_prefix, dashboard_link.token_prefix)

    def test_render_runtime_rejects_localhost_link_templates(self) -> None:
        service = AdminService(
            self.repository,
            AdminSettings(
                database_url="postgresql://example",
                admin_api_token="test-admin-token",
                environment_name="production",
                glimpse_access_url_template="http://localhost:5173/?t={token}",
                dashboard_access_url_template="https://dashboard.example/view?t={token}",
                cors_allow_origins=("https://admin.example",),
                require_configured_url_templates=True,
            ),
        )

        with self.assertRaisesRegex(AdminConfigurationError, "GLIMPSE_ACCESS_URL_TEMPLATE"):
            service.generate_link(self.pilot.id, TokenType.GLIMPSE_APP)

    def test_token_validation_enforces_type(self) -> None:
        link = self.service.generate_link(self.pilot.id, TokenType.GLIMPSE_APP)
        raw_token = self.repository.tokens[link.token_id]["token_recoverable"]

        valid = self.service.validate_token(raw_token, TokenType.GLIMPSE_APP)
        wrong_type = self.service.validate_token(raw_token, TokenType.DASHBOARD)

        self.assertTrue(valid.valid)
        self.assertEqual(valid.pilot_id, self.pilot.id)
        self.assertFalse(wrong_type.valid)
        self.assertEqual(wrong_type.reason, "wrong_token_type")

    def test_rotate_invalidates_old_token_and_returns_new_link(self) -> None:
        old_link = self.service.generate_link(self.pilot.id, TokenType.GLIMPSE_APP)
        old_token = self.repository.tokens[old_link.token_id]["token_recoverable"]

        new_link = self.service.rotate_link(old_link.token_id)
        new_token = self.repository.tokens[new_link.token_id]["token_recoverable"]

        self.assertEqual(self.repository.tokens[old_link.token_id]["status"], "revoked")
        self.assertFalse(self.service.validate_token(old_token, TokenType.GLIMPSE_APP).valid)
        self.assertTrue(self.service.validate_token(new_token, TokenType.GLIMPSE_APP).valid)

    def test_revoke_invalidates_token(self) -> None:
        link = self.service.generate_link(self.pilot.id, TokenType.DASHBOARD)
        raw_token = self.repository.tokens[link.token_id]["token_recoverable"]

        revoked_link = self.service.revoke_link(link.token_id)

        self.assertEqual(revoked_link.status, TokenStatus.REVOKED)
        self.assertIsNone(revoked_link.full_access_link)
        self.assertFalse(self.service.validate_token(raw_token, TokenType.DASHBOARD).valid)

    def test_summary_filters_by_pilot_id(self) -> None:
        self.repository.summary_counts[self.pilot.id] = {
            "sessions_count": 3,
            "last_activity_at": _now(),
            "feedback_records_count": 2,
        }
        self.service.generate_link(self.pilot.id, TokenType.GLIMPSE_APP)

        summary = self.service.get_pilot_summary(self.pilot.id)

        self.assertEqual(summary.sessions_count, 3)
        self.assertEqual(summary.feedback_records_count, 2)
        self.assertEqual(summary.link_statuses[TokenType.GLIMPSE_APP], TokenStatus.ACTIVE)

    def test_hash_never_contains_raw_token(self) -> None:
        raw_token = "secret-token-value"

        self.assertNotIn(raw_token, hash_access_token(raw_token))

    def test_delete_pilot_requires_closed_status(self) -> None:
        link = self.service.generate_link(self.pilot.id, TokenType.GLIMPSE_APP)

        with self.assertRaisesRegex(Exception, "Pilot can only be deleted"):
            self.service.delete_pilot(self.pilot.id)

        self.service.update_pilot(self.pilot.id, PilotUpdate(status="closed"))
        self.service.delete_pilot(self.pilot.id)

        self.assertIsNone(self.repository.get_pilot(self.pilot.id))
        self.assertNotIn(link.token_id, self.repository.tokens)

    def test_delete_enterprise_requires_closed_status(self) -> None:
        second_pilot = self.service.create_pilot(
            PilotCreate(enterprise_id=self.enterprise.id, name="Second Pilot")
        )

        with self.assertRaisesRegex(Exception, "Enterprise can only be deleted"):
            self.service.delete_enterprise(self.enterprise.id)

        self.service.update_pilot(self.pilot.id, PilotUpdate(status="closed"))
        self.service.update_pilot(second_pilot.id, PilotUpdate(status="closed"))
        self.service.update_enterprise(self.enterprise.id, EnterpriseUpdate(status="closed"))
        self.service.delete_enterprise(self.enterprise.id)

        self.assertIsNone(self.repository.get_enterprise(self.enterprise.id))
        self.assertIsNone(self.repository.get_pilot(self.pilot.id))
        self.assertIsNone(self.repository.get_pilot(second_pilot.id))

    def test_enterprise_pause_and_active_transitions_cascade_pilots(self) -> None:
        self.service.update_pilot(self.pilot.id, PilotUpdate(status="active"))
        draft_pilot = self.service.create_pilot(
            PilotCreate(enterprise_id=self.enterprise.id, name="Draft Pilot")
        )

        self.service.update_enterprise(self.enterprise.id, EnterpriseUpdate(status="paused"))

        self.assertEqual(self.service.get_pilot(self.pilot.id).status.value, "paused")
        self.assertEqual(self.service.get_pilot(draft_pilot.id).status.value, "draft")

        self.service.update_enterprise(self.enterprise.id, EnterpriseUpdate(status="active"))

        self.assertEqual(self.service.get_pilot(self.pilot.id).status.value, "active")
        self.assertEqual(self.service.get_pilot(draft_pilot.id).status.value, "draft")

    def test_enterprise_can_close_only_when_all_pilots_closed(self) -> None:
        with self.assertRaisesRegex(Exception, "all pilots are closed"):
            self.service.update_enterprise(self.enterprise.id, EnterpriseUpdate(status="closed"))

        self.service.update_pilot(self.pilot.id, PilotUpdate(status="closed"))
        enterprise = self.service.update_enterprise(
            self.enterprise.id,
            EnterpriseUpdate(status="closed"),
        )

        self.assertEqual(enterprise.status.value, "closed")


class AdminRouteAuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryAdminRepository()
        self.service = AdminService(self.repository, make_settings())
        app.dependency_overrides[get_service] = lambda: self.service
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    @patch.dict("os.environ", {"ADMIN_API_TOKEN": "test-admin-token"}, clear=False)
    def test_admin_routes_require_authentication(self) -> None:
        response = self.client.get("/admin/enterprises")

        self.assertEqual(response.status_code, 403)

    @patch.dict("os.environ", {"ADMIN_API_TOKEN": "test-admin-token"}, clear=False)
    def test_authenticated_admin_can_create_enterprise(self) -> None:
        response = self.client.post(
            "/admin/enterprises",
            headers={"Authorization": "Bearer test-admin-token"},
            json={"name": "Route Enterprise"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Route Enterprise")

    @patch.dict("os.environ", {"ADMIN_API_TOKEN": "test-admin-token"}, clear=False)
    def test_authenticated_admin_can_delete_pilot(self) -> None:
        enterprise = self.service.create_enterprise(EnterpriseCreate(name="Delete Route"))
        pilot = self.service.create_pilot(
            PilotCreate(enterprise_id=enterprise.id, name="Pilot To Delete")
        )
        self.service.update_pilot(pilot.id, PilotUpdate(status="closed"))

        response = self.client.delete(
            f"/admin/pilots/{pilot.id}",
            headers={"Authorization": "Bearer test-admin-token"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "deleted", "id": pilot.id})
        self.assertIsNone(self.repository.get_pilot(pilot.id))

    @patch.dict("os.environ", {"ADMIN_API_TOKEN": "test-admin-token"}, clear=False)
    def test_authenticated_admin_can_delete_enterprise(self) -> None:
        enterprise = self.service.create_enterprise(EnterpriseCreate(name="Enterprise To Delete"))
        pilot = self.service.create_pilot(
            PilotCreate(enterprise_id=enterprise.id, name="Child Pilot")
        )
        self.service.update_pilot(pilot.id, PilotUpdate(status="closed"))
        self.service.update_enterprise(enterprise.id, EnterpriseUpdate(status="closed"))

        response = self.client.delete(
            f"/admin/enterprises/{enterprise.id}",
            headers={"Authorization": "Bearer test-admin-token"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "deleted", "id": enterprise.id})
        self.assertIsNone(self.repository.get_enterprise(enterprise.id))
        self.assertIsNone(self.repository.get_pilot(pilot.id))

    @patch.dict("os.environ", {"ADMIN_API_TOKEN": "test-admin-token"}, clear=False)
    def test_public_token_validation_does_not_require_admin_auth(self) -> None:
        enterprise = self.service.create_enterprise(EnterpriseCreate(name="Public Validation"))
        pilot = self.service.create_pilot(
            PilotCreate(enterprise_id=enterprise.id, name="Validation Pilot")
        )
        link = self.service.generate_link(pilot.id, TokenType.GLIMPSE_APP)
        raw_token = self.repository.tokens[link.token_id]["token_recoverable"]

        response = self.client.post(
            "/access/validate",
            json={"token": raw_token, "token_type": "glimpse_app"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["valid"])
        self.assertEqual(response.json()["pilot_id"], pilot.id)


if __name__ == "__main__":
    unittest.main()
