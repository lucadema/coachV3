import unittest
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi.testclient import TestClient

from admin_backend.app import app
from admin_backend.models import PilotStatus
from admin_backend.routes import get_service
from admin_backend.service import AdminService, hash_access_token


def _dashboard_context(
    *,
    token_id: str = "token-1",
    pilot_id: str = "pilot-1",
    pilot_status: str = "active",
    token_status: str = "active",
    expires_at: datetime | None = None,
) -> dict[str, Any]:
    return {
        "token_id": token_id,
        "pilot_id": pilot_id,
        "token_status": token_status,
        "token_expires_at": expires_at,
        "pilot_name": "Leadership Pilot",
        "pilot_status": pilot_status,
        "enterprise_name": "Aether Works",
    }


class FakeDashboardRepository:
    def __init__(self) -> None:
        self.contexts_by_hash: dict[str, dict[str, Any]] = {}
        self.problem_counts: dict[str, dict[str, int]] = {}
        self.engagement_counts: dict[str, dict[str, int]] = {}
        self.feedback_rows: dict[str, list[Any]] = {}
        self.used_token_ids: list[str] = []

    def add_token(self, token: str, context: dict[str, Any]) -> None:
        self.contexts_by_hash[hash_access_token(token)] = context

    def find_dashboard_token_context(self, token_hash: str) -> dict[str, Any] | None:
        return self.contexts_by_hash.get(token_hash)

    def mark_token_used(self, token_id: str) -> None:
        self.used_token_ids.append(token_id)

    def get_problem_category_counts(self, pilot_id: str) -> dict[str, int]:
        return self.problem_counts.get(pilot_id, {})

    def get_engagement_signal_counts(self, pilot_id: str) -> dict[str, int]:
        return self.engagement_counts.get(pilot_id, {})

    def list_feedback_responses_for_pilot(self, pilot_id: str) -> list[Any]:
        return self.feedback_rows.get(pilot_id, [])


class DashboardServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeDashboardRepository()
        self.service = AdminService(self.repository)

    def test_active_dashboard_token_returns_aggregated_pilot_data(self) -> None:
        token = "dashboard-token"
        self.repository.add_token(token, _dashboard_context())
        self.repository.problem_counts["pilot-1"] = {
            "siloed_thinking": 3,
            "lack_of_clarity_alignment": 2,
            "unknown_value": 99,
        }
        self.repository.engagement_counts["pilot-1"] = {
            "no_visible_risk": 4,
            "frustration_signal": 1,
        }
        self.repository.feedback_rows["pilot-1"] = [
            {
                "weekly_time_saved": {
                    "value": "up_to_60_minutes",
                    "numeric_value": 30,
                },
                "people_who_would_benefit": {
                    "value": "me_and_1_to_10_others",
                    "numeric_value": 6,
                },
                "flag_to_organisation": True,
            },
            {
                "weekly_time_saved": {"value": "not_sure_or_not_applicable"},
                "people_who_would_benefit": {
                    "value": "me_and_1_to_10_others",
                    "numeric_value": 6,
                },
                "flag_to_organisation": False,
            },
            {
                "flag_to_organisation": "yes",
            },
        ]

        dashboard = self.service.get_dashboard_data(token)

        self.assertTrue(dashboard.available)
        self.assertEqual(dashboard.enterprise_name, "Aether Works")
        self.assertEqual(dashboard.pilot_name, "Leadership Pilot")
        self.assertEqual(dashboard.pilot_status, PilotStatus.ACTIVE)
        category_counts = {bucket.value: bucket.count for bucket in dashboard.problem_categories}
        self.assertEqual(category_counts["siloed_thinking"], 3)
        self.assertEqual(category_counts["lack_of_clarity_alignment"], 2)
        self.assertNotIn("unknown_value", category_counts)
        signal_counts = {bucket.value: bucket.count for bucket in dashboard.engagement_signals}
        self.assertEqual(signal_counts["no_visible_risk"], 4)
        self.assertEqual(signal_counts["disengagement_risk"], 0)
        self.assertEqual(dashboard.value_unlocked.qualifying_responses_count, 1)
        self.assertEqual(dashboard.value_unlocked.monthly_minutes, 720)
        self.assertEqual(
            dashboard.value_unlocked.flag_to_organisation,
            {"yes_count": 1, "no_count": 1},
        )
        self.assertEqual(self.repository.used_token_ids, ["token-1"])

    def test_value_inputs_use_configured_numeric_mappings_for_raw_option_values(self) -> None:
        token = "dashboard-token"
        self.repository.add_token(token, _dashboard_context())
        self.repository.feedback_rows["pilot-1"] = [
            {
                "feedback_pack_id": "pilot_impact_questions",
                "feedback_responses": {
                    "weekly_time_saved": "more_than_an_hour",
                    "people_who_would_benefit": "me_and_21_plus_others",
                    "flag_to_organisation": True,
                },
            },
            {
                "feedback_pack_id": "pilot_impact_questions",
                "feedback_responses": {
                    "weekly_time_saved": "not_sure_or_not_applicable",
                    "people_who_would_benefit": "me_and_1_to_10_others",
                    "flag_to_organisation": False,
                },
            },
        ]

        dashboard = self.service.get_dashboard_data(token)

        self.assertTrue(dashboard.available)
        self.assertEqual(dashboard.value_unlocked.qualifying_responses_count, 1)
        self.assertEqual(dashboard.value_unlocked.monthly_minutes, 9000)
        self.assertEqual(
            dashboard.value_unlocked.flag_to_organisation,
            {"yes_count": 1, "no_count": 1},
        )

    def test_paused_pilot_can_render_dashboard(self) -> None:
        token = "paused-dashboard-token"
        self.repository.add_token(token, _dashboard_context(pilot_status="paused"))

        dashboard = self.service.get_dashboard_data(token)

        self.assertTrue(dashboard.available)
        self.assertEqual(dashboard.pilot_status, PilotStatus.PAUSED)

    def test_draft_and_closed_pilots_return_safe_unavailable_response(self) -> None:
        for status in ("draft", "closed"):
            with self.subTest(status=status):
                repository = FakeDashboardRepository()
                repository.add_token("token", _dashboard_context(pilot_status=status))
                dashboard = AdminService(repository).get_dashboard_data("token")

                self.assertFalse(dashboard.available)
                self.assertIsNone(dashboard.enterprise_name)
                self.assertEqual(dashboard.problem_categories, [])
                self.assertEqual(repository.used_token_ids, [])

    def test_invalid_inactive_and_expired_tokens_return_unavailable_response(self) -> None:
        expired_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        cases = [
            ("missing", None),
            ("revoked", _dashboard_context(token_status="revoked")),
            ("expired", _dashboard_context(expires_at=expired_at)),
        ]

        for token, context in cases:
            with self.subTest(token=token):
                repository = FakeDashboardRepository()
                if context is not None:
                    repository.add_token(token, context)
                dashboard = AdminService(repository).get_dashboard_data(token)

                self.assertFalse(dashboard.available)
                self.assertIsNone(dashboard.pilot_name)


class DashboardRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeDashboardRepository()
        self.service = AdminService(self.repository)
        app.dependency_overrides[get_service] = lambda: self.service
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_dashboard_route_is_public_and_returns_data_for_active_pilot(self) -> None:
        self.repository.add_token("route-token", _dashboard_context())

        response = self.client.get("/dashboard/route-token")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["available"])
        self.assertEqual(body["enterprise_name"], "Aether Works")

    def test_dashboard_route_returns_safe_unavailable_for_invalid_token(self) -> None:
        response = self.client.get("/dashboard/not-found")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["available"], False)


if __name__ == "__main__":
    unittest.main()
