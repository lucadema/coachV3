import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.api import app
from backend.controller import _telemetry_generation_flags, handle_user_msg
from backend.enums import ClosureState, PathwaysState, Stage, SynthesisState
from backend.models import Session
from backend.state_store import state_store


class TelemetryGenerationFlagTests(unittest.TestCase):
    def test_synthesis_validating_marks_synthesis_generated_only(self) -> None:
        session = Session(
            session_id="session-1",
            stage=Stage.SYNTHESIS.value,
            state=SynthesisState.VALIDATING.value,
        )

        self.assertEqual(_telemetry_generation_flags(session), (True, None))

    def test_pathways_presenting_marks_both_generated_outputs(self) -> None:
        session = Session(
            session_id="session-1",
            stage=Stage.PATHWAYS.value,
            state=PathwaysState.PRESENTING.value,
        )

        self.assertEqual(_telemetry_generation_flags(session), (True, True))

    def test_completed_closure_marks_both_generated_outputs(self) -> None:
        session = Session(
            session_id="session-1",
            stage=Stage.CLOSURE.value,
            state=ClosureState.COMPLETED.value,
            completed=True,
        )

        self.assertEqual(_telemetry_generation_flags(session), (True, True))


class ClientTelemetryEventRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        state_store.clear()
        self.client = TestClient(app)
        state_store.save_session(
            Session(
                session_id="session-1",
                stage=Stage.CLOSURE.value,
                state=ClosureState.COMPLETED.value,
                completed=True,
                turn_count=8,
            )
        )

    def tearDown(self) -> None:
        state_store.clear()

    @patch("backend.api.telemetry.record_session_updated")
    def test_pdf_download_event_sets_pdf_flag(self, mock_record_session_updated) -> None:
        response = self.client.post(
            "/telemetry/session_event",
            json={"session_id": "session-1", "event": "pdf_downloaded"},
        )

        self.assertEqual(response.status_code, 200)
        mock_record_session_updated.assert_called_once_with(
            session_id="session-1",
            stage=Stage.CLOSURE.value,
            state=ClosureState.COMPLETED.value,
            turns_count=8,
            pdf_downloaded=True,
            status="completed",
            session_label=None,
            pilot_id=None,
        )

    @patch("backend.api.telemetry.record_feedback_submitted")
    def test_feedback_event_records_feedback_answers(self, mock_record_feedback) -> None:
        response = self.client.post(
            "/telemetry/session_event",
            json={
                "session_id": "session-1",
                "event": "feedback_submitted",
                "answer_1": True,
                "answer_2": False,
                "dropdown_values": ["Receiving structured pathways rather than a generic answer"],
                "payload": {"source": "test"},
            },
        )

        self.assertEqual(response.status_code, 200)
        mock_record_feedback.assert_called_once_with(
            session_id="session-1",
            answer_1=True,
            answer_2=False,
            dropdown_values=["Receiving structured pathways rather than a generic answer"],
            payload={"source": "test"},
            pilot_id=None,
        )

    def test_client_event_requires_existing_session(self) -> None:
        response = self.client.post(
            "/telemetry/session_event",
            json={"session_id": "missing", "event": "pdf_downloaded"},
        )

        self.assertEqual(response.status_code, 404)


class PilotContextCaptureTests(unittest.TestCase):
    def setUp(self) -> None:
        state_store.clear()
        state_store.save_session(
            Session(
                session_id="session-1",
                stage=Stage.CLASSIFICATION.value,
                state="evaluating",
            )
        )

    def tearDown(self) -> None:
        state_store.clear()

    @patch("backend.controller.telemetry.record_session_started")
    @patch("backend.controller.telemetry.record_session_updated")
    @patch("backend.controller.pilot_access.resolve_glimpse_pilot_id")
    @patch("backend.controller._run_stage_loop")
    def test_user_turn_resolves_access_token_to_pilot_id(
        self,
        mock_run_stage_loop,
        mock_resolve_pilot,
        mock_record_updated,
        mock_record_started,
    ) -> None:
        mock_resolve_pilot.return_value = "pilot-1"
        mock_run_stage_loop.side_effect = lambda session: session

        session = handle_user_msg(
            session_id="session-1",
            user_message="I need clarity on a decision.",
            client_context={"accessToken": "AbC_1234567890-token_value"},
        )

        self.assertEqual(session.pilot_id, "pilot-1")
        mock_record_started.assert_called_once()
        self.assertEqual(mock_record_started.call_args.kwargs["pilot_id"], "pilot-1")
        self.assertEqual(mock_record_updated.call_args.kwargs["pilot_id"], "pilot-1")

    @patch("backend.controller.telemetry.record_session_started")
    @patch("backend.controller.telemetry.record_session_updated")
    @patch("backend.controller.assess_synthesis_telemetry")
    @patch("backend.controller._run_stage_loop")
    def test_synthesis_generation_triggers_assessment_before_update(
        self,
        mock_run_stage_loop,
        mock_assess,
        mock_record_updated,
        _mock_record_started,
    ) -> None:
        def complete_synthesis(session: Session) -> Session:
            session.stage = Stage.SYNTHESIS.value
            session.state = SynthesisState.VALIDATING.value
            session.coach_message = "The synthesis is about unclear ownership."
            session.problem_category = "lack_of_clarity_alignment"
            session.engagement_signal = "frustration_signal"
            return session

        mock_run_stage_loop.side_effect = complete_synthesis

        handle_user_msg("session-1", "We keep missing ownership on decisions.")

        mock_assess.assert_called_once()
        self.assertEqual(
            mock_assess.call_args.kwargs["synthesis_text"],
            "The synthesis is about unclear ownership.",
        )
        self.assertEqual(
            mock_record_updated.call_args.kwargs["problem_category"],
            "lack_of_clarity_alignment",
        )
        self.assertEqual(
            mock_record_updated.call_args.kwargs["engagement_signal"],
            "frustration_signal",
        )


if __name__ == "__main__":
    unittest.main()
