"""
Static FastAPI backend for local React UI testing.

This app intentionally does not import from or call the production backend.
It returns predictable pseudo-responses with a small artificial delay so the
frontend can exercise loading and rendering states without invoking AI models.
"""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


RESPONSE_DELAY_SECONDS = 1

LOCAL_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

_SESSION_TURNS: dict[str, int] = {}


class FlexibleRequest(BaseModel):
    """Accept any frontend payload while deliberately ignoring its contents."""

    class Config:
        extra = "allow"


class SessionView(BaseModel):
    session_id: str = Field(default_factory=lambda: f"test-{uuid4()}")
    stage: str
    state: str
    cancelled: bool = False
    completed: bool = False


async def _simulate_loading() -> None:
    await asyncio.sleep(RESPONSE_DELAY_SECONDS)


def _session(
    stage: str,
    state: str,
    completed: bool = False,
    session_id: str | None = None,
) -> dict[str, Any]:
    return SessionView(
        session_id=session_id or f"test-{uuid4()}",
        stage=stage,
        state=state,
        completed=completed,
    ).dict()


def _turn_response(session_id: str, turn_count: int) -> dict[str, Any]:
    if turn_count == 1:
        return {
            "session": _session("coaching", "guiding", session_id=session_id),
            "coach_message": (
                "It sounds like the core tension is between protecting delivery "
                "quality and preserving trust with your team. What feels most "
                "difficult to say plainly right now?"
            ),
            "debug_message": "static_test_backend.user_message.coaching",
        }

    if turn_count == 2:
        synthesis_text = (
            "You are trying to decide how to reset expectations around a "
            "high-pressure deadline. The problem is not only the amount of work, "
            "but the risk that raising capacity limits could be interpreted as a "
            "lack of commitment. A useful next step is to make the trade-offs "
            "visible without making the conversation defensive."
        )
        return {
            "session": _session("synthesis", "validating", session_id=session_id),
            "synthesis": synthesis_text,
            "coach_message": synthesis_text,
            "debug_message": "static_test_backend.user_message.synthesis",
        }

    if turn_count == 3:
        return _pathways_response(session_id=session_id)

    return {
        "session": _session("closure", "completed", completed=True, session_id=session_id),
        "coach_message": (
            "You now have a clear synthesis and a set of practical pathways to "
            "compare. Choose the direction that gives you the cleanest next "
            "conversation, then keep the first step deliberately small."
        ),
        "debug_message": "static_test_backend.user_message.closure",
    }


def _pathways_response(session_id: str | None = None) -> dict[str, Any]:
    pathways_text = "\n\n".join(
        [
            (
                "## Reframe The Deadline Conversation\n"
                "Orientation: Treat the conversation as a shared prioritisation "
                "decision rather than a personal capacity confession.\n"
                "Conditions: Works best when your manager can trade scope, timing, "
                "or quality and you can bring concrete options."
            ),
            (
                "## Protect The Team Through Explicit Trade-Offs\n"
                "Orientation: Name the operational cost of the current plan and ask "
                "which constraint should move.\n"
                "Conditions: Useful when the team is already stretched and you need "
                "to prevent hidden overtime from becoming the default."
            ),
            (
                "## Start With A Small Boundary Experiment\n"
                "Orientation: Propose a short trial for clearer escalation rules, "
                "focus blocks, or reduced ad hoc work.\n"
                "Conditions: Best when a full reset would feel too abrupt but a "
                "limited test would be easy to accept."
            ),
        ]
    )

    return {
        "session": _session("pathways", "presenting", session_id=session_id),
        "pathways": [
            {
                "title": "Reframe The Deadline Conversation",
                "orientation": "Make prioritisation the subject of the discussion.",
                "conditions": "Use when scope, timing, or quality can still move.",
            },
            {
                "title": "Protect The Team Through Explicit Trade-Offs",
                "orientation": "Make the operational cost of the current plan visible.",
                "conditions": "Use when hidden overtime or quality risk is building.",
            },
            {
                "title": "Start With A Small Boundary Experiment",
                "orientation": "Try a limited reset before asking for a bigger change.",
                "conditions": "Use when a full boundary conversation feels too abrupt.",
            },
        ],
        "coach_message": pathways_text,
        "debug_message": "static_test_backend.pathways",
    }


app = FastAPI(title="Coach V3 Test Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "backend": "test"}


@app.get("/session_initialise")
async def session_initialise() -> dict[str, Any]:
    session_id = f"test-{uuid4()}"
    _SESSION_TURNS[session_id] = 0

    return _session("classification", "evaluating", session_id=session_id)


@app.post("/user_message")
async def user_message(payload: FlexibleRequest | None = Body(default=None)) -> dict[str, Any]:
    await _simulate_loading()
    session_id = None

    if payload is not None:
        session_id = getattr(payload, "session_id", None)

    if not session_id:
        session_id = f"test-{uuid4()}"

    next_turn = _SESSION_TURNS.get(session_id, 0) + 1
    _SESSION_TURNS[session_id] = next_turn

    return _turn_response(session_id=session_id, turn_count=next_turn)


@app.post("/problem")
async def problem(_: FlexibleRequest | None = Body(default=None)) -> dict[str, Any]:
    await _simulate_loading()
    problem_statement = (
        "I am balancing a demanding delivery deadline with a need to set clearer "
        "boundaries with my team, and I am unsure how to raise the issue without "
        "sounding uncommitted."
    )

    return {
        "session": _session("classification", "completed", completed=True),
        "problem": problem_statement,
        "coach_message": (
            "Thanks. The working problem statement is clear enough to begin: "
            f"{problem_statement}"
        ),
        "debug_message": "static_test_backend.problem",
    }


@app.post("/coach")
async def coach(_: FlexibleRequest | None = Body(default=None)) -> dict[str, Any]:
    await _simulate_loading()

    return {
        "session": _session("coaching", "guiding"),
        "coach_message": (
            "It sounds like the core tension is between protecting delivery quality "
            "and preserving trust with your team. What feels most difficult to say "
            "plainly right now?"
        ),
        "debug_message": "static_test_backend.coach",
    }


@app.post("/synthesis")
async def synthesis(_: FlexibleRequest | None = Body(default=None)) -> dict[str, Any]:
    await _simulate_loading()
    synthesis_text = (
        "You are trying to decide how to reset expectations around a high-pressure "
        "deadline. The problem is not only the amount of work, but the risk that "
        "raising capacity limits could be interpreted as a lack of commitment. A "
        "useful next step is to make the trade-offs visible without making the "
        "conversation defensive."
    )

    return {
        "session": _session("synthesis", "validating"),
        "synthesis": synthesis_text,
        "coach_message": synthesis_text,
        "debug_message": "static_test_backend.synthesis",
    }


@app.post("/pathways")
async def pathways(_: FlexibleRequest | None = Body(default=None)) -> dict[str, Any]:
    await _simulate_loading()
    return _pathways_response()
