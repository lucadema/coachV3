"""Regression smoke test for the Coach V3.1 execution model."""

from __future__ import annotations

import os
from inspect import signature
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from backend import engine
from backend.api import app
from backend.controller import (
    _apply_macro_stage_transition,
    get_debug,
    handle_user_msg,
    init_session,
)
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
from backend.models import ChatMessage, DebugReply, Session, SessionView, StageReply, UserMsgReply
from backend.state_store import StateStore, state_store
from backend.stages import classification, closure, coaching, pathways, synthesis


os.environ["COACHV3_USE_LLM"] = "0"


def banner(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"OK: {message}")


def make_session(
    session_id: str,
    stage: Stage,
    state: str,
    user_message: str | None = None,
    chat_history: list[ChatMessage] | None = None,
) -> Session:
    """Create and persist a test session with the given stage/state."""
    session = Session(
        session_id=session_id,
        stage=stage.value,
        state=state,
        user_message=user_message,
        chat_history=chat_history or [],
    )
    state_store.save_session(session)
    return session


def test_imports() -> None:
    banner("1. Import smoke test")

    check(app.title == "Coach V3 API", "FastAPI app imports correctly")
    check(Stage.CLASSIFICATION.value == "classification", "Stage enum is available")
    check(StateType.EVALUATIVE.value == "evaluative", "StateType enum is available")
    check(
        ClassificationState.EVALUATING.value == "evaluating",
        "ClassificationState enum is available",
    )
    check(
        CoachingState.GUIDING.value == "guiding",
        "CoachingState enum is available",
    )
    check(ChatRole.USER.value == "user", "ChatRole enum is available")
    check(Session.__name__ == "Session", "Session model is available")
    check(SessionView.__name__ == "SessionView", "SessionView model is available")
    check(UserMsgReply.__name__ == "UserMsgReply", "UserMsgReply model is available")
    check(DebugReply.__name__ == "DebugReply", "DebugReply model is available")
    check(StageReply.__name__ == "StageReply", "StageReply model is available")
    check("turn_count" in Session.model_fields, "Session has turn_count")
    check("stage_turn_count" in Session.model_fields, "Session has stage_turn_count")
    check("run_coaching" in StageReply.model_fields, "StageReply has run_coaching")
    check("continue_turn" in StageReply.model_fields, "StageReply has continue_turn")


def test_stage_contracts() -> None:
    banner("2. Stage module contract smoke test")

    state_cases = [
        (classification.get_state_type, ClassificationState.EVALUATING.value, StateType.EVALUATIVE.value),
        (classification.get_state_type, ClassificationState.AMBIGUOUS.value, StateType.WAITING.value),
        (coaching.get_state_type, CoachingState.GUIDING.value, StateType.EVALUATIVE.value),
        (synthesis.get_state_type, SynthesisState.PREPARING.value, StateType.PRODUCTION.value),
        (synthesis.get_state_type, SynthesisState.VALIDATING.value, StateType.WAITING.value),
        (pathways.get_state_type, PathwaysState.PREPARING.value, StateType.PRODUCTION.value),
        (pathways.get_state_type, PathwaysState.PRESENTING.value, StateType.WAITING.value),
        (closure.get_state_type, ClosureState.PREPARING.value, StateType.PRODUCTION.value),
    ]

    for fn, state_name, expected in state_cases:
        check(
            fn(state_name) == expected,
            f"{fn.__module__.split('.')[-1]}.get_state_type({state_name}) == {expected}",
        )

    check(
        list(signature(classification.apply_evaluation).parameters.keys()) == ["session", "result"],
        "classification.apply_evaluation signature is stable",
    )
    check(
        list(signature(coaching.apply_evaluation).parameters.keys()) == ["session", "result"],
        "coaching.apply_evaluation signature is stable",
    )
    check(
        list(signature(synthesis.apply_production).parameters.keys()) == ["session", "result"],
        "synthesis.apply_production signature is stable",
    )
    check(
        list(signature(pathways.handle_waiting).parameters.keys()) == ["session"],
        "pathways.handle_waiting signature is stable",
    )

    sample_pathways_session = Session(
        session_id="pathways-format",
        stage=Stage.PATHWAYS.value,
        state=PathwaysState.PREPARING.value,
        chat_history=[
            ChatMessage(role=ChatRole.ASSISTANT, message="Validated synthesis text."),
        ],
    )
    fallback_pathways_text = pathways._default_pathways_message(sample_pathways_session)
    check(
        "## " in fallback_pathways_text
        and "Orientation:" in fallback_pathways_text
        and "Conditions:" in fallback_pathways_text,
        "Pathways fallback text uses a card-friendly structured format",
    )
    check(
        "## <SHORT TITLE>" in pathways.COACHING_OUTPUT_INSTRUCTION,
        "Pathways coaching output instruction asks for titled sections",
    )


def test_state_store_persistence() -> None:
    banner("3. State store persistence")

    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "sessions.sqlite3"
        store_one = StateStore(db_path=db_path)
        session = Session(
            session_id="persisted-session",
            stage=Stage.CLASSIFICATION.value,
            state=ClassificationState.EVALUATING.value,
            user_message="Persist me",
            coach_message="Visible reply",
            stage_context={"source": "smoke"},
        )
        store_one.save_session(session)

        store_two = StateStore(db_path=db_path)
        restored = store_two.get_session("persisted-session")

        check(restored is not None, "StateStore restores a saved session from SQLite")
        check(restored.session_id == session.session_id, "Restored session_id matches")
        check(restored.coach_message == "Visible reply", "Restored coach_message matches")
        check(
            restored.stage_context.get("source") == "smoke",
            "Restored stage_context matches",
        )


def test_engine_raw_llm_reply_debug() -> None:
    banner("4. Engine raw LLM reply debug")

    original_call_llm = engine._call_llm

    evaluation_raw_reply = (
        '{\n'
        '  "coaching_outcome": "CONTINUE",\n'
        '  "evaluation_message": "Keep exploring.",\n'
        '  "debug_message": "raw evaluation debug"\n'
        '}'
    )
    coaching_raw_reply = (
        '{\n'
        '  "coach_message": "What is the core tension?",\n'
        '  "debug_message": "raw coaching debug"\n'
        '}'
    )

    try:
        engine._call_llm = lambda _prompt: (evaluation_raw_reply, "llm_call_status=ok")
        evaluation_output = engine.evaluate(
            stage_yaml_path="backend/config/coaching.yaml",
            state_name=CoachingState.GUIDING.value,
            user_message="I need to understand the conflict better.",
            structured=True,
        )
        check(isinstance(evaluation_output, dict), "Evaluation output is structured")
        evaluation_debug = str(evaluation_output.get("debug_message", ""))
        check(
            "evaluation_llm_reply_raw_begin" in evaluation_debug
            and "evaluation_llm_reply_raw_end" in evaluation_debug,
            "Evaluation debug includes raw LLM reply boundaries",
        )
        check(
            evaluation_raw_reply in evaluation_debug,
            "Evaluation debug includes the full raw LLM reply",
        )
        check(
            "evaluation_prompt_full_begin" in evaluation_debug
            and "evaluation_prompt_full_end" in evaluation_debug,
            "Evaluation debug includes full prompt boundaries",
        )
        check(
            "Latest user message:\nI need to understand the conflict better." in evaluation_debug,
            "Evaluation debug includes the full runtime prompt text",
        )

        engine._call_llm = lambda _prompt: (coaching_raw_reply, "llm_call_status=ok")
        coaching_output = engine.coach(
            stage_yaml_path="backend/config/coaching.yaml",
            state_name=CoachingState.GUIDING.value,
            user_message="I need to understand the conflict better.",
            structured=True,
        )
        check(isinstance(coaching_output, dict), "Coaching output is structured")
        coaching_debug = str(coaching_output.get("debug_message", ""))
        check(
            "coaching_llm_reply_raw_begin" in coaching_debug
            and "coaching_llm_reply_raw_end" in coaching_debug,
            "Coaching debug includes raw LLM reply boundaries",
        )
        check(
            coaching_raw_reply in coaching_debug,
            "Coaching debug includes the full raw LLM reply",
        )
        check(
            "coaching_prompt_full_begin" in coaching_debug
            and "coaching_prompt_full_end" in coaching_debug,
            "Coaching debug includes full prompt boundaries",
        )
    finally:
        engine._call_llm = original_call_llm


def test_engine_simplified_yaml_prompt_order() -> None:
    banner("5. Engine simplified YAML prompt order")

    config = {
        "meta": {
            "stage": "unit-test",
            "description": "Description should not be assembled.",
        },
        "common": {
            "preamble": "01 common preamble",
            "role": "02 common role",
            "rules": "03 common rules",
            "output_spec": "04 common output spec",
        },
        "stage": {
            "purpose": "05 stage purpose",
            "rules": "06 stage rules",
            "evaluation": "07 stage evaluation",
            "coaching": "07 stage coaching",
        },
        "states": {
            "active": {
                "purpose": "08 state purpose",
                "evaluation": "09 state evaluation",
                "coaching": "09 state coaching",
            },
        },
    }

    evaluation_prompt = engine._assemble_prompt(config, "active", "evaluation")
    check(
        evaluation_prompt
        == "\n\n".join(
            [
                "01 common preamble",
                "02 common role",
                "03 common rules",
                "04 common output spec",
                "05 stage purpose",
                "06 stage rules",
                "07 stage evaluation",
                "08 state purpose",
                "09 state evaluation",
            ]
        ),
        "Evaluation prompt uses the simplified YAML order",
    )
    check(
        "Description should not be assembled." not in evaluation_prompt,
        "Evaluation prompt ignores meta.description",
    )

    coaching_prompt = engine._assemble_prompt(config, "active", "coaching")
    check(
        coaching_prompt
        == "\n\n".join(
            [
                "01 common preamble",
                "02 common role",
                "03 common rules",
                "04 common output spec",
                "05 stage purpose",
                "06 stage rules",
                "07 stage coaching",
                "08 state purpose",
                "09 state coaching",
            ]
        ),
        "Coaching prompt uses the simplified YAML order",
    )


def test_controller_transition_initial_states() -> None:
    banner("6. Controller transition initial-state mapping")

    cases = [
        (Stage.CLASSIFICATION, ClassificationState.EVALUATING.value),
        (Stage.COACHING, CoachingState.GUIDING.value),
        (Stage.SYNTHESIS, SynthesisState.PREPARING.value),
        (Stage.PATHWAYS, PathwaysState.PREPARING.value),
        (Stage.CLOSURE, ClosureState.PREPARING.value),
    ]

    for index, (next_stage, expected_state) in enumerate(cases, start=1):
        session = Session(
            session_id=f"transition-{index}",
            stage=Stage.CLASSIFICATION.value,
            state="placeholder",
            debug_message="pre-transition debug",
            stage_context={"old": "value"},
            stage_turn_count=3,
        )

        transitioned = _apply_macro_stage_transition(
            StageReply(session=session, next_stage=next_stage)
        )

        check(
            transitioned.stage == next_stage.value,
            f"Macro-stage transition sets stage to {next_stage.value}",
        )
        check(
            transitioned.state == expected_state,
            f"Macro-stage transition sets initial state {expected_state}",
        )
        check(
            transitioned.stage_context == {},
            "Macro-stage transition resets stage_context",
        )
        check(
            transitioned.stage_turn_count == 0,
            "Macro-stage transition resets stage_turn_count",
        )
        check(
            transitioned.debug_message is not None
            and "Macro transition applied" in transitioned.debug_message,
            "Macro-stage transition appends explicit debug output",
        )


def test_evaluation_and_user_text_separation() -> None:
    banner("7. Evaluation vs coaching separation")

    original_evaluate = engine.evaluate
    original_coach = engine.coach

    def fake_evaluate(**kwargs: object) -> dict[str, str]:
        stage_name = str(kwargs["stage_yaml_path"])
        if stage_name.endswith("classification.yaml"):
            return {
                "classification_label": "AMBIGUOUS",
                "evaluation_message": "Classification result: ambiguous.",
                "coach_message": "THIS SHOULD NOT LEAK",
                "debug_message": "fake_classification_eval=ambiguous",
            }
        return {
            "coaching_outcome": "CONTINUE",
            "evaluation_message": "Coaching result: continue.",
            "coach_message": "THIS SHOULD NOT LEAK",
            "debug_message": "fake_coaching_eval=continue",
        }

    def fake_coach(**kwargs: object) -> dict[str, str]:
        stage_name = str(kwargs["stage_yaml_path"])
        if stage_name.endswith("classification.yaml"):
            return {
                "coach_message": "Please clarify the work challenge in one sentence.",
                "debug_message": "fake_classification_coach=ok",
            }
        return {
            "coach_message": "What feels most important to clarify next?",
            "debug_message": "fake_coaching_coach=ok",
        }

    engine.evaluate = fake_evaluate
    engine.coach = fake_coach

    try:
        state_store.clear()
        classification_session = init_session(session_id="eval-separation-classification")
        classification_result = handle_user_msg(
            classification_session.session_id,
            "I need help.",
        )
        check(
            classification_result.coach_message
            == "Please clarify the work challenge in one sentence.",
            "Classification uses the coaching step for visible text",
        )
        check(
            "THIS SHOULD NOT LEAK" not in str(classification_result.coach_message),
            "Classification ignores stray user-facing text from evaluation output",
        )

        make_session(
            session_id="eval-separation-coaching",
            stage=Stage.COACHING,
            state=CoachingState.GUIDING.value,
        )
        coaching_result = handle_user_msg(
            "eval-separation-coaching",
            "The conflict is mostly about priorities and escalation.",
        )
        check(
            coaching_result.coach_message == "What feels most important to clarify next?",
            "Coaching uses the coaching step for visible text",
        )
        check(
            "THIS SHOULD NOT LEAK" not in str(coaching_result.coach_message),
            "Coaching ignores stray user-facing text from evaluation output",
        )
    finally:
        engine.evaluate = original_evaluate
        engine.coach = original_coach


def test_controller_classification_and_coaching_flow() -> dict[str, str]:
    banner("8. Controller classification and coaching flow")

    state_store.clear()
    session = init_session()

    check(bool(session.session_id), "Session initializes with a session_id")
    check(session.stage == "classification", "Initial macro-stage is classification")
    check(session.state == "evaluating", "Initial local state is evaluating")
    check(session.turn_count == 0, "Initial turn_count is zero")
    check(session.stage_turn_count == 0, "Initial stage_turn_count is zero")
    check(session.debug_message == "Session initialized.", "Init debug message is set")

    valid_message = (
        "I'm overwhelmed at work and I can't decide whether to quit "
        "or ask my manager for help."
    )
    valid_updated = handle_user_msg(session.session_id, valid_message)

    check(
        valid_updated.stage == Stage.COACHING.value,
        "Valid classification advances into Coaching in the same turn",
    )
    check(
        valid_updated.state == CoachingState.GUIDING.value,
        "Valid classification lands in the Coaching guiding state",
    )
    check(valid_updated.cancelled is False, "Valid classification does not cancel")
    check(valid_updated.turn_count == 1, "First user turn increments turn_count")
    check(
        valid_updated.stage_turn_count == 0,
        "Stage transition resets stage_turn_count for the new stage",
    )
    check(
        valid_updated.evaluation_message is not None
        and "continue" in valid_updated.evaluation_message.lower(),
        "The latest evaluation_message comes from the active Coaching evaluation",
    )
    check(
        valid_updated.coach_message is not None
        and "important to understand" in valid_updated.coach_message.lower(),
        "The same turn ends with a coaching-generated user-facing question",
    )
    check(
        len(valid_updated.chat_history) == 2,
        "The valid flow stores one user turn and one assistant reply",
    )
    check(
        valid_updated.debug_message is not None
        and "controller_state_type=evaluative" in valid_updated.debug_message
        and "classification_transition=evaluating_to_completed" in valid_updated.debug_message
        and "coaching_transition=guiding_to_guiding" in valid_updated.debug_message,
        "Valid flow keeps explicit controller and stage debug traces",
    )

    coaching_follow_up = handle_user_msg(
        session.session_id,
        "The conflict is mostly about unclear priorities and how to raise them.",
    )
    check(
        coaching_follow_up.stage == Stage.COACHING.value,
        "Coaching follow-up remains in the Coaching macro-stage",
    )
    check(
        coaching_follow_up.state == CoachingState.GUIDING.value,
        "Coaching follow-up remains in guiding on offline CONTINUE fallback",
    )
    check(
        coaching_follow_up.turn_count == 2,
        "Second user turn increments turn_count again",
    )
    check(
        coaching_follow_up.stage_turn_count == 1,
        "The first direct coaching user turn increments stage_turn_count",
    )

    ambiguous_session = init_session(session_id="ambiguous-session")
    ambiguous_updated = handle_user_msg(ambiguous_session.session_id, "I need help.")
    check(
        ambiguous_updated.stage == Stage.CLASSIFICATION.value,
        "Ambiguous classification remains in classification",
    )
    check(
        ambiguous_updated.state == ClassificationState.AMBIGUOUS.value,
        "Ambiguous classification sets local state to ambiguous",
    )
    check(
        ambiguous_updated.coach_message is not None
        and "clearer sentence" in ambiguous_updated.coach_message.lower(),
        "Ambiguous classification uses coaching to ask for clarification",
    )
    check(
        "classification_transition=evaluating_to_ambiguous" in str(ambiguous_updated.debug_message),
        "Ambiguous classification debug shows the local transition",
    )

    invalid_session = init_session(session_id="invalid-session")
    invalid_updated = handle_user_msg(
        invalid_session.session_id,
        "Tell me a joke about meetings.",
    )
    check(
        invalid_updated.stage == Stage.CLASSIFICATION.value,
        "Invalid classification stays in classification",
    )
    check(
        invalid_updated.state == ClassificationState.CANCELLED.value,
        "Invalid classification cancels the session",
    )
    check(invalid_updated.cancelled is True, "Invalid classification sets cancelled")
    check(
        invalid_updated.coach_message is not None
        and "can't continue" in invalid_updated.coach_message.lower(),
        "Invalid classification uses coaching/boundary text for the visible reply",
    )

    invalid_resubmitted = handle_user_msg(
        invalid_session.session_id,
        "Trying to continue after cancellation.",
    )
    check(
        invalid_resubmitted.state == ClassificationState.CANCELLED.value,
        "Cancelled classification remains cancelled on resubmission",
    )
    check(
        "already_cancelled" in str(invalid_resubmitted.debug_message),
        "Cancelled classification resubmission is handled as a terminal state",
    )

    bounded_session = init_session(session_id="bounded-ambiguity-session")
    first_ambiguous = handle_user_msg(bounded_session.session_id, "I need help.")
    first_ambiguous_state = first_ambiguous.state
    second_ambiguous = handle_user_msg(
        bounded_session.session_id,
        "Still not sure, just help.",
    )
    check(
        first_ambiguous_state == ClassificationState.AMBIGUOUS.value,
        "Bounded ambiguity first turn becomes ambiguous",
    )
    check(
        second_ambiguous.state == ClassificationState.CANCELLED.value,
        "Bounded ambiguity cancels on unresolved clarification",
    )
    check(second_ambiguous.cancelled is True, "Bounded ambiguity sets cancelled")
    check(
        "bounded_ambiguity_triggered=true" in str(second_ambiguous.debug_message),
        "Bounded ambiguity is explicit in debug output",
    )
    check(
        len(second_ambiguous.chat_history) == 4,
        "Bounded ambiguity still stores both user turns and both assistant replies",
    )

    return {
        "valid": valid_updated.session_id,
        "ambiguous": ambiguous_updated.session_id,
        "invalid": invalid_updated.session_id,
        "bounded": second_ambiguous.session_id,
    }


def test_v31_synthesis_pathways_closure_flow() -> None:
    banner("9. Synthesis, Pathways, and Closure V3.1 flow")

    original_evaluate = engine.evaluate
    original_coach = engine.coach
    evaluate_calls: list[dict[str, object]] = []
    coach_calls: list[dict[str, object]] = []

    def fake_evaluate(**kwargs: object) -> dict[str, str]:
        evaluate_calls.append(kwargs)
        stage_name = str(kwargs["stage_yaml_path"])
        if stage_name.endswith("coaching.yaml"):
            return {
                "coaching_outcome": "COMPLETE",
                "evaluation_message": "Coaching result: complete.",
                "debug_message": "fake_coaching_eval=complete",
            }
        raise AssertionError(f"Unexpected evaluation call for {stage_name}")

    def fake_coach(**kwargs: object) -> dict[str, str]:
        coach_calls.append(kwargs)
        stage_name = str(kwargs["stage_yaml_path"])
        state_name = str(kwargs["state_name"])

        if stage_name.endswith("synthesis.yaml") and state_name == SynthesisState.PREPARING.value:
            return {
                "coach_message": "SYNTHESIS TEXT",
                "debug_message": "fake_synthesis_prepare=ok",
            }
        if stage_name.endswith("synthesis.yaml") and state_name == SynthesisState.REFINING.value:
            return {
                "coach_message": "REVISED SYNTHESIS TEXT",
                "debug_message": "fake_synthesis_refine=ok",
            }
        if stage_name.endswith("pathways.yaml") and state_name == PathwaysState.PREPARING.value:
            return {
                "coach_message": "PATHWAYS TEXT",
                "debug_message": "fake_pathways_prepare=ok",
            }
        if stage_name.endswith("closure.yaml") and state_name == ClosureState.PREPARING.value:
            return {
                "coach_message": "CLOSING TEXT",
                "debug_message": "fake_closure_prepare=ok",
            }
        return {
            "coach_message": "UNEXPECTED COACH OUTPUT",
            "debug_message": "fake_coach_unexpected",
        }

    engine.evaluate = fake_evaluate
    engine.coach = fake_coach

    try:
        state_store.clear()
        coaching_session = make_session(
            session_id="coaching-to-synthesis",
            stage=Stage.COACHING,
            state=CoachingState.GUIDING.value,
            chat_history=[
                ChatMessage(role=ChatRole.USER, message="I need help handling a conflict with my manager."),
                ChatMessage(role=ChatRole.ASSISTANT, message="What makes the conflict hard to address?"),
            ],
        )

        synthesis_entry = handle_user_msg(
            coaching_session.session_id,
            "I can now explain the conflict clearly and what is blocking me.",
        )
        check(
            synthesis_entry.stage == Stage.SYNTHESIS.value,
            "Coaching COMPLETE transitions into Synthesis",
        )
        check(
            synthesis_entry.state == SynthesisState.VALIDATING.value,
            "Synthesis preparing auto-runs and lands in validating",
        )
        check(
            synthesis_entry.coach_message == "SYNTHESIS TEXT",
            "Synthesis preparing produces the visible synthesis text",
        )
        check(
            len(evaluate_calls) == 1 and str(evaluate_calls[0]["stage_yaml_path"]).endswith("coaching.yaml"),
            "Only Coaching uses evaluation in this flow",
        )

        pathways_entry = handle_user_msg(
            coaching_session.session_id,
            "yes",
        )
        check(
            pathways_entry.stage == Stage.PATHWAYS.value,
            "Accepting synthesis transitions into Pathways",
        )
        check(
            pathways_entry.state == PathwaysState.PRESENTING.value,
            "Pathways preparing auto-runs and lands in presenting",
        )
        check(
            pathways_entry.coach_message == "PATHWAYS TEXT",
            "Pathways preparing produces the visible pathways text",
        )
        check(
            len(evaluate_calls) == 1,
            "Synthesis and Pathways do not invoke evaluation by default",
        )

        closure_entry = handle_user_msg(
            coaching_session.session_id,
            "selection:pathway_one",
        )
        check(
            closure_entry.stage == Stage.CLOSURE.value,
            "Pathways acknowledgement transitions into Closure",
        )
        check(
            closure_entry.state == ClosureState.COMPLETED.value,
            "Closure preparing auto-runs and completes the session",
        )
        check(
            closure_entry.coach_message == "CLOSING TEXT",
            "Closure produces the visible closing text",
        )
        check(closure_entry.completed is True, "Closure marks the session completed")
        check(
            len(evaluate_calls) == 1,
            "Closure also does not invoke evaluation by default",
        )

        refinement_session = make_session(
            session_id="synthesis-refinement",
            stage=Stage.SYNTHESIS,
            state=SynthesisState.VALIDATING.value,
            chat_history=[
                ChatMessage(role=ChatRole.USER, message="I need help deciding how to raise a resourcing issue."),
                ChatMessage(role=ChatRole.ASSISTANT, message="INITIAL SYNTHESIS TEXT"),
            ],
        )
        refined = handle_user_msg(
            refinement_session.session_id,
            "Not quite. Include the budget pressure and timeline risk.",
        )
        check(
            refined.stage == Stage.PATHWAYS.value,
            "A refinement turn still advances to Pathways after the final synthesis",
        )
        check(
            refined.state == PathwaysState.PREPARING.value,
            "After refinement the next stage is Pathways preparing",
        )
        check(
            refined.coach_message == "REVISED SYNTHESIS TEXT",
            "The refinement turn returns the revised synthesis text before pathways run",
        )
    finally:
        engine.evaluate = original_evaluate
        engine.coach = original_coach


def test_api_flow() -> str:
    banner("10. FastAPI in-process smoke test")

    state_store.clear()
    client = TestClient(app)

    response = client.get("/health")
    check(response.status_code == 200, "/health returns 200")
    check(response.json() == {"status": "ok"}, "/health payload is correct")

    response = client.get("/session_initialise")
    check(response.status_code == 200, "/session_initialise returns 200")
    init_payload = response.json()

    check("session_id" in init_payload, "Init payload contains session_id")
    check(init_payload["stage"] == "classification", "Init payload stage is classification")
    check(init_payload["state"] == "evaluating", "Init payload state is evaluating")

    session_id = init_payload["session_id"]
    print("init payload:", init_payload)

    response = client.get(f"/debug_trace/{session_id}")
    check(response.status_code == 200, "/debug_trace returns 200 after init")
    debug_payload = response.json()

    check("session" in debug_payload, "Debug payload contains session")
    check(
        debug_payload["session"]["session_id"] == session_id,
        "Debug payload session_id matches",
    )
    check("debug_message" in debug_payload, "Debug payload contains debug_message")
    check("user_message" in debug_payload, "Debug payload contains user_message")
    check(
        "evaluation_message" in debug_payload,
        "Debug payload contains evaluation_message",
    )
    check("coach_message" in debug_payload, "Debug payload contains coach_message")
    check("turn_count" in debug_payload, "Debug payload contains turn_count")
    check(
        "stage_turn_count" in debug_payload,
        "Debug payload contains stage_turn_count",
    )
    check("stage_context" in debug_payload, "Debug payload contains stage_context")
    check(debug_payload["turn_count"] == 0, "Init debug payload turn_count is zero")
    check(
        debug_payload["stage_turn_count"] == 0,
        "Init debug payload stage_turn_count is zero",
    )

    response = client.post(
        "/user_message",
        json={
            "session_id": session_id,
            "user_message": (
                "I'm struggling with a conflict with my manager about "
                "priorities and I need help deciding how to address it."
            ),
        },
    )
    check(response.status_code == 200, "/user_message returns 200")
    user_payload = response.json()

    check("session" in user_payload, "User reply contains session")
    check(
        user_payload["session"]["session_id"] == session_id,
        "User reply session_id matches",
    )
    check(
        user_payload["session"]["stage"] == Stage.COACHING.value,
        "User reply advances into coaching on valid intake",
    )
    check(
        user_payload["session"]["state"] == CoachingState.GUIDING.value,
        "User reply lands in coaching guiding",
    )
    check("coach_message" in user_payload, "User reply contains coach_message field")
    check(
        user_payload["coach_message"] is not None and len(user_payload["coach_message"]) > 0,
        "User reply exposes the latest coach_message",
    )

    response = client.get(f"/debug_trace/{session_id}")
    check(response.status_code == 200, "Post-turn /debug_trace returns 200")
    debug_payload = response.json()
    check(
        debug_payload["user_message"] is not None,
        "Post-turn debug payload exposes latest user_message",
    )
    check(
        debug_payload["evaluation_message"] is not None,
        "Post-turn debug payload exposes latest evaluation_message",
    )
    check(
        debug_payload["coach_message"] is not None,
        "Post-turn debug payload exposes latest coach_message",
    )
    check(
        debug_payload["turn_count"] == 1,
        "Post-turn debug payload increments turn_count",
    )

    return session_id


def test_negative_api_cases() -> None:
    banner("11. Negative API tests")

    client = TestClient(app)

    response = client.post(
        "/user_message",
        json={"session_id": "does-not-exist", "user_message": "hello"},
    )
    check(response.status_code == 404, "Unknown session on /user_message returns 404")

    response = client.get("/debug_trace/does-not-exist")
    check(response.status_code == 404, "Unknown session on /debug_trace returns 404")

    response = client.post("/user_message", json={"session_id": "abc"})
    check(response.status_code == 422, "Invalid body on /user_message returns 422")


def main() -> None:
    banner("Coach V3.1 execution-model smoke test")

    test_imports()
    test_stage_contracts()
    test_state_store_persistence()
    test_engine_raw_llm_reply_debug()
    test_engine_simplified_yaml_prompt_order()
    test_controller_transition_initial_states()
    test_evaluation_and_user_text_separation()
    controller_session_ids = test_controller_classification_and_coaching_flow()
    test_v31_synthesis_pathways_closure_flow()
    api_session_id = test_api_flow()
    test_negative_api_cases()

    banner("All smoke tests passed")
    print(f"Controller smoke session_ids: {controller_session_ids}")
    print(f"API smoke session_id: {api_session_id}")
    print("Coach V3 now runs on the V3.1 controller/stage execution model.")


if __name__ == "__main__":
    main()
