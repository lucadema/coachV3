"""
Lightweight smoke test for the Coach V3 scaffold.

Purpose
-------
This script is a living regression check for the current scaffold.
It is intentionally small and should be updated as the contracts and
expected behaviour evolve.

What it checks
--------------
1. Imports load correctly
2. Stage handler signatures match the simplified internal contract
3. Controller + state store basic flow works
4. FastAPI endpoints work in-process through TestClient
5. Negative API cases return the expected HTTP codes

How to run
----------
From the repo root (coachV3), with the virtual environment activated:

    python smoke_test.py

Important
---------
This script assumes the current simplified scaffold contract:
- controller returns Session directly
- stage handlers expose handle_stage(session: Session) -> StageReply
- GET /session_initialise returns SessionView directly
- POST /user_message returns UserMsgReply
- GET /debug_trace/{session_id} returns DebugReply
"""

from __future__ import annotations

from inspect import signature

from fastapi.testclient import TestClient

from backend.api import app
from backend.controller import get_debug, handle_user_msg, init_session
from backend.enums import ChatRole, ClassificationState, Stage
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


def test_controller_flow() -> str:
    banner("3. Controller + state store smoke test")

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

    updated = handle_user_msg(session.session_id, "This is a scaffold smoke test")

    check(
        updated.session_id == session.session_id,
        "User turn keeps the same session_id",
    )
    check(
        updated.user_message == "This is a scaffold smoke test",
        "User message is stored on the session",
    )
    check(updated.stage == "classification", "Stage remains classification in placeholder flow")
    check(updated.state == "evaluating", "State remains evaluating in placeholder flow")
    check(len(updated.chat_history) == 1, "User turn adds one chat history entry")
    check(
        updated.chat_history[0].role == ChatRole.USER,
        "Chat history entry role is USER",
    )
    check(
        updated.chat_history[0].message == "This is a scaffold smoke test",
        "Chat history entry stores the user text",
    )
    check(
        updated.debug_message is not None and len(updated.debug_message) > 0,
        "Stage handler sets a debug message",
    )

    print(f"session_id: {updated.session_id}")
    print(f"stage/state: {updated.stage} / {updated.state}")
    print(f"debug_message: {updated.debug_message}")

    return updated.session_id


def test_api_flow() -> str:
    banner("4. FastAPI in-process smoke test")

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
            "user_message": "API smoke test message",
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
        user_payload["session"]["stage"] == "classification",
        "User reply stage remains classification in placeholder flow",
    )
    check(
        user_payload["session"]["state"] == "evaluating",
        "User reply state remains evaluating in placeholder flow",
    )
    check(
        "coach_message" in user_payload,
        "User reply contains coach_message field",
    )
    print("user payload:", user_payload)

    return session_id


def test_negative_api_cases() -> None:
    banner("5. Negative API tests")

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
    banner("Coach V3 scaffold smoke test")

    test_imports()
    test_stage_signatures()
    controller_session_id = test_controller_flow()
    api_session_id = test_api_flow()
    test_negative_api_cases()

    banner("All smoke tests passed")
    print(f"Controller smoke session_id: {controller_session_id}")
    print(f"API smoke session_id: {api_session_id}")
    print("You can now update this script incrementally as the scaffold evolves.")


if __name__ == "__main__":
    main()
