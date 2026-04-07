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

from backend.engine import engine
from backend.enums import ClassificationState, Stage
from backend.models import Session, StageReply


def _join_debug_lines(*lines: str) -> str:
    """Build a readable debug trace without dropping earlier details."""
    return "\n".join(line for line in lines if line)


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
            result = engine.classify(session)
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
            result = engine.classify(session)
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
