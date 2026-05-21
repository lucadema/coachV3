import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.api import app
from backend.controller import _telemetry_generation_flags
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
        )

    def test_client_event_requires_existing_session(self) -> None:
        response = self.client.post(
            "/telemetry/session_event",
            json={"session_id": "missing", "event": "pdf_downloaded"},
        )

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
