"""
Closure stage module for Coach V3.

Closure follows the V3.1 production/terminal model:
- preparing: production
- completed: terminal
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.enums import ClosureState, StateType
from backend.models import Session, StageReply


STAGE_YAML_PATH = Path(__file__).resolve().parents[1] / "config" / "closure.yaml"

COACHING_OUTPUT_INSTRUCTION = """
Return JSON only with exactly these keys:
- coach_message: concise user-facing closing text
- debug_message: concise trace/debug detail
"""

STATE_TYPE_BY_NAME = {
    ClosureState.PREPARING.value: StateType.PRODUCTION.value,
    ClosureState.COMPLETED.value: StateType.TERMINAL.value,
}


def _join_debug_lines(*lines: str) -> str:
    """Build a readable debug trace without dropping earlier details."""
    return "\n".join(line for line in lines if line)


def _set_debug_message(session: Session, *lines: str) -> None:
    """Append stage-local debug lines without dropping earlier trace detail."""
    session.debug_message = _join_debug_lines(str(session.debug_message or ""), *lines)


def _default_closure_message(session: Session) -> str:
    """Provide a safe offline closing message when no LLM text is available."""
    return (
        "This session is now complete. Thank you for working through the "
        "problem with care and clarity."
    )


def get_state_type(state_name: str) -> str:
    """Return the V3.1 execution type for a Closure state."""
    return STATE_TYPE_BY_NAME.get(state_name, StateType.TERMINAL.value)


def apply_evaluation(session: Session, result: Any) -> StageReply:
    """Closure does not use evaluation in the V3.1 baseline flow."""
    session.state = ClosureState.COMPLETED.value
    session.completed = True
    session.cancelled = False
    session.evaluation_message = (
        "Closure result: unexpected evaluation call. This stage should not "
        "invoke evaluation in the baseline V3.1 flow."
    )
    session.coach_message = _default_closure_message(session)
    _set_debug_message(
        session,
        "closure_evaluation_error=unexpected_call",
        f"closure_engine_output={result}",
        f"closure_state_out={session.state}",
    )
    return StageReply(session=session)


def normalize_coaching_output(session: Session, result: Any) -> dict[str, str]:
    """Closure uses apply_production(...) directly for coaching output."""
    return {
        "coach_message": _default_closure_message(session),
        "debug_message": "closure_coaching_normalize_unused=true",
    }


def apply_production(session: Session, result: Any) -> StageReply:
    """Apply deterministic production behaviour for Closure preparing."""
    current_state = session.state
    default_message = _default_closure_message(session)

    if not isinstance(result, dict):
        coach_message = default_message
        debug_message = _join_debug_lines(
            "closure_coaching_error=plain_text_output",
            f"closure_coaching_engine_output={result}",
            "closure_coaching_fallback=default",
        )
    else:
        coach_message = str(result.get("coach_message") or "").strip()
        fallback_used = False
        if not coach_message or coach_message.startswith("TODO:"):
            coach_message = default_message
            fallback_used = True
        debug_message = _join_debug_lines(
            str(result.get("debug_message") or "closure_coaching_debug=missing"),
            "closure_coaching_fallback=default" if fallback_used else "",
        )

    if current_state != ClosureState.PREPARING.value:
        session.state = ClosureState.COMPLETED.value
        session.completed = True
        session.cancelled = False
        session.evaluation_message = (
            "Closure result: invalid production state. The stage received an "
            "unexpected production-state value."
        )
        session.coach_message = default_message
        _set_debug_message(
            session,
            debug_message,
            "closure_production_error=unexpected_state",
            f"closure_state_in={current_state}",
            f"closure_state_out={session.state}",
        )
        return StageReply(session=session)

    session.coach_message = coach_message
    session.state = ClosureState.COMPLETED.value
    session.completed = True
    session.cancelled = False
    _set_debug_message(
        session,
        debug_message,
        "closure_transition=preparing_to_completed",
        "closure_resolution=completed",
        f"closure_state_in={current_state}",
        f"closure_state_out={session.state}",
        "session_completed=true",
    )
    return StageReply(session=session)


def handle_waiting(session: Session) -> StageReply:
    """Closure has no waiting states in V3.1; fail safely if reached."""
    session.state = ClosureState.COMPLETED.value
    session.completed = True
    session.cancelled = False
    session.evaluation_message = (
        "Closure result: invalid waiting state. The stage received an "
        "unexpected waiting-state value."
    )
    session.coach_message = _default_closure_message(session)
    _set_debug_message(
        session,
        "closure_waiting_error=unexpected_state",
        f"closure_state_out={session.state}",
    )
    return StageReply(session=session)


def handle_terminal(session: Session) -> StageReply:
    """Handle deterministic terminal-state behaviour for Closure."""
    current_state = session.state

    if current_state == ClosureState.COMPLETED.value:
        session.completed = True
        session.cancelled = False
        session.evaluation_message = (
            "Closure result: already completed. The session is already closed."
        )
        session.coach_message = _default_closure_message(session)
        _set_debug_message(
            session,
            "closure_stage_status=already_completed",
            f"closure_state_in={current_state}",
        )
        return StageReply(session=session)

    session.state = ClosureState.COMPLETED.value
    session.completed = True
    session.cancelled = False
    session.evaluation_message = (
        "Closure result: invalid internal state. The stage received an "
        "unexpected closure state."
    )
    session.coach_message = _default_closure_message(session)
    _set_debug_message(
        session,
        "closure_stage_error=unexpected_state",
        f"closure_state_in={current_state}",
        f"closure_state_out={session.state}",
    )
    return StageReply(session=session)
