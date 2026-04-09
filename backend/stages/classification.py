"""
Classification stage module for Coach V3.

This stage owns only its local FSM and stage-specific interpretation rules.
The controller owns the execution loop and engine calls.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from backend.enums import ClassificationState, Stage, StateType
from backend.models import Session, StageReply


STAGE_YAML_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "classification.yaml"
)

EVALUATION_OUTPUT_INSTRUCTION = """
Return JSON only with exactly these keys:
- classification_label: one of VALID, AMBIGUOUS, OUT_OF_SCOPE, DISTRESS
- evaluation_message: concise internal evaluation summary
- debug_message: concise trace/debug detail
"""

COACHING_OUTPUT_INSTRUCTION = """
Return JSON only with exactly these keys:
- coach_message: concise user-facing classification response
- debug_message: concise trace/debug detail
"""

STATE_TYPE_BY_NAME = {
    ClassificationState.EVALUATING.value: StateType.EVALUATIVE.value,
    ClassificationState.AMBIGUOUS.value: StateType.WAITING.value,
    ClassificationState.COMPLETED.value: StateType.TERMINAL.value,
    ClassificationState.CANCELLED.value: StateType.TERMINAL.value,
}

OUTCOME_BY_CLASSIFICATION_LABEL = {
    "valid": "valid",
    "ambiguous": "ambiguous",
    "invalid": "invalid",
    "out_of_scope": "invalid",
    "distress": "invalid",
}

DEFAULT_COACH_MESSAGE_BY_LABEL = {
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
    "cancelled": (
        "This session has already been stopped at classification. Please "
        "start a new session with the specific decision, challenge, or "
        "conflict you want to work on."
    ),
}


def _join_debug_lines(*lines: str) -> str:
    """Build a readable debug trace without dropping earlier details."""
    return "\n".join(line for line in lines if line)


def _set_debug_message(session: Session, *lines: str) -> None:
    """Append stage-local debug lines without dropping earlier trace detail."""
    session.debug_message = _join_debug_lines(str(session.debug_message or ""), *lines)


def _normalize_label(value: Any) -> str:
    """Normalize model labels without treating YAML as the FSM owner."""
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _offline_classification_fallback_output(user_message: str | None) -> dict[str, str]:
    """Deterministic offline fallback owned by the Classification stage."""
    normalized = " ".join((user_message or "").strip().lower().split())
    tokens = re.findall(r"[a-z']+", normalized)

    coaching_keywords = [
        "work",
        "career",
        "manager",
        "team",
        "relationship",
        "conflict",
        "stress",
        "overwhelmed",
        "burnout",
        "decision",
        "decide",
        "goal",
        "priorities",
        "communication",
        "boundaries",
    ]
    ambiguous_keywords = [
        "help",
        "advice",
        "stuck",
        "unsure",
        "not sure",
        "something",
        "issue",
        "problem",
    ]
    invalid_keywords = [
        "weather",
        "joke",
        "recipe",
        "sports score",
        "stock price",
        "movie review",
        "trivia",
    ]

    matched_invalid_keyword = next(
        (keyword for keyword in invalid_keywords if keyword in normalized),
        None,
    )
    matched_ambiguous_keyword = next(
        (keyword for keyword in ambiguous_keywords if keyword in normalized),
        None,
    )
    matched_coaching_keyword = next(
        (keyword for keyword in coaching_keywords if keyword in normalized),
        None,
    )

    if matched_invalid_keyword:
        label = "invalid"
        reason = f"matched invalid topic keyword '{matched_invalid_keyword}'"
    elif len(tokens) < 6:
        label = "ambiguous"
        reason = (
            f"message only contains {len(tokens)} word(s), which is below "
            "the valid threshold of 6"
        )
    elif matched_coaching_keyword:
        label = "valid"
        reason = (
            f"matched coaching keyword '{matched_coaching_keyword}' "
            "with enough detail"
        )
    elif matched_ambiguous_keyword and len(tokens) < 9:
        label = "ambiguous"
        reason = (
            f"matched ambiguity keyword '{matched_ambiguous_keyword}' "
            "and still lacks context"
        )
    else:
        label = "ambiguous"
        reason = "message does not yet clearly describe a coaching issue"

    messages = {
        "valid": (
            "Classification result: valid. The opening message contains "
            "a coaching-suitable issue with enough context to proceed."
        ),
        "ambiguous": (
            "Classification result: ambiguous. The opening message may "
            "be coaching-relevant, but it still needs clarification."
        ),
        "invalid": (
            "Classification result: invalid. The opening message does "
            "not fit the coaching intake flow."
        ),
    }

    return {
        "classification_label": label,
        "evaluation_message": f"{messages[label]} Reason: {reason}.",
        "debug_message": "\n".join(
            [
                "classification_stage_fallback=offline_v1",
                "classification_parse_status=offline_fallback",
                f"classification_outcome={label}",
                f"classification_reason={reason}",
                f"matched_invalid_keyword={matched_invalid_keyword or 'none'}",
                f"matched_ambiguous_keyword={matched_ambiguous_keyword or 'none'}",
                f"matched_coaching_keyword={matched_coaching_keyword or 'none'}",
            ]
        ),
    }


def _should_use_offline_fallback(result: Any) -> bool:
    """Use the stage-local fallback only for generic no-LLM engine output."""
    if not isinstance(result, dict):
        return False

    if result.get("outcome") or result.get("classification_label"):
        return False

    evaluation_message = str(result.get("evaluation_message") or "").strip()
    debug_message = str(result.get("debug_message") or "")
    return (
        evaluation_message.startswith("TODO:")
        or "structured_parse_status=no_llm_output" in debug_message
    )


def get_state_type(state_name: str) -> str:
    """Return the V3.1 execution type for a Classification state."""
    return STATE_TYPE_BY_NAME.get(state_name, StateType.TERMINAL.value)


def apply_evaluation(session: Session, result: Any) -> StageReply:
    """Interpret the engine evaluation result and apply local FSM changes."""
    current_state = session.state
    from_ambiguous = bool(session.stage_context.pop("classification_from_ambiguous", False))

    if _should_use_offline_fallback(result):
        fallback_result = _offline_classification_fallback_output(session.user_message)
        result = {
            **fallback_result,
            "debug_message": _join_debug_lines(
                str(result.get("debug_message") or ""),
                "classification_fallback_source=stage_module",
                fallback_result.get("debug_message", ""),
            ),
        }

    if not isinstance(result, dict):
        raw_outcome = "invalid"
        outcome = "invalid"
        evaluation_message = (
            "Classification result: invalid engine output. The engine returned "
            "plain text where structured evaluation output was required."
        )
        debug_message = (
            "classification_engine_error=plain_text_output "
            f"engine_output={result}"
        )
    else:
        raw_outcome = _normalize_label(
            result.get("outcome") or result.get("classification_label")
        )
        outcome = OUTCOME_BY_CLASSIFICATION_LABEL.get(raw_outcome, raw_outcome or "invalid")
        missing_fields = []
        if not (result.get("outcome") or result.get("classification_label")):
            missing_fields.append("classification_label")
        missing_fields.extend(
            field
            for field in ("evaluation_message", "debug_message")
            if not result.get(field)
        )
        evaluation_message = str(result.get("evaluation_message") or "").strip()
        if not evaluation_message or evaluation_message.startswith("TODO:"):
            evaluation_message = (
                f"Classification result: {outcome}. Engine label: "
                f"{raw_outcome or 'missing'}. The engine returned structured "
                "output without an evaluation_message."
            )
        debug_message = _join_debug_lines(
            str(result.get("debug_message") or "classification_engine_debug=missing"),
            (
                f"classification_engine_missing_fields={','.join(missing_fields)}"
                if missing_fields
                else ""
            ),
        )

    session.stage_context["classification_last_outcome"] = outcome
    session.stage_context["classification_last_raw_outcome"] = raw_outcome or "invalid"
    session.evaluation_message = evaluation_message

    if from_ambiguous and outcome in {"ambiguous", "invalid"}:
        session.state = ClassificationState.CANCELLED.value
        session.cancelled = True
        session.evaluation_message = (
            "Classification result: cancelled after clarification. The "
            "follow-up still did not resolve the intake. "
            f"Underlying decision: {evaluation_message}"
        )
        _set_debug_message(
            session,
            debug_message,
            f"classification_raw_outcome={raw_outcome or 'missing'}",
            f"classification_normalized_outcome={outcome}",
            "classification_transition=evaluating_to_cancelled",
            "bounded_ambiguity_triggered=true",
            "classification_resolution=rejected_after_clarification",
            f"classification_state_in={current_state}",
            f"classification_state_out={session.state}",
        )
        return StageReply(session=session, run_coaching=True)

    match outcome:
        case "valid":
            session.state = ClassificationState.COMPLETED.value
            session.cancelled = False
            _set_debug_message(
                session,
                debug_message,
                f"classification_raw_outcome={raw_outcome or 'missing'}",
                f"classification_normalized_outcome={outcome}",
                "classification_transition=evaluating_to_completed",
                "classification_resolution=accepted",
                f"classification_state_in={current_state}",
                f"classification_state_out={session.state}",
                f"next_stage={Stage.COACHING.value}",
            )
            return StageReply(session=session, next_stage=Stage.COACHING)

        case "ambiguous":
            session.state = ClassificationState.AMBIGUOUS.value
            session.cancelled = False
            _set_debug_message(
                session,
                debug_message,
                f"classification_raw_outcome={raw_outcome or 'missing'}",
                f"classification_normalized_outcome={outcome}",
                "classification_transition=evaluating_to_ambiguous",
                "classification_resolution=needs_clarification",
                f"classification_state_in={current_state}",
                f"classification_state_out={session.state}",
            )
            return StageReply(session=session, run_coaching=True)

        case "invalid":
            session.state = ClassificationState.CANCELLED.value
            session.cancelled = True
            _set_debug_message(
                session,
                debug_message,
                f"classification_raw_outcome={raw_outcome or 'missing'}",
                f"classification_normalized_outcome={outcome}",
                "classification_transition=evaluating_to_cancelled",
                "classification_resolution=rejected",
                f"classification_state_in={current_state}",
                f"classification_state_out={session.state}",
            )
            return StageReply(session=session, run_coaching=True)

        case _:
            session.state = ClassificationState.CANCELLED.value
            session.cancelled = True
            session.evaluation_message = (
                "Classification result: invalid internal outcome. The engine "
                f"returned an unexpected classification label: {raw_outcome or 'missing'}."
            )
            _set_debug_message(
                session,
                debug_message,
                f"classification_raw_outcome={raw_outcome or 'missing'}",
                f"classification_normalized_outcome={outcome or 'missing'}",
                "classification_transition=evaluating_to_cancelled",
                "classification_resolution=unexpected_engine_outcome",
                f"classification_state_in={current_state}",
                f"classification_state_out={session.state}",
            )
            return StageReply(session=session, run_coaching=True)


def normalize_coaching_output(session: Session, result: Any) -> dict[str, str]:
    """Normalize user-facing coaching output for Classification."""
    fallback_key = _normalize_label(
        session.stage_context.get("classification_last_raw_outcome")
        or session.stage_context.get("classification_last_outcome")
        or session.state
    )
    fallback_message = (
        DEFAULT_COACH_MESSAGE_BY_LABEL.get(fallback_key)
        or DEFAULT_COACH_MESSAGE_BY_LABEL.get("invalid")
    )

    if not isinstance(result, dict):
        return {
            "coach_message": fallback_message,
            "debug_message": _join_debug_lines(
                "classification_coaching_error=plain_text_output",
                f"classification_coaching_engine_output={result}",
                "classification_coaching_fallback=default",
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
            str(result.get("debug_message") or "classification_coaching_debug=missing"),
            "classification_coaching_fallback=default" if fallback_used else "",
        ),
    }


def handle_waiting(session: Session) -> StageReply:
    """Consume deterministic waiting-state input for Classification."""
    current_state = session.state

    if current_state == ClassificationState.AMBIGUOUS.value:
        session.state = ClassificationState.EVALUATING.value
        session.cancelled = False
        session.stage_context["classification_from_ambiguous"] = True
        _set_debug_message(
            session,
            "classification_waiting_input_consumed=true",
            "classification_transition=ambiguous_to_evaluating",
            f"classification_state_in={current_state}",
            f"classification_state_out={session.state}",
        )
        return StageReply(session=session, continue_turn=True)

    session.state = ClassificationState.CANCELLED.value
    session.cancelled = True
    session.evaluation_message = (
        "Classification result: invalid waiting state. The stage received an "
        "unexpected waiting-state value."
    )
    session.coach_message = (
        "I can't continue because the classification stage entered an "
        "unexpected state."
    )
    _set_debug_message(
        session,
        "classification_waiting_error=unexpected_state",
        f"classification_state_in={current_state}",
        f"classification_state_out={session.state}",
    )
    return StageReply(session=session)


def handle_terminal(session: Session) -> StageReply:
    """Handle deterministic terminal-state behaviour for Classification."""
    current_state = session.state

    if current_state == ClassificationState.COMPLETED.value:
        session.cancelled = False
        _set_debug_message(
            session,
            "classification_stage_status=already_completed",
            f"classification_state_in={current_state}",
            f"next_stage={Stage.COACHING.value}",
        )
        return StageReply(session=session, next_stage=Stage.COACHING)

    if current_state == ClassificationState.CANCELLED.value:
        session.cancelled = True
        session.evaluation_message = (
            "Classification result: already cancelled. The classification "
            "stage will not be re-opened."
        )
        session.coach_message = DEFAULT_COACH_MESSAGE_BY_LABEL["cancelled"]
        _set_debug_message(
            session,
            "classification_stage_status=already_cancelled",
            f"classification_state_in={current_state}",
            f"classification_state_out={session.state}",
        )
        return StageReply(session=session)

    session.state = ClassificationState.CANCELLED.value
    session.cancelled = True
    session.evaluation_message = (
        "Classification result: invalid internal state. The stage received "
        "an unexpected classification state."
    )
    session.coach_message = (
        "I can't continue because the classification stage entered an "
        "unexpected state."
    )
    _set_debug_message(
        session,
        "classification_stage_error=unexpected_state",
        f"classification_state_in={current_state}",
        f"classification_state_out={session.state}",
    )
    return StageReply(session=session)
