"""
Macro-stage controller for Coach V3.

Controller owns:
- session loading and persistence
- macro-stage routing
- state-type execution dispatch
- macro-stage transitions

Stage modules own:
- local FSM decisions
- state-type declarations
- deterministic local transitions
- stage-specific result normalization
"""

from __future__ import annotations

import uuid
from typing import Any

from backend import engine
from backend.enums import (
    ChatRole,
    ClassificationState,
    ClosureState,
    CoachingState,
    PathwaysState,
    Stage,
    StateType,
    SynthesisState,
)
from backend.models import ChatMessage, Session, StageReply
from backend.state_store import state_store
from backend.stages import classification, closure, coaching, pathways, synthesis


INITIAL_STATE_BY_STAGE = {
    Stage.CLASSIFICATION: ClassificationState.EVALUATING.value,
    Stage.COACHING: CoachingState.GUIDING.value,
    Stage.SYNTHESIS: SynthesisState.PREPARING.value,
    Stage.PATHWAYS: PathwaysState.PREPARING.value,
    Stage.CLOSURE: ClosureState.PREPARING.value,
}

MAX_INTERNAL_STEPS = 12


def _initial_state_for_stage(stage: Stage) -> str:
    """Return the required initial local state for a macro-stage."""
    return INITIAL_STATE_BY_STAGE[stage]


def _append_debug_message(session: Session, *lines: str) -> None:
    """Append plain-text debug lines without dropping earlier trace detail."""
    merged_lines = [str(session.debug_message).strip()] if session.debug_message else []
    merged_lines.extend(line for line in lines if line)
    session.debug_message = "\n".join(line for line in merged_lines if line)


def _require_session(session_id: str) -> Session:
    """Load an existing session or raise a clear error."""
    session = state_store.get_session(session_id)

    if session is None:
        raise ValueError(f"Session not found: {session_id}")

    return session


def _stage_module_for(stage_name: str) -> Any:
    """Return the active stage module for the current macro-stage."""
    match stage_name:
        case "classification":
            return classification
        case "coaching":
            return coaching
        case "synthesis":
            return synthesis
        case "pathways":
            return pathways
        case "closure":
            return closure
        case _:
            raise ValueError(f"Unknown stage: {stage_name}")


def _apply_macro_stage_transition(stage_reply: StageReply) -> Session:
    """Apply any requested macro-stage transition and return the updated session."""
    session = stage_reply.session

    if stage_reply.next_stage is None:
        return session

    previous_stage = session.stage
    previous_state = session.state
    session.stage = stage_reply.next_stage.value
    session.state = _initial_state_for_stage(stage_reply.next_stage)
    session.stage_context = {}
    session.stage_turn_count = 0

    _append_debug_message(
        session,
        (
            "Macro transition applied: "
            f"{previous_stage}/{previous_state} -> "
            f"{session.stage}/{session.state}."
        ),
    )
    return session


def _run_coaching_step(module: Any, stage_reply: StageReply, step_index: int) -> StageReply:
    """Run engine.coach(...) and let the stage normalize the visible output."""
    session = stage_reply.session
    coaching_result = engine.coach(
        stage_yaml_path=module.STAGE_YAML_PATH,
        state_name=session.state,
        user_message=session.user_message,
        history=session.chat_history,
        context=session.stage_context,
        output_instruction=getattr(module, "COACHING_OUTPUT_INSTRUCTION", None),
        structured=True,
    )
    coaching_output = module.normalize_coaching_output(session, coaching_result)
    session.coach_message = coaching_output["coach_message"]
    _append_debug_message(
        session,
        coaching_output["debug_message"],
        f"controller_step={step_index}",
        "controller_coaching_ran=true",
    )
    return stage_reply


def _continue_processing(stage_reply: StageReply) -> bool:
    """
    Decide whether the controller should keep processing this turn.

    Rules:
    - explicit stage-module re-entry wins
    - after a macro-stage transition, continue only when no visible text has
      been produced yet for the current user turn
    """
    if stage_reply.continue_turn:
        return True

    if stage_reply.next_stage is None:
        return False

    session = stage_reply.session
    return not bool(session.coach_message)


def _run_stage_loop(session: Session) -> Session:
    """
    Execute the active stage until the current user turn should stop.

    The controller owns which engine step runs for each state type.
    """
    for step_index in range(1, MAX_INTERNAL_STEPS + 1):
        try:
            module = _stage_module_for(session.stage)
        except ValueError as exc:
            session.cancelled = True
            session.state = "cancelled"
            _append_debug_message(
                session,
                f"controller_step={step_index}",
                "controller_stage_error=unknown_stage",
                str(exc),
            )
            return session

        state_type = module.get_state_type(session.state)
        _append_debug_message(
            session,
            f"controller_step={step_index}",
            f"controller_stage={session.stage}",
            f"controller_state={session.state}",
            f"controller_state_type={state_type}",
        )

        match state_type:
            case StateType.EVALUATIVE.value:
                evaluation_result = engine.evaluate(
                    stage_yaml_path=module.STAGE_YAML_PATH,
                    state_name=session.state,
                    user_message=session.user_message,
                    history=session.chat_history,
                    context=session.stage_context,
                    output_instruction=getattr(module, "EVALUATION_OUTPUT_INSTRUCTION", None),
                    structured=True,
                )
                stage_reply = module.apply_evaluation(session, evaluation_result)
                _append_debug_message(
                    stage_reply.session,
                    f"controller_step={step_index}",
                    "controller_evaluation_ran=true",
                )
                if stage_reply.run_coaching:
                    stage_reply = _run_coaching_step(module, stage_reply, step_index)
                else:
                    _append_debug_message(
                        stage_reply.session,
                        f"controller_step={step_index}",
                        "controller_coaching_ran=false",
                    )

            case StateType.PRODUCTION.value:
                coaching_result = engine.coach(
                    stage_yaml_path=module.STAGE_YAML_PATH,
                    state_name=session.state,
                    user_message=session.user_message,
                    history=session.chat_history,
                    context=session.stage_context,
                    output_instruction=getattr(module, "COACHING_OUTPUT_INSTRUCTION", None),
                    structured=True,
                )
                stage_reply = module.apply_production(session, coaching_result)
                _append_debug_message(
                    stage_reply.session,
                    f"controller_step={step_index}",
                    "controller_evaluation_ran=false",
                    "controller_coaching_ran=true",
                )

            case StateType.WAITING.value:
                stage_reply = module.handle_waiting(session)
                _append_debug_message(
                    stage_reply.session,
                    f"controller_step={step_index}",
                    "controller_evaluation_ran=false",
                    "controller_coaching_ran=false",
                )

            case StateType.TERMINAL.value:
                stage_reply = module.handle_terminal(session)
                _append_debug_message(
                    stage_reply.session,
                    f"controller_step={step_index}",
                    "controller_evaluation_ran=false",
                    "controller_coaching_ran=false",
                )

            case _:
                session.cancelled = True
                session.state = "cancelled"
                _append_debug_message(
                    session,
                    f"controller_step={step_index}",
                    "controller_state_type_error=unexpected_value",
                    f"controller_unexpected_state_type={state_type}",
                )
                return session

        session = _apply_macro_stage_transition(stage_reply)
        if _continue_processing(stage_reply):
            continue

        return session

    session.cancelled = True
    _append_debug_message(
        session,
        "controller_loop_guard_triggered=true",
        f"controller_max_internal_steps={MAX_INTERNAL_STEPS}",
    )
    return session


def init_session(session_id: str | None = None) -> Session:
    """Initialize, persist, and return a new session."""
    session = Session(
        session_id=session_id or str(uuid.uuid4()),
        stage=Stage.CLASSIFICATION.value,
        state=_initial_state_for_stage(Stage.CLASSIFICATION),
        debug_message="Session initialized.",
    )
    state_store.save_session(session)
    return session


def handle_user_msg(session_id: str, user_message: str) -> Session:
    """Apply one user turn, execute the V3.1 state loop, persist, and return."""
    session = _require_session(session_id)

    session.evaluation_message = None
    session.coach_message = None
    session.debug_message = None

    session.user_message = user_message
    session.turn_count += 1
    session.stage_turn_count += 1
    session.chat_history.append(ChatMessage(role=ChatRole.USER, message=user_message))

    session = _run_stage_loop(session)

    if session.coach_message:
        session.chat_history.append(
            ChatMessage(role=ChatRole.ASSISTANT, message=session.coach_message)
        )

    state_store.save_session(session)
    return session


def get_debug(session_id: str) -> Session:
    """Return the current session for the debug endpoint."""
    return _require_session(session_id)
