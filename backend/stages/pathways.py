"""
Pathways stage module for Coach V3.

Pathways follows the V3.1 production/waiting/terminal model:
- preparing: production
- presenting: waiting
- completed: terminal
- cancelled: terminal
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.enums import ChatRole, PathwaysState, Stage, StateType
from backend.models import Session, StageReply


STAGE_YAML_PATH = Path(__file__).resolve().parents[1] / "config" / "pathways.yaml"

COACHING_OUTPUT_INSTRUCTION = """
Return JSON only with exactly these keys:
- coach_message: user-facing pathways text
- debug_message: concise trace/debug detail

For coach_message:
- return 3 or 4 distinct pathways
- use this exact structure for each pathway:
  ## <SHORT TITLE>
  Orientation: <one or two concise sentences>
  Conditions: <two to four concise sentences>
- separate pathways with a blank line
- do not add an introductory paragraph or closing paragraph
"""

STATE_TYPE_BY_NAME = {
    PathwaysState.PREPARING.value: StateType.PRODUCTION.value,
    PathwaysState.PRESENTING.value: StateType.WAITING.value,
    PathwaysState.COMPLETED.value: StateType.TERMINAL.value,
    PathwaysState.CANCELLED.value: StateType.TERMINAL.value,
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


def _latest_synthesis_text(session: Session) -> str:
    """Read the latest relevant assistant synthesis text from session history."""
    assistant_messages = [
        item.message.strip()
        for item in session.chat_history
        if item.role == ChatRole.ASSISTANT and item.message.strip()
    ]
    if assistant_messages:
        return assistant_messages[-1]
    return "the validated synthesis of the user's work-related challenge"


def _default_pathways_message(session: Session) -> str:
    """Provide a safe offline pathways message when no LLM text is available."""
    synthesis_text = _latest_synthesis_text(session)
    return "\n\n".join(
        [
            (
                "## BUILD THE EVIDENCE FIRST\n"
                "Orientation: Build confidence by gathering sharper proof, local insight, "
                "or concrete examples before pushing for a bigger move.\n"
                "Conditions: This works best when the problem is blocked by uncertainty, "
                "weak stakeholder confidence, or missing evidence. Use the current "
                f"synthesis as the anchor for what evidence would matter most: {synthesis_text}"
            ),
            (
                "## REFRAME THE BUSINESS CASE\n"
                "Orientation: Reposition the issue in terms that matter more clearly to "
                "decision-makers, priorities, or organisational outcomes.\n"
                "Conditions: This is useful when the current framing is not landing, even "
                "if the underlying issue is real. Focus on translating the synthesis into "
                "timing, risk, cost, or strategic language that others can act on."
            ),
            (
                "## CREATE A LOW-BARRIER NEXT STEP\n"
                "Orientation: Design one smaller move that creates momentum without "
                "requiring full agreement or a high-stakes commitment upfront.\n"
                "Conditions: This is strongest when the issue feels politically sensitive, "
                "complex, or hard to solve in one step. Turn the synthesis into a limited, "
                "testable action that reduces exposure while still moving the situation forward."
            ),
        ]
    )


def get_state_type(state_name: str) -> str:
    """Return the V3.1 execution type for a Pathways state."""
    return STATE_TYPE_BY_NAME.get(state_name, StateType.TERMINAL.value)


def apply_evaluation(session: Session, result: Any) -> StageReply:
    """Pathways does not use evaluation in the V3.1 baseline flow."""
    session.state = PathwaysState.CANCELLED.value
    session.cancelled = True
    session.evaluation_message = (
        "Pathways result: unexpected evaluation call. This stage should not "
        "invoke evaluation in the baseline V3.1 flow."
    )
    session.coach_message = (
        "I can't continue because the pathways stage entered an unexpected path."
    )
    _set_debug_message(
        session,
        "pathways_evaluation_error=unexpected_call",
        f"pathways_engine_output={result}",
        f"pathways_state_out={session.state}",
    )
    return StageReply(session=session)


def normalize_coaching_output(session: Session, result: Any) -> dict[str, str]:
    """Pathways uses apply_production(...) directly for coaching output."""
    return {
        "coach_message": _default_pathways_message(session),
        "debug_message": "pathways_coaching_normalize_unused=true",
    }


def apply_production(session: Session, result: Any) -> StageReply:
    """Apply deterministic production behaviour for Pathways preparing."""
    current_state = session.state
    default_message = _default_pathways_message(session)

    if not isinstance(result, dict):
        coach_message = default_message
        debug_message = _join_debug_lines(
            "pathways_coaching_error=plain_text_output",
            f"pathways_coaching_engine_output={result}",
            "pathways_coaching_fallback=default",
        )
    else:
        coach_message = str(result.get("coach_message") or "").strip()
        fallback_used = False
        if not coach_message or coach_message.startswith("TODO:"):
            coach_message = default_message
            fallback_used = True
        debug_message = _join_debug_lines(
            str(result.get("debug_message") or "pathways_coaching_debug=missing"),
            "pathways_coaching_fallback=default" if fallback_used else "",
        )

    if current_state != PathwaysState.PREPARING.value:
        session.state = PathwaysState.CANCELLED.value
        session.cancelled = True
        session.evaluation_message = (
            "Pathways result: invalid production state. The stage received an "
            "unexpected production-state value."
        )
        session.coach_message = (
            "I can't continue because the pathways stage entered an unexpected state."
        )
        _set_debug_message(
            session,
            debug_message,
            "pathways_production_error=unexpected_state",
            f"pathways_state_in={current_state}",
            f"pathways_state_out={session.state}",
        )
        return StageReply(session=session)

    session.coach_message = coach_message
    session.cancelled = False
    session.state = PathwaysState.PRESENTING.value
    _set_debug_message(
        session,
        debug_message,
        "pathways_transition=preparing_to_presenting",
        "pathways_resolution=presented",
        f"pathways_state_in={current_state}",
        f"pathways_state_out={session.state}",
    )
    return StageReply(session=session)


def handle_waiting(session: Session) -> StageReply:
    """Consume deterministic feedback for Pathways presenting."""
    current_state = session.state
    user_text = _normalized_text(session.user_message)

    if current_state != PathwaysState.PRESENTING.value:
        session.state = PathwaysState.CANCELLED.value
        session.cancelled = True
        session.evaluation_message = (
            "Pathways result: invalid waiting state. The stage received an "
            "unexpected waiting-state value."
        )
        session.coach_message = (
            "I can't continue because the pathways stage entered an unexpected state."
        )
        _set_debug_message(
            session,
            "pathways_waiting_error=unexpected_state",
            f"pathways_state_in={current_state}",
            f"pathways_state_out={session.state}",
        )
        return StageReply(session=session)

    cancel_values = {"cancel", "abort", "stop", "end", "quit"}
    positive_prefixes = (
        "selection:",
        "select:",
        "pathway:",
        "pathway_selected:",
    )
    positive_values = {
        "continue",
        "next",
        "yes",
        "ok",
        "okay",
        "ack",
        "acknowledged",
    }

    if user_text in cancel_values:
        session.state = PathwaysState.CANCELLED.value
        session.cancelled = True
        session.evaluation_message = (
            "Pathways result: cancelled during presentation. The user asked "
            "to stop instead of continuing to closure."
        )
        session.coach_message = (
            "I'll stop here rather than continue into the closing step."
        )
        _set_debug_message(
            session,
            "pathways_transition=presenting_to_cancelled",
            "pathways_resolution=user_cancelled",
            f"pathways_state_in={current_state}",
            f"pathways_state_out={session.state}",
        )
        return StageReply(session=session)

    if user_text in positive_values or user_text.startswith(positive_prefixes):
        session.state = PathwaysState.COMPLETED.value
        session.cancelled = False
        _set_debug_message(
            session,
            "pathways_transition=presenting_to_completed",
            "pathways_resolution=selection_or_acknowledgement_received",
            f"pathways_state_in={current_state}",
            f"pathways_state_out={session.state}",
            f"next_stage={Stage.CLOSURE.value}",
        )
        return StageReply(session=session, next_stage=Stage.CLOSURE)

    session.state = PathwaysState.COMPLETED.value
    session.cancelled = False
    _set_debug_message(
        session,
        "pathways_transition=presenting_to_completed",
        "pathways_resolution=free_text_acknowledgement_assumed",
        f"pathways_state_in={current_state}",
        f"pathways_state_out={session.state}",
        f"next_stage={Stage.CLOSURE.value}",
    )
    return StageReply(session=session, next_stage=Stage.CLOSURE)


def handle_terminal(session: Session) -> StageReply:
    """Handle deterministic terminal-state behaviour for Pathways."""
    current_state = session.state

    if current_state == PathwaysState.COMPLETED.value:
        session.cancelled = False
        _set_debug_message(
            session,
            "pathways_stage_status=already_completed",
            f"pathways_state_in={current_state}",
            f"next_stage={Stage.CLOSURE.value}",
        )
        return StageReply(session=session, next_stage=Stage.CLOSURE)

    if current_state == PathwaysState.CANCELLED.value:
        session.cancelled = True
        session.evaluation_message = (
            "Pathways result: already cancelled. The pathways stage will not "
            "be re-opened."
        )
        session.coach_message = (
            "This pathways step has already been stopped, so I won't reopen it."
        )
        _set_debug_message(
            session,
            "pathways_stage_status=already_cancelled",
            f"pathways_state_in={current_state}",
            f"pathways_state_out={session.state}",
        )
        return StageReply(session=session)

    session.state = PathwaysState.CANCELLED.value
    session.cancelled = True
    session.evaluation_message = (
        "Pathways result: invalid internal state. The stage received an "
        "unexpected pathways state."
    )
    session.coach_message = (
        "I can't continue because the pathways stage entered an unexpected state."
    )
    _set_debug_message(
        session,
        "pathways_stage_error=unexpected_state",
        f"pathways_state_in={current_state}",
        f"pathways_state_out={session.state}",
    )
    return StageReply(session=session)
