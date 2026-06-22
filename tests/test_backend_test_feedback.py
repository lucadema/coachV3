import unittest

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

        with unittest.mock.patch(
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
        with unittest.mock.patch("backend_test.main.RESPONSE_DELAY_SECONDS", 0):
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
            unittest.mock.patch("backend_test.main.RESPONSE_DELAY_SECONDS", 0),
            unittest.mock.patch(
                "backend_test.main._resolve_glimpse_pilot_id",
                return_value="pilot-1",
            ) as mock_resolve,
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
            unittest.mock.patch("backend_test.main.RESPONSE_DELAY_SECONDS", 0),
            unittest.mock.patch("backend_test.main._resolve_glimpse_pilot_id", return_value=None),
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
            unittest.mock.patch("backend_test.main.RESPONSE_DELAY_SECONDS", 0),
            unittest.mock.patch("backend_test.main._resolve_glimpse_pilot_id", return_value="pilot-1"),
            unittest.mock.patch(
                "backend_test.main._get_pilot_feedback_pack_id",
                return_value="pilot_impact_questions",
            ) as mock_get_pack,
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

        with unittest.mock.patch(
            "backend_test.main._get_pilot_feedback_pack_id",
            return_value=None,
        ):
            response = self.client.get(f"/coach/v2/feedback-form?session_id={self.session_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["feedback_pack_id"], "glimpse_default")

    def test_feedback_form_falls_back_when_pilot_pack_is_unknown(self) -> None:
        _SESSIONS[self.session_id]["pilot_id"] = "pilot-1"

        with unittest.mock.patch(
            "backend_test.main._get_pilot_feedback_pack_id",
            return_value="unknown_pack",
        ):
            response = self.client.get(f"/coach/v2/feedback-form?session_id={self.session_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["feedback_pack_id"], "glimpse_default")


if __name__ == "__main__":
    unittest.main()
