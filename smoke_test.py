"""Regression smoke test for the first real functional slice of Coach V3."""

from __future__ import annotations

from inspect import signature

from fastapi.testclient import TestClient

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
    SynthesisState,
)
from backend.models import DebugReply, Session, SessionView, StageReply, UserMsgReply
from backend.state_store import state_store
from backend.stages import classification, closure, coaching, pathways, synthesis


def banner(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"OK: {message}")


def test_imports() -> None:
    banner("1. Import smoke test")

    check(app.title == "Coach V3 API", "FastAPI app imports correctly")
    check(Stage.CLASSIFICATION.value == "classification", "Stage enum is available")
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


def test_stage_signatures() -> None:
    banner("2. Stage module signature test")

    modules = {
        "classification": classification,
        "coaching": coaching,
        "synthesis": synthesis,
        "pathways": pathways,
        "closure": closure,
    }

    for name, module in modules.items():
        sig = signature(module.handle_stage)
        params = list(sig.parameters.keys())
        check(params == ["session"], f"{name}.handle_stage signature is {sig}")


def test_controller_transition_initial_states() -> None:
    banner("3. Controller transition initial-state mapping")

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
            transitioned.debug_message is not None
            and "Macro transition applied" in transitioned.debug_message,
            "Macro-stage transition appends explicit debug output",
        )


def test_controller_classification_flows() -> dict[str, str]:
    banner("4. Controller classification flow smoke test")

    state_store.clear()

    session = init_session()

    check(bool(session.session_id), "Session initializes with a session_id")
    check(session.stage == "classification", "Initial macro-stage is classification")
    check(session.state == "evaluating", "Initial local state is evaluating")
    check(session.debug_message == "Session initialized.", "Init debug message is set")
    check(
        state_store.get_session(session.session_id) is not None,
        "Initialized session is persisted in state_store",
    )

    debug_session = get_debug(session.session_id)
    check(
        debug_session.session_id == session.session_id,
        "Debug retrieval returns the same session",
    )
    check(
        debug_session.debug_message == "Session initialized.",
        "Debug retrieval exposes the current debug message",
    )

    valid_message = (
        "I'm overwhelmed at work and I can't decide whether to quit "
        "or ask my manager for help."
    )
    valid_updated = handle_user_msg(session.session_id, valid_message)

    check(
        valid_updated.session_id == session.session_id,
        "Valid flow keeps the same session_id",
    )
    check(
        valid_updated.user_message == valid_message,
        "Valid flow stores the user message",
    )
    check(
        valid_updated.stage == Stage.COACHING.value,
        "Valid classification advances to coaching",
    )
    check(
        valid_updated.state == CoachingState.GUIDING.value,
        "Valid classification sets coaching local state to guiding",
    )
    check(valid_updated.cancelled is False, "Valid classification does not cancel")
    check(
        valid_updated.evaluation_message is not None
        and "valid" in valid_updated.evaluation_message.lower(),
        "Valid classification sets a useful evaluation_message",
    )
    check(
        valid_updated.coach_message is not None and len(valid_updated.coach_message) > 0,
        "Valid classification sets a coach_message",
    )
    check(
        len(valid_updated.chat_history) == 2,
        "Valid classification stores the user turn and coach reply",
    )
    check(
        valid_updated.chat_history[0].role == ChatRole.USER,
        "Valid flow first chat entry role is USER",
    )
    check(
        valid_updated.chat_history[1].role == ChatRole.ASSISTANT,
        "Valid flow second chat entry role is ASSISTANT",
    )
    check(
        valid_updated.debug_message is not None
        and "classification_outcome=valid" in valid_updated.debug_message
        and "Macro transition applied" in valid_updated.debug_message,
        "Valid classification keeps detailed debug output including macro transition",
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
        ambiguous_updated.cancelled is False,
        "Ambiguous classification does not cancel immediately",
    )
    check(
        ambiguous_updated.evaluation_message is not None
        and "ambiguous" in ambiguous_updated.evaluation_message.lower(),
        "Ambiguous classification sets a useful evaluation_message",
    )
    check(
        ambiguous_updated.coach_message is not None
        and "clearer sentence" in ambiguous_updated.coach_message.lower(),
        "Ambiguous classification asks for clarification",
    )
    check(
        ambiguous_updated.debug_message is not None
        and "classification_outcome=ambiguous" in ambiguous_updated.debug_message,
        "Ambiguous classification debug trace surfaces the ambiguous outcome",
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
    check(
        invalid_updated.cancelled is True,
        "Invalid classification sets session.cancelled",
    )
    check(
        invalid_updated.evaluation_message is not None
        and "invalid" in invalid_updated.evaluation_message.lower(),
        "Invalid classification sets a useful evaluation_message",
    )
    check(
        invalid_updated.debug_message is not None
        and "classification_outcome=invalid" in invalid_updated.debug_message,
        "Invalid classification debug trace surfaces the invalid outcome",
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
        "Bounded ambiguity scenario first turn becomes ambiguous",
    )
    check(
        second_ambiguous.stage == Stage.CLASSIFICATION.value,
        "Bounded ambiguity cancellation stays in classification",
    )
    check(
        second_ambiguous.state == ClassificationState.CANCELLED.value,
        "Bounded ambiguity cancels on unresolved clarification",
    )
    check(
        second_ambiguous.cancelled is True,
        "Bounded ambiguity sets session.cancelled",
    )
    check(
        second_ambiguous.evaluation_message is not None
        and "cancelled after clarification"
        in second_ambiguous.evaluation_message.lower(),
        "Bounded ambiguity makes the cancellation reason explicit",
    )
    check(
        second_ambiguous.debug_message is not None
        and "bounded_ambiguity_triggered=true" in second_ambiguous.debug_message,
        "Bounded ambiguity is explicit in debug output",
    )
    check(
        len(second_ambiguous.chat_history) == 4,
        "Bounded ambiguity stores both turns plus both assistant replies",
    )

    print(f"valid session_id: {valid_updated.session_id}")
    print(f"valid stage/state: {valid_updated.stage} / {valid_updated.state}")
    print(f"ambiguous stage/state: {ambiguous_updated.stage} / {ambiguous_updated.state}")
    print(f"invalid stage/state: {invalid_updated.stage} / {invalid_updated.state}")
    print(
        "bounded ambiguity stage/state: "
        f"{second_ambiguous.stage} / {second_ambiguous.state}"
    )

    return {
        "valid": valid_updated.session_id,
        "ambiguous": ambiguous_updated.session_id,
        "invalid": invalid_updated.session_id,
        "bounded": second_ambiguous.session_id,
    }


def test_api_flow() -> str:
    banner("5. FastAPI in-process smoke test")

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
    check(
        "debug_message" in debug_payload,
        "Debug payload contains debug_message",
    )
    print("debug payload:", debug_payload)

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
        "User reply stage advances to coaching on valid classification",
    )
    check(
        user_payload["session"]["state"] == CoachingState.GUIDING.value,
        "User reply state is the coaching initial local state",
    )
    check(
        "coach_message" in user_payload,
        "User reply contains coach_message field",
    )
    check(
        user_payload["coach_message"] is not None and len(user_payload["coach_message"]) > 0,
        "User reply exposes the latest coach_message",
    )
    print("user payload:", user_payload)

    return session_id


def test_negative_api_cases() -> None:
    banner("6. Negative API tests")

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
    banner("Coach V3 functional-slice smoke test")

    test_imports()
    test_stage_signatures()
    test_controller_transition_initial_states()
    controller_session_ids = test_controller_classification_flows()
    api_session_id = test_api_flow()
    test_negative_api_cases()

    banner("All smoke tests passed")
    print(f"Controller smoke session_ids: {controller_session_ids}")
    print(f"API smoke session_id: {api_session_id}")
    print("Classification is now the first real V3 slice under regression coverage.")


if __name__ == "__main__":
    main()
