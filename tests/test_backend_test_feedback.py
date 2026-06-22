import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend_test.main import _SESSIONS, _get_default_feedback_pack, app


class TestBackendFeedbackContractTests(unittest.TestCase):
    def setUp(self) -> None:
        _SESSIONS.clear()
        self.client = TestClient(app)
        response = self.client.get("/session_initialise")
        self.assertEqual(response.status_code, 200)
        self.session_id = response.json()["session_id"]

    def test_feedback_form_matches_yaml_contract(self) -> None:
        default_entry = _get_default_feedback_pack()
        self.assertIsNotNone(default_entry)
        default_pack_id, default_pack = default_entry or ("", {})

        response = self.client.get(f"/coach/v2/feedback-form?session_id={self.session_id}")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["show_feedback"])
        self.assertEqual(body["feedback_pack_id"], default_pack_id)
        self.assertEqual(body["survey_query"], default_pack["survey_query"])
        self.assertEqual(body["questions"][0]["id"], default_pack["questions"][0]["id"])

    def test_feedback_form_uses_pilot_feedback_pack_when_available(self) -> None:
        _SESSIONS[self.session_id]["pilot_id"] = "pilot-1"

        with patch(
            "backend_test.main._get_pilot_feedback_pack_id",
            return_value="pilot_impact_questions",
        ) as mock_get_pack:
            response = self.client.get(f"/coach/v2/feedback-form?session_id={self.session_id}")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["feedback_pack_id"], "pilot_impact_questions")
        self.assertEqual(body["questions"][0]["id"], "weekly_time_saved")
        mock_get_pack.assert_called_once_with("pilot-1")

    def test_user_message_can_seed_test_pilot_context(self) -> None:
        with (
            patch("backend_test.main.RESPONSE_DELAY_SECONDS", 0),
            patch("backend_test.main.telemetry.record_session_started"),
            patch("backend_test.main.telemetry.record_session_updated"),
            patch("backend_test.main.telemetry.record_session_closed"),
        ):
            response = self.client.post(
                "/user_message",
                json={
                    "session_id": self.session_id,
                    "user_message": "Here is my challenge.",
                    "client_context": {"pilot_id": "pilot-1"},
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(_SESSIONS[self.session_id]["pilot_id"], "pilot-1")

    def test_user_message_resolves_token_to_pilot_context(self) -> None:
        with (
            patch("backend_test.main.RESPONSE_DELAY_SECONDS", 0),
            patch(
                "backend_test.main._resolve_glimpse_pilot_id",
                return_value="pilot-1",
            ) as mock_resolve,
            patch("backend_test.main.telemetry.record_session_started"),
            patch("backend_test.main.telemetry.record_session_updated"),
            patch("backend_test.main.telemetry.record_session_closed"),
        ):
            response = self.client.post(
                "/user_message",
                json={
                    "session_id": self.session_id,
                    "user_message": "Here is my challenge.",
                    "client_context": {"accessToken": "a" * 24},
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(_SESSIONS[self.session_id]["pilot_id"], "pilot-1")
        mock_resolve.assert_called_once_with("a" * 24)

    def test_user_message_rejects_invalid_token(self) -> None:
        with (
            patch("backend_test.main.RESPONSE_DELAY_SECONDS", 0),
            patch("backend_test.main._resolve_glimpse_pilot_id", return_value=None),
        ):
            response = self.client.post(
                "/user_message",
                json={
                    "session_id": self.session_id,
                    "user_message": "Here is my challenge.",
                    "client_context": {"access_token": "b" * 24},
                },
            )

        self.assertEqual(response.status_code, 403)

    def test_feedback_form_uses_pack_from_token_resolved_pilot(self) -> None:
        with (
            patch("backend_test.main.RESPONSE_DELAY_SECONDS", 0),
            patch("backend_test.main._resolve_glimpse_pilot_id", return_value="pilot-1"),
            patch(
                "backend_test.main._get_pilot_feedback_pack_id",
                return_value="pilot_impact_questions",
            ) as mock_get_pack,
            patch("backend_test.main.telemetry.record_session_started"),
            patch("backend_test.main.telemetry.record_session_updated"),
            patch("backend_test.main.telemetry.record_session_closed"),
        ):
            user_response = self.client.post(
                "/user_message",
                json={
                    "session_id": self.session_id,
                    "user_message": "Here is my challenge.",
                    "client_context": {"token": "c" * 24},
                },
            )
            feedback_response = self.client.get(
                f"/coach/v2/feedback-form?session_id={self.session_id}"
            )

        self.assertEqual(user_response.status_code, 200)
        self.assertEqual(feedback_response.status_code, 200)
        self.assertEqual(feedback_response.json()["feedback_pack_id"], "pilot_impact_questions")
        mock_get_pack.assert_called_once_with("pilot-1")

    def test_feedback_form_falls_back_when_pilot_pack_is_missing(self) -> None:
        _SESSIONS[self.session_id]["pilot_id"] = "pilot-1"

        with patch(
            "backend_test.main._get_pilot_feedback_pack_id",
            return_value=None,
        ):
            response = self.client.get(f"/coach/v2/feedback-form?session_id={self.session_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["feedback_pack_id"], "glimpse_default")

    def test_feedback_form_falls_back_when_pilot_pack_is_unknown(self) -> None:
        _SESSIONS[self.session_id]["pilot_id"] = "pilot-1"

        with patch(
            "backend_test.main._get_pilot_feedback_pack_id",
            return_value="unknown_pack",
        ):
            response = self.client.get(f"/coach/v2/feedback-form?session_id={self.session_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["feedback_pack_id"], "glimpse_default")

    def test_user_message_records_session_telemetry(self) -> None:
        with (
            patch("backend_test.main.RESPONSE_DELAY_SECONDS", 0),
            patch("backend_test.main.telemetry.record_session_started") as mock_started,
            patch("backend_test.main.telemetry.record_session_updated") as mock_updated,
            patch("backend_test.main.telemetry.record_session_closed") as mock_closed,
        ):
            response = self.client.post(
                "/user_message",
                json={
                    "session_id": self.session_id,
                    "user_message": "Here is my challenge.",
                    "client_context": {"pilot_id": "pilot-1"},
                },
            )

        self.assertEqual(response.status_code, 200)
        mock_started.assert_called_once()
        self.assertEqual(mock_started.call_args.kwargs["session_id"], self.session_id)
        self.assertEqual(mock_started.call_args.kwargs["pilot_id"], "pilot-1")
        mock_updated.assert_called_once()
        self.assertEqual(mock_updated.call_args.kwargs["session_id"], self.session_id)
        self.assertEqual(mock_updated.call_args.kwargs["pilot_id"], "pilot-1")
        mock_closed.assert_not_called()

    def test_completed_user_message_records_closed_telemetry_once(self) -> None:
        _SESSIONS[self.session_id]["turn_count"] = 3
        _SESSIONS[self.session_id]["telemetry_started"] = True
        _SESSIONS[self.session_id]["pilot_id"] = "pilot-1"

        with (
            patch("backend_test.main.RESPONSE_DELAY_SECONDS", 0),
            patch("backend_test.main.telemetry.record_session_started") as mock_started,
            patch("backend_test.main.telemetry.record_session_updated") as mock_updated,
            patch("backend_test.main.telemetry.record_session_closed") as mock_closed,
        ):
            response = self.client.post(
                "/user_message",
                json={
                    "session_id": self.session_id,
                    "user_message": "Wrap up.",
                    "client_context": {},
                },
            )

        self.assertEqual(response.status_code, 200)
        mock_started.assert_not_called()
        mock_updated.assert_called_once()
        mock_closed.assert_called_once()
        self.assertEqual(mock_closed.call_args.kwargs["status"], "completed")
        self.assertEqual(mock_closed.call_args.kwargs["pilot_id"], "pilot-1")

    def test_feedback_submission_records_feedback_telemetry(self) -> None:
        _SESSIONS[self.session_id]["pilot_id"] = "pilot-1"

        with patch("backend_test.main.telemetry.record_feedback_submitted") as mock_feedback:
            response = self.client.post(
                "/coach/v2/feedback",
                json={
                    "session_id": self.session_id,
                    "feedback_pack_id": "glimpse_default",
                    "responses": {"helped_think_differently": True},
                },
            )

        self.assertEqual(response.status_code, 200)
        mock_feedback.assert_called_once()
        self.assertEqual(mock_feedback.call_args.kwargs["session_id"], self.session_id)
        self.assertEqual(mock_feedback.call_args.kwargs["feedback_pack_id"], "glimpse_default")
        self.assertEqual(mock_feedback.call_args.kwargs["pilot_id"], "pilot-1")

    def test_pdf_event_records_session_updated_telemetry(self) -> None:
        _SESSIONS[self.session_id]["pilot_id"] = "pilot-1"

        with patch("backend_test.main.telemetry.record_session_updated") as mock_updated:
            response = self.client.post(
                "/telemetry/session_event",
                json={"session_id": self.session_id, "event": "pdf_downloaded"},
            )

        self.assertEqual(response.status_code, 200)
        mock_updated.assert_called_once()
        self.assertTrue(mock_updated.call_args.kwargs["pdf_downloaded"])
        self.assertEqual(mock_updated.call_args.kwargs["pilot_id"], "pilot-1")


if __name__ == "__main__":
    unittest.main()
