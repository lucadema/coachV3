import tempfile
import unittest
from pathlib import Path

from backend.enums import ChatRole, Stage, SynthesisState
from backend.models import ChatMessage, Session
from backend.telemetry.assessment import (
    ENGAGEMENT_SIGNAL_VALUES,
    PROBLEM_CATEGORY_VALUES,
    assess_synthesis_telemetry,
    parse_controlled_json_value,
)


PROMPTS = """
problem_category_prompt: |
  Classify the synthesis.
engagement_signal_prompt: |
  Classify the conversation.
"""


class TelemetryAssessmentParsingTests(unittest.TestCase):
    def test_valid_problem_category_response_returns_value(self) -> None:
        self.assertEqual(
            parse_controlled_json_value(
                '{"problem_category": "siloed_thinking"}',
                field_name="problem_category",
                allowed_values=PROBLEM_CATEGORY_VALUES,
            ),
            "siloed_thinking",
        )

    def test_invalid_problem_category_response_returns_none(self) -> None:
        self.assertIsNone(
            parse_controlled_json_value(
                '{"problem_category": "personal_issue"}',
                field_name="problem_category",
                allowed_values=PROBLEM_CATEGORY_VALUES,
            )
        )

    def test_valid_engagement_signal_response_returns_value(self) -> None:
        self.assertEqual(
            parse_controlled_json_value(
                '{"engagement_signal": "frustration_signal"}',
                field_name="engagement_signal",
                allowed_values=ENGAGEMENT_SIGNAL_VALUES,
            ),
            "frustration_signal",
        )

    def test_invalid_engagement_signal_response_returns_none(self) -> None:
        self.assertIsNone(
            parse_controlled_json_value(
                '{"engagement_signal": ["frustration_signal"]}',
                field_name="engagement_signal",
                allowed_values=ENGAGEMENT_SIGNAL_VALUES,
            )
        )

    def test_prose_wrapped_json_is_rejected(self) -> None:
        self.assertIsNone(
            parse_controlled_json_value(
                'Here you go: {"problem_category": "siloed_thinking"}',
                field_name="problem_category",
                allowed_values=PROBLEM_CATEGORY_VALUES,
            )
        )


class TelemetryAssessmentFlowTests(unittest.TestCase):
    def _write_config(self, text: str) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "telemetry_assessment_prompts.yaml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_missing_yaml_leaves_fields_null_without_llm_call(self) -> None:
        calls: list[tuple[str, str, str | None]] = []
        session = Session(
            session_id="session-1",
            stage=Stage.SYNTHESIS.value,
            state=SynthesisState.VALIDATING.value,
        )

        assess_synthesis_telemetry(
            session,
            synthesis_text="Teams are not sharing context.",
            config_path="/tmp/coachv3-missing-prompts.yaml",
            raw_llm_caller=lambda prompt, operation, session_id: calls.append(
                (prompt, operation, session_id)
            )
            or None,
        )

        self.assertIsNone(session.problem_category)
        self.assertIsNone(session.engagement_signal)
        self.assertEqual(calls, [])

    def test_valid_responses_set_assessment_fields(self) -> None:
        path = self._write_config(PROMPTS)
        replies = {
            "telemetry.problem_category": '{"problem_category": "siloed_thinking"}',
            "telemetry.engagement_signal": '{"engagement_signal": "frustration_signal"}',
        }
        session = Session(
            session_id="session-1",
            stage=Stage.SYNTHESIS.value,
            state=SynthesisState.VALIDATING.value,
            chat_history=[
                ChatMessage(
                    role=ChatRole.USER,
                    message="My team does not hear about decisions until too late.",
                )
            ],
        )

        assess_synthesis_telemetry(
            session,
            synthesis_text="The teams operate without enough shared context.",
            config_path=path,
            raw_llm_caller=lambda _prompt, operation, _session_id: replies[operation],
        )

        self.assertEqual(session.problem_category, "siloed_thinking")
        self.assertEqual(session.engagement_signal, "frustration_signal")

    def test_invalid_responses_leave_fields_null(self) -> None:
        path = self._write_config(PROMPTS)
        session = Session(
            session_id="session-1",
            stage=Stage.SYNTHESIS.value,
            state=SynthesisState.VALIDATING.value,
            chat_history=[ChatMessage(role=ChatRole.USER, message="There is a work issue.")],
        )

        assess_synthesis_telemetry(
            session,
            synthesis_text="The synthesis is work-related.",
            config_path=path,
            raw_llm_caller=lambda _prompt, _operation, _session_id: '{"value": "bad"}',
        )

        self.assertIsNone(session.problem_category)
        self.assertIsNone(session.engagement_signal)

    def test_llm_failure_does_not_raise(self) -> None:
        path = self._write_config(PROMPTS)
        session = Session(
            session_id="session-1",
            stage=Stage.SYNTHESIS.value,
            state=SynthesisState.VALIDATING.value,
            chat_history=[ChatMessage(role=ChatRole.USER, message="There is a work issue.")],
        )

        def failing_caller(_prompt: str, _operation: str, _session_id: str | None) -> str:
            raise RuntimeError("provider unavailable")

        with self.assertLogs("backend.telemetry.assessment", level="WARNING"):
            assess_synthesis_telemetry(
                session,
                synthesis_text="The synthesis is work-related.",
                config_path=path,
                raw_llm_caller=failing_caller,
            )

        self.assertIsNone(session.problem_category)
        self.assertIsNone(session.engagement_signal)

    def test_idempotency_does_not_overwrite_existing_value(self) -> None:
        path = self._write_config(PROMPTS)
        operations: list[str] = []
        session = Session(
            session_id="session-1",
            stage=Stage.SYNTHESIS.value,
            state=SynthesisState.VALIDATING.value,
            problem_category="siloed_thinking",
            chat_history=[ChatMessage(role=ChatRole.USER, message="There is a work issue.")],
        )

        assess_synthesis_telemetry(
            session,
            synthesis_text="The synthesis is work-related.",
            config_path=path,
            raw_llm_caller=lambda _prompt, operation, _session_id: operations.append(operation)
            or '{"engagement_signal": "no_visible_risk"}',
        )

        self.assertEqual(session.problem_category, "siloed_thinking")
        self.assertEqual(session.engagement_signal, "no_visible_risk")
        self.assertEqual(operations, ["telemetry.engagement_signal"])

    def test_engagement_source_uses_conversation_not_generated_synthesis(self) -> None:
        path = self._write_config(PROMPTS)
        prompts: list[str] = []
        session = Session(
            session_id="session-1",
            stage=Stage.SYNTHESIS.value,
            state=SynthesisState.VALIDATING.value,
            problem_category="siloed_thinking",
            chat_history=[
                ChatMessage(role=ChatRole.USER, message="People stop raising blockers."),
                ChatMessage(role=ChatRole.ASSISTANT, message="What happens next?"),
            ],
        )

        assess_synthesis_telemetry(
            session,
            synthesis_text="Generated synthesis text should not be in transcript.",
            config_path=path,
            raw_llm_caller=lambda prompt, _operation, _session_id: prompts.append(prompt)
            or '{"engagement_signal": "voice_suppression_signal"}',
        )

        self.assertIn("People stop raising blockers.", prompts[0])
        self.assertNotIn("Generated synthesis text should not be in transcript.", prompts[0])


if __name__ == "__main__":
    unittest.main()
