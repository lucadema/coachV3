"""
Macro-stage controller for Coach V3.

Controller owns:
- end-to-end cognitive process orchestration
- session loading and persistence
- dispatch to the active stage module
- macro-stage transitions

Controller does not own local stage FSM logic.

Design rule for this POC:
- internal in-process calls use plain parameters and return values where
  possible
- the controller returns the canonical Session object directly
"""

from __future__ import annotations

import uuid

from backend.enums import (
    ChatRole,
    ClassificationState,
    ClosureState,
    CoachingState,
    PathwaysState,
    Stage,
    SynthesisState,
)
from backend.models import ChatMessage, Session, StageReply
from backend.state_store import state_store
from backend.stages import classification, closure, coaching, pathways, synthesis


# ============================================================================
# Session lifecycle helpers
# ============================================================================

INITIAL_STATE_BY_STAGE = {
    Stage.CLASSIFICATION: ClassificationState.EVALUATING.value,
    Stage.COACHING: CoachingState.GUIDING.value,
    Stage.SYNTHESIS: SynthesisState.PREPARING.value,
    Stage.PATHWAYS: PathwaysState.PREPARING.value,
    Stage.CLOSURE: ClosureState.PREPARING.value,
}


def _initial_state_for_stage(stage: Stage) -> str:
    """Return the required initial local state for a macro-stage."""
    return INITIAL_STATE_BY_STAGE[stage]


def _require_session(session_id: str) -> Session:
    """Load an existing session or raise a clear error."""
    session = state_store.get_session(session_id)

    if session is None:
        raise ValueError(f"Session not found: {session_id}")

    return session


# ============================================================================
# Stage dispatch and macro-stage handling
# ============================================================================

def _dispatch_stage(session: Session) -> StageReply:
    """
    Dispatch the in-memory session to the active stage module.

    Note:
    Stage modules should expose:
        handle_stage(session: Session) -> StageReply
    """
    match session.stage:
        case "classification":
            return classification.handle_stage(session)

        case "coaching":
            return coaching.handle_stage(session)

        case "synthesis":
            return synthesis.handle_stage(session)

        case "pathways":
            return pathways.handle_stage(session)

        case "closure":
            return closure.handle_stage(session)

        case _:
            session.debug_message = f"Unknown stage: {session.stage}"
            session.cancelled = True
            return StageReply(session=session)


def _apply_macro_stage_transition(stage_reply: StageReply) -> Session:
    """
    Apply any requested macro-stage transition and return the updated session.
    """
    session = stage_reply.session

    if stage_reply.next_stage is not None:
        previous_stage = session.stage
        session.stage = stage_reply.next_stage.value
        session.state = _initial_state_for_stage(stage_reply.next_stage)
        session.stage_context = {}

        transition_debug_message = (
            "Macro transition applied: "
            f"{previous_stage} -> {session.stage}; "
            f"local_state -> {session.state}."
        )
        if session.debug_message:
            session.debug_message = (
                f"{session.debug_message}\n{transition_debug_message}"
            )
        else:
            session.debug_message = transition_debug_message

    return session


# ============================================================================
# Public controller entrypoints
# ============================================================================

def init_session(session_id: str | None = None) -> Session:
    """
    Initialize, persist, and return a new session.

    No dedicated reply wrapper is used because only the canonical Session
    object needs to be returned.
    """
    session = Session(
        session_id=session_id or str(uuid.uuid4()),
        stage=Stage.CLASSIFICATION.value,
        state=_initial_state_for_stage(Stage.CLASSIFICATION),
        debug_message="Session initialized.",
    )
    state_store.save_session(session)
    return session


def handle_user_msg(session_id: str, user_message: str) -> Session:
    """
    Load session, apply the user turn, dispatch the active stage, persist, and
    return the updated session.
    """
    session = _require_session(session_id)

    session.evaluation_message = None
    session.coach_message = None
    session.debug_message = None

    session.user_message = user_message
    session.chat_history.append(
        ChatMessage(role=ChatRole.USER, message=user_message)
    )

    stage_reply = _dispatch_stage(session)
    session = _apply_macro_stage_transition(stage_reply)

    if session.coach_message:
        session.chat_history.append(
            ChatMessage(role=ChatRole.ASSISTANT, message=session.coach_message)
        )

    state_store.save_session(session)

    return session


def get_debug(session_id: str) -> Session:
    """
    Return the current session so the API layer can expose debug information
    without duplicating session fields in a separate internal reply model.
    """
    return _require_session(session_id)
