"""
Synthesis stage module for Coach V3.

Synthesis follows the V3.1 production/waiting/terminal model:
- preparing: production
- validating: waiting
- refining: production
- completed: terminal
- cancelled: terminal
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.enums import ChatRole, Stage, StateType, SynthesisState
from backend.models import Session, StageReply


STAGE_YAML_PATH = Path(__file__).resolve().parents[1] / "config" / "synthesis.yaml"

COACHING_OUTPUT_INSTRUCTION = """
Return JSON only with exactly these keys:
- coach_message: concise user-facing synthesis text
- debug_message: concise trace/debug detail
"""

STATE_TYPE_BY_NAME = {
    SynthesisState.PREPARING.value: StateType.PRODUCTION.value,
    SynthesisState.VALIDATING.value: StateType.WAITING.value,
    SynthesisState.REFINING.value: StateType.PRODUCTION.value,
    SynthesisState.COMPLETED.value: StateType.TERMINAL.value,
    SynthesisState.CANCELLED.value: StateType.TERMINAL.value,
}


def _join_debug_lines(*lines: str) -> str:
    """Build a readable debug trace without dropping earlier details."""
    return "\n".join(line for line in lines if line)


def _set_debug_message(session: Session, *lines: str) -> None:
    """Append stage-local debug lines without dropping earlier trace detail."""
    session.debug_message = _join_debug_lines(str(session.debug_message or ""), *lines)


def _normalized_text(value: str | None) -> str:
    """Normalize a user control string for deterministic checks."""
    return " ".join(str(value or "").strip().lower().split())


def _latest_user_context(session: Session) -> str:
    """Return a simple user-context summary from visible user turns."""
    user_messages = [
        item.message.strip()
        for item in session.chat_history
        if item.role == ChatRole.USER and item.message.strip()
    ]
    if not user_messages:
        return "the work-related challenge the user has been describing"
    if len(user_messages) == 1:
        return user_messages[-1]
    return f"{user_messages[0]} {user_messages[-1]}"


def _default_synthesis_message(session: Session) -> str:
    """Provide a safe offline synthesis when no LLM text is available."""
    context = _latest_user_context(session)
    return (
        "Here is the synthesis of the challenge as I currently understand it: "
        f"{context} The core issue appears to involve competing pressures, "
        "constraints, or expectations at work, and the real task is to define "
        "the problem clearly before choosing how to act."
    )


def get_state_type(state_name: str) -> str:
    """Return the V3.1 execution type for a Synthesis state."""
    return STATE_TYPE_BY_NAME.get(state_name, StateType.TERMINAL.value)


def apply_evaluation(session: Session, result: Any) -> StageReply:
    """Synthesis does not use evaluation in the V3.1 baseline flow."""
    session.state = SynthesisState.CANCELLED.value
    session.cancelled = True
    session.evaluation_message = (
        "Synthesis result: unexpected evaluation call. This stage should not "
        "invoke evaluation in the baseline V3.1 flow."
    )
    session.coach_message = (
        "I can't continue because the synthesis stage entered an unexpected path."
    )
    _set_debug_message(
        session,
        "synthesis_evaluation_error=unexpected_call",
        f"synthesis_engine_output={result}",
        f"synthesis_state_out={session.state}",
    )
    return StageReply(session=session)


def normalize_coaching_output(session: Session, result: Any) -> dict[str, str]:
    """Synthesis uses apply_production(...) directly for coaching output."""
    return {
        "coach_message": _default_synthesis_message(session),
        "debug_message": "synthesis_coaching_normalize_unused=true",
    }


def apply_production(session: Session, result: Any) -> StageReply:
    """Apply deterministic production behaviour for preparing/refining."""
    current_state = session.state
    default_message = _default_synthesis_message(session)

    if not isinstance(result, dict):
        coach_message = default_message
        debug_message = _join_debug_lines(
            "synthesis_coaching_error=plain_text_output",
            f"synthesis_coaching_engine_output={result}",
            "synthesis_coaching_fallback=default",
        )
    else:
        coach_message = str(result.get("coach_message") or "").strip()
        fallback_used = False
        if not coach_message or coach_message.startswith("TODO:"):
            coach_message = default_message
            fallback_used = True
        debug_message = _join_debug_lines(
            str(result.get("debug_message") or "synthesis_coaching_debug=missing"),
            "synthesis_coaching_fallback=default" if fallback_used else "",
        )

    session.coach_message = coach_message
    session.cancelled = False

    if current_state == SynthesisState.PREPARING.value:
        session.state = SynthesisState.VALIDATING.value
        _set_debug_message(
            session,
            debug_message,
            "synthesis_transition=preparing_to_validating",
            "synthesis_resolution=presented_for_validation",
            f"synthesis_state_in={current_state}",
            f"synthesis_state_out={session.state}",
        )
        return StageReply(session=session)

    if current_state == SynthesisState.REFINING.value:
        session.state = SynthesisState.COMPLETED.value
        _set_debug_message(
            session,
            debug_message,
            "synthesis_transition=refining_to_completed",
            "synthesis_resolution=refined_and_finalized",
            f"synthesis_state_in={current_state}",
            f"synthesis_state_out={session.state}",
            f"next_stage={Stage.PATHWAYS.value}",
        )
        return StageReply(session=session, next_stage=Stage.PATHWAYS)

    session.state = SynthesisState.CANCELLED.value
    session.cancelled = True
    session.evaluation_message = (
        "Synthesis result: invalid production state. The stage received an "
        "unexpected production-state value."
    )
    session.coach_message = (
        "I can't continue because the synthesis stage entered an unexpected state."
    )
    _set_debug_message(
        session,
        debug_message,
        "synthesis_production_error=unexpected_state",
        f"synthesis_state_in={current_state}",
        f"synthesis_state_out={session.state}",
    )
    return StageReply(session=session)


def handle_waiting(session: Session) -> StageReply:
    """Consume deterministic validation input for Synthesis."""
    current_state = session.state
    user_text = _normalized_text(session.user_message)

    if current_state != SynthesisState.VALIDATING.value:
        session.state = SynthesisState.CANCELLED.value
        session.cancelled = True
        session.evaluation_message = (
            "Synthesis result: invalid waiting state. The stage received an "
            "unexpected waiting-state value."
        )
        session.coach_message = (
            "I can't continue because the synthesis stage entered an unexpected state."
        )
        _set_debug_message(
            session,
            "synthesis_waiting_error=unexpected_state",
            f"synthesis_state_in={current_state}",
            f"synthesis_state_out={session.state}",
        )
        return StageReply(session=session)

    accept_values = {
        "yes",
        "y",
        "ok",
        "okay",
        "accurate",
        "correct",
        "confirm",
        "confirmed",
        "thats it",
        "that's it",
        "that is it",
        "looks right",
    }
    cancel_values = {
        "cancel",
        "abort",
        "stop",
        "end",
        "quit",
    }

    if user_text in accept_values:
        session.state = SynthesisState.COMPLETED.value
        session.cancelled = False
        _set_debug_message(
            session,
            "synthesis_transition=validating_to_completed",
            "synthesis_resolution=accepted",
            f"synthesis_state_in={current_state}",
            f"synthesis_state_out={session.state}",
            f"next_stage={Stage.PATHWAYS.value}",
        )
        return StageReply(session=session, next_stage=Stage.PATHWAYS)

    if user_text in cancel_values:
        session.state = SynthesisState.CANCELLED.value
        session.cancelled = True
        session.evaluation_message = (
            "Synthesis result: cancelled during validation. The user asked to "
            "stop instead of finalising the synthesis."
        )
        session.coach_message = (
            "I'll stop here rather than continue the synthesis or pathways flow."
        )
        _set_debug_message(
            session,
            "synthesis_transition=validating_to_cancelled",
            "synthesis_resolution=user_cancelled",
            f"synthesis_state_in={current_state}",
            f"synthesis_state_out={session.state}",
        )
        return StageReply(session=session)

    session.state = SynthesisState.REFINING.value
    session.cancelled = False
    _set_debug_message(
        session,
        "synthesis_transition=validating_to_refining",
        "synthesis_resolution=user_comment_requires_refinement",
        f"synthesis_state_in={current_state}",
        f"synthesis_state_out={session.state}",
    )
    return StageReply(session=session, continue_turn=True)


def handle_terminal(session: Session) -> StageReply:
    """Handle deterministic terminal-state behaviour for Synthesis."""
    current_state = session.state

    if current_state == SynthesisState.COMPLETED.value:
        session.cancelled = False
        _set_debug_message(
            session,
            "synthesis_stage_status=already_completed",
            f"synthesis_state_in={current_state}",
            f"next_stage={Stage.PATHWAYS.value}",
        )
        return StageReply(session=session, next_stage=Stage.PATHWAYS)

    if current_state == SynthesisState.CANCELLED.value:
        session.cancelled = True
        session.evaluation_message = (
            "Synthesis result: already cancelled. The synthesis stage will "
            "not be re-opened."
        )
        session.coach_message = (
            "This synthesis step has already been stopped, so I won't reopen it."
        )
        _set_debug_message(
            session,
            "synthesis_stage_status=already_cancelled",
            f"synthesis_state_in={current_state}",
            f"synthesis_state_out={session.state}",
        )
        return StageReply(session=session)

    session.state = SynthesisState.CANCELLED.value
    session.cancelled = True
    session.evaluation_message = (
        "Synthesis result: invalid internal state. The stage received an "
        "unexpected synthesis state."
    )
    session.coach_message = (
        "I can't continue because the synthesis stage entered an unexpected state."
    )
    _set_debug_message(
        session,
        "synthesis_stage_error=unexpected_state",
        f"synthesis_state_in={current_state}",
        f"synthesis_state_out={session.state}",
    )
    return StageReply(session=session)
