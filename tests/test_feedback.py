import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.api import app
from backend.enums import ClosureState, Stage
from backend.feedback import (
    FeedbackConfigError,
    FeedbackSubmission,
    FeedbackValidationError,
    get_active_feedback_form,
    get_default_feedback_pack,
    get_feedback_pack,
    load_feedback_config,
    normalise_feedback_responses,
    store_feedback_submission,
)
from backend.models import Session
from backend.state_store import state_store


class FeedbackConfigTests(unittest.TestCase):
    def test_default_feedback_pack_loads(self) -> None:
        pack_entry = get_default_feedback_pack()

        self.assertIsNotNone(pack_entry)
        pack_id, pack = pack_entry or ("", None)
        self.assertEqual(pack_id, "glimpse_default")
        self.assertTrue(pack.survey_query)
        self.assertEqual(len(pack.questions), 5)
        self.assertEqual(pack.questions[0].id, "helped_think_differently")

    def test_missing_yaml_raises_config_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            with self.assertRaises(FeedbackConfigError):
                load_feedback_config(Path(temp_dir) / "missing.yaml")

    def test_invalid_yaml_shape_raises_config_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "feedback.yaml"
            path.write_text("- not-a-mapping\n", encoding="utf-8")

            with self.assertRaises(FeedbackConfigError):
                load_feedback_config(path)


class FeedbackValidationTests(unittest.TestCase):
    def test_required_questions_are_enforced(self) -> None:
        pack_entry = get_default_feedback_pack()
        self.assertIsNotNone(pack_entry)
        _pack_id, pack = pack_entry or ("", None)
        pack.questions[0].required = True

        with self.assertRaisesRegex(FeedbackValidationError, "required_feedback_question_missing"):
            normalise_feedback_responses(pack, {})

    def test_optional_unanswered_questions_are_omitted(self) -> None:
        pack = get_feedback_pack("glimpse_default")

        self.assertEqual(normalise_feedback_responses(pack, {}), {})

    def test_boolean_and_multi_select_answers_validate(self) -> None:
        pack = get_feedback_pack("glimpse_default")

        self.assertEqual(
            normalise_feedback_responses(
                pack,
                {
                    "helped_think_differently": True,
                    "valuable_moments": ["relevant_resolutions"],
                },
            ),
            {
                "helped_think_differently": True,
                "valuable_moments": ["relevant_resolutions"],
            },
        )

    def test_invalid_multi_select_value_is_rejected(self) -> None:
        pack = get_feedback_pack("glimpse_default")

        with self.assertRaisesRegex(FeedbackValidationError, "invalid_multi_select_option"):
            normalise_feedback_responses(pack, {"valuable_moments": ["unknown"]})

    def test_single_select_numeric_value_is_resolved_server_side(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "feedback.yaml"
            path.write_text(
                """
default_feedback_pack_id: default
feedback_packs:
  default:
    label: Default
    title: Title
    survey_query: Query?
    questions:
      - id: time_spent
        type: single_select
        text: Time spent?
        required: false
        options:
          - value: between_10_and_20
            label: Between 10 and 20 minutes
            numeric_value: 15
""",
                encoding="utf-8",
            )
            config = load_feedback_config(path)
            pack = config.feedback_packs["default"]

        self.assertEqual(
            normalise_feedback_responses(pack, {"time_spent": "between_10_and_20"}),
            {"time_spent": {"value": "between_10_and_20", "numeric_value": 15}},
        )


class FeedbackApiTests(unittest.TestCase):
    def setUp(self) -> None:
        state_store.clear()
        state_store.save_session(
            Session(
                session_id="session-1",
                stage=Stage.CLOSURE.value,
                state=ClosureState.COMPLETED.value,
                completed=True,
            )
        )
        self.client = TestClient(app)

    def tearDown(self) -> None:
        state_store.clear()

    def test_feedback_form_route_returns_default_pack(self) -> None:
        response = self.client.get("/coach/v2/feedback-form?session_id=session-1")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["show_feedback"])
        self.assertEqual(body["feedback_pack_id"], "glimpse_default")
        self.assertTrue(body["survey_query"])
        self.assertEqual(body["questions"][0]["id"], "helped_think_differently")

    @patch("backend.feedback.pilot_access.get_pilot_feedback_pack_id")
    def test_feedback_form_route_uses_pilot_feedback_pack(self, mock_get_pack) -> None:
        mock_get_pack.return_value = "pilot_impact_questions"
        stored = state_store.get_session("session-1")
        self.assertIsNotNone(stored)
        stored.pilot_id = "pilot-1"
        state_store.save_session(stored)

        response = self.client.get("/coach/v2/feedback-form?session_id=session-1")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["feedback_pack_id"], "pilot_impact_questions")
        self.assertEqual(body["questions"][0]["id"], "weekly_time_saved")
        mock_get_pack.assert_called_once_with("pilot-1")

    @patch("backend.feedback.pilot_access.get_pilot_feedback_pack_id")
    def test_feedback_form_route_falls_back_for_missing_pilot_pack(self, mock_get_pack) -> None:
        mock_get_pack.return_value = None
        stored = state_store.get_session("session-1")
        self.assertIsNotNone(stored)
        stored.pilot_id = "pilot-1"
        state_store.save_session(stored)

        response = self.client.get("/coach/v2/feedback-form?session_id=session-1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["feedback_pack_id"], "glimpse_default")

    @patch("backend.feedback.pilot_access.get_pilot_feedback_pack_id")
    def test_feedback_form_route_falls_back_for_unknown_pilot_pack(self, mock_get_pack) -> None:
        mock_get_pack.return_value = "unknown_pack"
        stored = state_store.get_session("session-1")
        self.assertIsNotNone(stored)
        stored.pilot_id = "pilot-1"
        state_store.save_session(stored)

        response = self.client.get("/coach/v2/feedback-form?session_id=session-1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["feedback_pack_id"], "glimpse_default")

    @patch("backend.feedback.pilot_access.get_pilot_feedback_pack_id")
    def test_active_feedback_form_falls_back_for_lookup_error(self, mock_get_pack) -> None:
        mock_get_pack.side_effect = RuntimeError("database unavailable")

        response = get_active_feedback_form(
            Session(
                session_id="session-lookup-error",
                stage=Stage.CLOSURE.value,
                state=ClosureState.COMPLETED.value,
                completed=True,
                pilot_id="pilot-1",
            )
        )

        self.assertTrue(response.show_feedback)
        self.assertEqual(response.feedback_pack_id, "glimpse_default")

    @patch("backend.feedback.telemetry.record_feedback_submitted")
    def test_feedback_submission_stores_normalised_session_fields(self, mock_record) -> None:
        response = self.client.post(
            "/coach/v2/feedback",
            json={
                "session_id": "session-1",
                "feedback_pack_id": "glimpse_default",
                "responses": {
                    "helped_think_differently": True,
                    "valuable_moments": ["relevant_resolutions"],
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        stored = state_store.get_session("session-1")
        self.assertIsNotNone(stored)
        self.assertEqual(stored.feedback_pack_id, "glimpse_default")
        self.assertEqual(
            stored.feedback_responses,
            {
                "helped_think_differently": True,
                "valuable_moments": ["relevant_resolutions"],
            },
        )
        mock_record.assert_called_once()

    def test_feedback_submission_rejects_invalid_question(self) -> None:
        response = self.client.post(
            "/coach/v2/feedback",
            json={
                "session_id": "session-1",
                "feedback_pack_id": "glimpse_default",
                "responses": {"unknown": True},
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_store_feedback_rejects_missing_session(self) -> None:
        with self.assertRaisesRegex(FeedbackValidationError, "session_not_found"):
            store_feedback_submission(
                FeedbackSubmission(
                    session_id="missing",
                    feedback_pack_id="glimpse_default",
                    responses={},
                )
            )


if __name__ == "__main__":
    unittest.main()
