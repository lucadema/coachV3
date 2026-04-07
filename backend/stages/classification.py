"""
Classification stage module for Coach V3.

Purpose
-------
This module owns the local FSM and stage-specific behaviour for the
Classification macro-stage.

This is the first real stage implementation in V3. It owns the local
classification FSM and uses backend.engine for prompt/config loading plus
deterministic first-slice classification support.
"""

from pathlib import Path

from backend.engine import evaluate
from backend.enums import ClassificationState, Stage
from backend.models import Session, StageReply


STAGE_YAML_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "classification.yaml"
)

CLASSIFICATION_OUTPUT_INSTRUCTION = """
Return JSON only with exactly these keys:
- classification_label: one of VALID, AMBIGUOUS, OUT_OF_SCOPE, DISTRESS
- evaluation_message: concise internal evaluation summary
- coach_message: concise user-facing classification response
- debug_message: concise trace/debug detail
"""

OUTCOME_BY_CLASSIFICATION_LABEL = {
    "valid": "valid",
    "ambiguous": "ambiguous",
    "invalid": "invalid",
    "out_of_scope": "invalid",
    "distress": "invalid",
}

DEFAULT_COACH_MESSAGE_BY_LABEL = {
    "valid": (
        "Thanks. That sounds like a real situation we can work through, so "
        "let's begin."
    ),
    "ambiguous": (
        "I can help, but I need one clearer sentence about the decision, "
        "challenge, or conflict you want coaching on."
    ),
    "invalid": (
        "I can't continue this session because the opening message does not "
        "describe a coaching issue I can work on here."
    ),
    "out_of_scope": (
        "I can't continue this session because the opening message is outside "
        "the coaching issue this process is designed for."
    ),
    "distress": (
        "I can't continue this coaching flow because the message sounds better "
        "suited to immediate wellbeing support than this process."
    ),
}


def _join_debug_lines(*lines: str) -> str:
    """Build a readable debug trace without dropping earlier details."""
    return "\n".join(line for line in lines if line)


def _evaluate_classification(session: Session) -> dict:
    """Evaluate classification and normalize the result for the local FSM."""
    result = evaluate(
        stage_yaml_path=STAGE_YAML_PATH,
        state_name=session.state,
        user_message=session.user_message,
        history=session.chat_history,
        context=session.stage_context,
        output_instruction=CLASSIFICATION_OUTPUT_INSTRUCTION,
        structured=True,
    )

    if not isinstance(result, dict):
        return {
            "outcome": "invalid",
            "evaluation_message": (
                "Classification result: invalid engine output. The engine "
                "returned plain text where structured output was required."
            ),
            "coach_message": (
                "I can't continue because classification returned an "
                "unexpected response."
            ),
            "debug_message": (
                "classification_engine_error=plain_text_output "
                f"engine_output={result}"
            ),
        }

    raw_outcome = str(
        result.get("outcome")
        or result.get("classification_label")
        or "invalid"
    ).strip().lower()
    outcome = OUTCOME_BY_CLASSIFICATION_LABEL.get(raw_outcome, raw_outcome)
    missing_fields = []
    if not (result.get("outcome") or result.get("classification_label")):
        missing_fields.append("classification_label")
    missing_fields.extend(
        field
        for field in ("evaluation_message", "coach_message", "debug_message")
        if not result.get(field)
    )

    result["outcome"] = outcome
    result["evaluation_message"] = result.get("evaluation_message") or (
        f"Classification result: {outcome}. Engine label: {raw_outcome}. The "
        "engine returned structured output without an evaluation_message."
    )
    result["coach_message"] = (
        result.get("coach_message")
        or DEFAULT_COACH_MESSAGE_BY_LABEL.get(raw_outcome)
        or DEFAULT_COACH_MESSAGE_BY_LABEL.get(outcome)
        or "I can't continue because classification returned an unexpected result."
    )
    result["debug_message"] = _join_debug_lines(
        str(result.get("debug_message") or "classification_engine_debug=missing"),
        (
            f"classification_engine_missing_fields={','.join(missing_fields)}"
            if missing_fields
            else ""
        ),
        f"classification_raw_outcome={raw_outcome}",
        f"classification_normalized_outcome={outcome}",
    )
    return result


def handle_stage(session: Session) -> StageReply:
    """
    Handle one turn for the Classification stage.

    Local FSM:
    - evaluating -> ambiguous
    - evaluating -> completed
    - evaluating -> cancelled
    - ambiguous -> completed
    - ambiguous -> cancelled

    Bounded ambiguity rule:
    - if the user is already in ambiguous and the clarification still does not
      resolve the issue, cancel rather than looping forever
    """
    current_state = session.state

    match current_state:
        case "evaluating":
            result = _evaluate_classification(session)
            session.evaluation_message = result["evaluation_message"]

            match result["outcome"]:
                case "valid":
                    session.state = ClassificationState.COMPLETED.value
                    session.cancelled = False
                    session.coach_message = result["coach_message"]
                    session.debug_message = _join_debug_lines(
                        result["debug_message"],
                        "classification_transition=evaluating_to_completed",
                        "classification_resolution=accepted",
                        f"classification_state_out={session.state}",
                        f"next_stage={Stage.COACHING.value}",
                    )
                    return StageReply(session=session, next_stage=Stage.COACHING)

                case "ambiguous":
                    session.state = ClassificationState.AMBIGUOUS.value
                    session.cancelled = False
                    session.coach_message = result["coach_message"]
                    session.debug_message = _join_debug_lines(
                        result["debug_message"],
                        "classification_transition=evaluating_to_ambiguous",
                        "classification_resolution=needs_clarification",
                        f"classification_state_out={session.state}",
                    )
                    return StageReply(session=session)

                case "invalid":
                    session.state = ClassificationState.CANCELLED.value
                    session.cancelled = True
                    session.coach_message = result["coach_message"]
                    session.debug_message = _join_debug_lines(
                        result["debug_message"],
                        "classification_transition=evaluating_to_cancelled",
                        "classification_resolution=rejected",
                        f"classification_state_out={session.state}",
                    )
                    return StageReply(session=session)

                case _:
                    session.state = ClassificationState.CANCELLED.value
                    session.cancelled = True
                    session.coach_message = (
                        "I can't continue because classification returned an "
                        "unexpected result."
                    )
                    session.debug_message = _join_debug_lines(
                        result["debug_message"],
                        "classification_transition=evaluating_to_cancelled",
                        "classification_resolution=unexpected_engine_outcome",
                        f"classification_outcome={result['outcome']}",
                        f"classification_state_out={session.state}",
                    )
                    return StageReply(session=session)

        case "ambiguous":
            result = _evaluate_classification(session)
            session.evaluation_message = result["evaluation_message"]

            match result["outcome"]:
                case "valid":
                    session.state = ClassificationState.COMPLETED.value
                    session.cancelled = False
                    session.coach_message = result["coach_message"]
                    session.debug_message = _join_debug_lines(
                        result["debug_message"],
                        "classification_transition=ambiguous_to_completed",
                        "classification_resolution=accepted_after_clarification",
                        f"classification_state_out={session.state}",
                        f"next_stage={Stage.COACHING.value}",
                    )
                    return StageReply(session=session, next_stage=Stage.COACHING)

                case "ambiguous" | "invalid":
                    session.state = ClassificationState.CANCELLED.value
                    session.cancelled = True
                    session.evaluation_message = (
                        "Classification result: cancelled after clarification. "
                        f"The follow-up still did not resolve the intake. "
                        f"Underlying decision: {result['evaluation_message']}"
                    )
                    session.coach_message = (
                        "I still can't identify a clear coaching issue from "
                        "the clarification, so I'll stop here rather than keep "
                        "looping. Please start a new session with the specific "
                        "decision, challenge, or conflict you want to work on."
                    )
                    session.debug_message = _join_debug_lines(
                        result["debug_message"],
                        "classification_transition=ambiguous_to_cancelled",
                        "bounded_ambiguity_triggered=true",
                        "classification_resolution=rejected_after_clarification",
                        f"classification_state_out={session.state}",
                    )
                    return StageReply(session=session)

                case _:
                    session.state = ClassificationState.CANCELLED.value
                    session.cancelled = True
                    session.coach_message = (
                        "I can't continue because classification returned an "
                        "unexpected result."
                    )
                    session.debug_message = _join_debug_lines(
                        result["debug_message"],
                        "classification_transition=ambiguous_to_cancelled",
                        "bounded_ambiguity_triggered=true",
                        "classification_resolution=unexpected_engine_outcome",
                        f"classification_outcome={result['outcome']}",
                        f"classification_state_out={session.state}",
                    )
                    return StageReply(session=session)

        case _:
            session.state = ClassificationState.CANCELLED.value
            session.cancelled = True
            session.evaluation_message = (
                "Classification result: invalid internal state. The stage "
                "received an unexpected classification state."
            )
            session.coach_message = (
                "I can't continue because the classification stage entered an "
                "unexpected state."
            )
            session.debug_message = _join_debug_lines(
                "classification_stage_error=unexpected_state",
                f"classification_state_in={current_state}",
                f"classification_state_out={session.state}",
            )
            return StageReply(session=session)
