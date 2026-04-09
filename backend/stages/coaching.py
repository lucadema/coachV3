"""
Coaching stage module for Coach V3.

This stage owns only its local FSM and stage-specific interpretation rules.
The controller owns the execution loop and engine calls.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.enums import CoachingState, Stage, StateType
from backend.models import Session, StageReply


STAGE_YAML_PATH = Path(__file__).resolve().parents[1] / "config" / "coaching.yaml"

EVALUATION_OUTPUT_INSTRUCTION = """
Return JSON only with exactly these keys:
- coaching_outcome: one of CONTINUE, COMPLETE, CANCEL
- evaluation_message: concise internal evaluation summary
- debug_message: concise trace/debug detail
"""

COACHING_OUTPUT_INSTRUCTION = """
Return JSON only with exactly these keys:
- coach_message: concise user-facing coaching response
- debug_message: concise trace/debug detail
"""

STATE_TYPE_BY_NAME = {
    CoachingState.GUIDING.value: StateType.EVALUATIVE.value,
    CoachingState.COMPLETED.value: StateType.TERMINAL.value,
    CoachingState.CANCELLED.value: StateType.TERMINAL.value,
}

OUTCOME_BY_COACHING_LABEL = {
    "continue": "continue",
    "complete": "complete",
    "cancel": "cancel",
}

DEFAULT_COACH_MESSAGE_BY_OUTCOME = {
    "continue": (
        "Let's keep clarifying this. What feels most important to understand "
        "about the problem right now?"
    ),
    "cancel": (
        "I'll stop the coaching flow here because it is not the right fit to "
        "continue this session."
    ),
    "cancelled": (
        "This coaching stage has already been stopped, so I won't reopen it "
        "inside this session."
    ),
}


def _join_debug_lines(*lines: str) -> str:
    """Build a readable debug trace without dropping earlier details."""
    return "\n".join(line for line in lines if line)


def _set_debug_message(session: Session, *lines: str) -> None:
    """Append stage-local debug lines without dropping earlier trace detail."""
    session.debug_message = _join_debug_lines(str(session.debug_message or ""), *lines)


def _normalize_label(value: Any) -> str:
    """Normalize model labels without interpreting YAML as FSM logic."""
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def get_state_type(state_name: str) -> str:
    """Return the V3.1 execution type for a Coaching state."""
    return STATE_TYPE_BY_NAME.get(state_name, StateType.TERMINAL.value)


def apply_evaluation(session: Session, result: Any) -> StageReply:
    """Interpret the engine evaluation result and apply local FSM changes."""
    current_state = session.state

    if not isinstance(result, dict):
        raw_outcome = "missing"
        outcome = "continue"
        evaluation_message = (
            "Coaching result: continue. The engine returned plain text where "
            "structured evaluation output was required."
        )
        debug_message = (
            "coaching_engine_error=plain_text_evaluation_output "
            f"engine_output={result}"
        )
    else:
        raw_outcome = _normalize_label(
            result.get("outcome")
            or result.get("coaching_outcome")
            or result.get("coaching_label")
        )
        outcome = OUTCOME_BY_COACHING_LABEL.get(raw_outcome, "continue")
        missing_fields = []
        if not (result.get("outcome") or result.get("coaching_outcome")):
            missing_fields.append("coaching_outcome")
        missing_fields.extend(
            field
            for field in ("evaluation_message", "debug_message")
            if not result.get(field)
        )
        evaluation_message = str(result.get("evaluation_message") or "").strip()
        if not evaluation_message or evaluation_message.startswith("TODO:"):
            evaluation_message = (
                f"Coaching result: {outcome}. Engine label: "
                f"{raw_outcome or 'missing'}. The engine returned structured "
                "output without an evaluation_message."
            )
        debug_message = _join_debug_lines(
            str(result.get("debug_message") or "coaching_engine_debug=missing"),
            (
                f"coaching_engine_missing_fields={','.join(missing_fields)}"
                if missing_fields
                else ""
            ),
        )

    session.stage_context["coaching_latest_outcome"] = outcome
    session.stage_context["coaching_latest_evaluation_message"] = evaluation_message
    session.stage_context["coaching_turn_count"] = (
        int(session.stage_context.get("coaching_turn_count", 0)) + 1
    )
    session.evaluation_message = evaluation_message

    match outcome:
        case "continue":
            session.state = CoachingState.GUIDING.value
            session.cancelled = False
            _set_debug_message(
                session,
                debug_message,
                f"coaching_raw_outcome={raw_outcome or 'missing'}",
                f"coaching_normalized_outcome={outcome}",
                "coaching_transition=guiding_to_guiding",
                "coaching_resolution=continue",
                f"coaching_state_in={current_state}",
                f"coaching_state_out={session.state}",
            )
            return StageReply(session=session, run_coaching=True)

        case "complete":
            session.state = CoachingState.COMPLETED.value
            session.cancelled = False
            _set_debug_message(
                session,
                debug_message,
                f"coaching_raw_outcome={raw_outcome or 'missing'}",
                f"coaching_normalized_outcome={outcome}",
                "coaching_transition=guiding_to_completed",
                "coaching_resolution=complete",
                f"coaching_state_in={current_state}",
                f"coaching_state_out={session.state}",
                f"next_stage={Stage.SYNTHESIS.value}",
            )
            return StageReply(session=session, next_stage=Stage.SYNTHESIS)

        case "cancel":
            session.state = CoachingState.CANCELLED.value
            session.cancelled = True
            _set_debug_message(
                session,
                debug_message,
                f"coaching_raw_outcome={raw_outcome or 'missing'}",
                f"coaching_normalized_outcome={outcome}",
                "coaching_transition=guiding_to_cancelled",
                "coaching_resolution=cancel",
                f"coaching_state_in={current_state}",
                f"coaching_state_out={session.state}",
            )
            return StageReply(session=session, run_coaching=True)

        case _:
            session.state = CoachingState.GUIDING.value
            session.cancelled = False
            session.evaluation_message = (
                "Coaching result: continue. The engine returned an unexpected "
                f"outcome label: {raw_outcome or 'missing'}."
            )
            _set_debug_message(
                session,
                debug_message,
                f"coaching_raw_outcome={raw_outcome or 'missing'}",
                f"coaching_normalized_outcome={outcome}",
                "coaching_transition=guiding_to_guiding",
                "coaching_resolution=unexpected_engine_outcome",
                f"coaching_state_in={current_state}",
                f"coaching_state_out={session.state}",
            )
            return StageReply(session=session, run_coaching=True)


def normalize_coaching_output(session: Session, result: Any) -> dict[str, str]:
    """Normalize user-facing coaching output for Coaching."""
    fallback_key = _normalize_label(
        session.stage_context.get("coaching_latest_outcome") or session.state
    )
    fallback_message = (
        DEFAULT_COACH_MESSAGE_BY_OUTCOME.get(fallback_key)
        or DEFAULT_COACH_MESSAGE_BY_OUTCOME["continue"]
    )

    if not isinstance(result, dict):
        return {
            "coach_message": fallback_message,
            "debug_message": _join_debug_lines(
                "coaching_response_status=plain_text_output",
                f"coaching_response_engine_output={result}",
                "coaching_response_fallback=default",
            ),
        }

    coach_message = str(result.get("coach_message") or "").strip()
    fallback_used = False
    if not coach_message or coach_message.startswith("TODO:"):
        coach_message = fallback_message
        fallback_used = True

    return {
        "coach_message": coach_message,
        "debug_message": _join_debug_lines(
            str(result.get("debug_message") or "coaching_response_debug=missing"),
            "coaching_response_fallback=default" if fallback_used else "",
        ),
    }


def handle_waiting(session: Session) -> StageReply:
    """Coaching has no waiting states in V3.1; fail safely if reached."""
    session.state = CoachingState.CANCELLED.value
    session.cancelled = True
    session.evaluation_message = (
        "Coaching result: invalid waiting state. The stage received an "
        "unexpected waiting-state value."
    )
    session.coach_message = (
        "I can't continue because the coaching stage entered an unexpected state."
    )
    _set_debug_message(
        session,
        "coaching_waiting_error=unexpected_state",
        f"coaching_state_out={session.state}",
    )
    return StageReply(session=session)


def handle_terminal(session: Session) -> StageReply:
    """Handle deterministic terminal-state behaviour for Coaching."""
    current_state = session.state

    if current_state == CoachingState.COMPLETED.value:
        session.cancelled = False
        _set_debug_message(
            session,
            "coaching_stage_status=already_completed",
            f"coaching_state_in={current_state}",
            f"next_stage={Stage.SYNTHESIS.value}",
        )
        return StageReply(session=session, next_stage=Stage.SYNTHESIS)

    if current_state == CoachingState.CANCELLED.value:
        session.cancelled = True
        session.evaluation_message = (
            "Coaching result: already cancelled. The coaching stage will not "
            "be re-opened."
        )
        session.coach_message = DEFAULT_COACH_MESSAGE_BY_OUTCOME["cancelled"]
        _set_debug_message(
            session,
            "coaching_stage_status=already_cancelled",
            f"coaching_state_in={current_state}",
            f"coaching_state_out={session.state}",
        )
        return StageReply(session=session)

    session.state = CoachingState.CANCELLED.value
    session.cancelled = True
    session.evaluation_message = (
        "Coaching result: invalid internal state. The stage received an "
        "unexpected coaching state."
    )
    session.coach_message = (
        "I can't continue because the coaching stage entered an unexpected state."
    )
    _set_debug_message(
        session,
        "coaching_stage_error=unexpected_state",
        f"coaching_state_in={current_state}",
        f"coaching_state_out={session.state}",
    )
    return StageReply(session=session)
