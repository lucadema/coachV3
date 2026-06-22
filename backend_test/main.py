"""
Static FastAPI backend for local React UI testing.

This app intentionally does not import from or call the production backend.
It returns predictable pseudo-responses with a small artificial delay so the
frontend can exercise loading and rendering states without invoking AI models.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

import yaml
from dotenv import load_dotenv
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from backend import telemetry


RESPONSE_DELAY_SECONDS = 1

LOCAL_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.1.162:5173",
]

FEEDBACK_CONFIG_PATH = Path(__file__).resolve().parent.parent / "backend" / "config" / "feedback_forms.yaml"
XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
SELECT_QUESTION_TYPES = {"single_select", "multi_select"}
ACCESS_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{20,256}$")
SUPPORTED_QUESTION_TYPES = {
    "boolean",
    "likert_1_5",
    "single_select",
    "multi_select",
    "short_text",
    "free_text",
}
PILOT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")

_SESSIONS: dict[str, dict[str, Any]] = {}
logger = logging.getLogger(__name__)


def _load_env() -> None:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)


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


class UserMsg(BaseModel):
    session_id: str
    user_message: str
    client_context: dict[str, Any] | None = None


class ClientTelemetryEvent(BaseModel):
    session_id: str
    event: Literal["pdf_downloaded", "feedback_submitted"]
    answer_1: bool | None = None
    answer_2: bool | None = None
    dropdown_values: list[str] | None = None
    payload: dict[str, Any] | None = None


class FeedbackSubmission(BaseModel):
    session_id: str
    feedback_pack_id: str
    responses: dict[str, Any] = Field(default_factory=dict)


async def _simulate_loading() -> None:
    await asyncio.sleep(RESPONSE_DELAY_SECONDS)


def _store_session(session_view: dict[str, Any], **updates: Any) -> dict[str, Any]:
    session_id = session_view["session_id"]
    current = _SESSIONS.get(
        session_id,
        {
            "session": session_view,
            "user_message": None,
            "evaluation_message": None,
            "coach_message": None,
            "debug_message": None,
            "turn_count": 0,
            "stage_turn_count": 0,
            "stage_context": {},
            "pilot_id": None,
            "telemetry_started": False,
            "telemetry_closed": False,
            "feedback_pack_id": None,
            "feedback_responses": None,
        },
    )
    current["session"] = session_view
    current.update(updates)
    _SESSIONS[session_id] = current
    return current


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


def _turn_response(session_id: str, turn_count: int, user_message_text: str) -> dict[str, Any]:
    if turn_count == 1:
        response = {
            "session": _session("coaching", "guiding", session_id=session_id),
            "coach_message": (
                "It sounds like the core tension is between protecting delivery "
                "quality and preserving trust with your team. What feels most "
                "difficult to say plainly right now?"
            ),
            "debug_message": "static_test_backend.user_message.coaching",
        }
        _store_turn(session_id, response, turn_count, user_message_text)
        return response

    if turn_count == 2:
        synthesis_text = (
            "You are trying to decide how to reset expectations around a "
            "high-pressure deadline. The problem is not only the amount of work, "
            "but the risk that raising capacity limits could be interpreted as a "
            "lack of commitment. A useful next step is to make the trade-offs "
            "visible without making the conversation defensive."
        )
        response = {
            "session": _session("synthesis", "validating", session_id=session_id),
            "synthesis": synthesis_text,
            "coach_message": synthesis_text,
            "debug_message": "static_test_backend.user_message.synthesis",
        }
        _store_turn(session_id, response, turn_count, user_message_text)
        return response

    if turn_count == 3:
        response = _pathways_response(session_id=session_id)
        _store_turn(session_id, response, turn_count, user_message_text)
        return response

    response = {
        "session": _session("closure", "completed", completed=True, session_id=session_id),
        "coach_message": (
            "You now have a clear synthesis and a set of practical pathways to "
            "compare. Choose the direction that gives you the cleanest next "
            "conversation, then keep the first step deliberately small."
        ),
        "debug_message": "static_test_backend.user_message.closure",
    }
    _store_turn(session_id, response, turn_count, user_message_text)
    return response


def _store_turn(
    session_id: str,
    response: dict[str, Any],
    turn_count: int,
    user_message_text: str,
) -> None:
    _store_session(
        response["session"],
        user_message=user_message_text,
        evaluation_message=(
            "Static test evaluation: user input accepted and routed through the "
            "mock stage sequence."
        ),
        coach_message=response.get("coach_message"),
        debug_message=response.get("debug_message"),
        turn_count=turn_count,
        stage_turn_count=turn_count,
    )


def _session_status(session: dict[str, Any]) -> str | None:
    session_view = session.get("session") or {}
    if session_view.get("completed"):
        return "completed"
    if session_view.get("cancelled"):
        return "cancelled"
    return None


def _telemetry_generation_flags(session: dict[str, Any]) -> tuple[bool | None, bool | None]:
    session_view = session.get("session") or {}
    stage = session_view.get("stage")
    state = session_view.get("state")

    synthesis_generated = None
    pathways_generated = None

    if stage in {"synthesis", "pathways", "closure"}:
        synthesis_generated = True
    if stage in {"pathways", "closure"}:
        pathways_generated = True
    if stage == "synthesis" and state == "validating":
        synthesis_generated = True
    if stage == "pathways" and state == "presenting":
        pathways_generated = True

    return synthesis_generated, pathways_generated


def _record_test_session_started(session_id: str, session: dict[str, Any]) -> None:
    if session.get("telemetry_started"):
        return

    _load_env()
    session_view = session.get("session") or {}
    telemetry.record_session_started(
        session_id=session_id,
        stage=session_view.get("stage"),
        state=session_view.get("state"),
        turns_count=session.get("turn_count", 0),
        pilot_id=session.get("pilot_id"),
    )
    session["telemetry_started"] = True


def _record_test_session_updated(session_id: str, session: dict[str, Any]) -> None:
    _load_env()
    session_view = session.get("session") or {}
    status = _session_status(session)
    synthesis_generated, pathways_generated = _telemetry_generation_flags(session)
    telemetry.record_session_updated(
        session_id=session_id,
        stage=session_view.get("stage"),
        state=session_view.get("state"),
        turns_count=session.get("turn_count", 0),
        synthesis_generated=synthesis_generated,
        pathways_generated=pathways_generated,
        pdf_downloaded=None,
        status=status,
        pilot_id=session.get("pilot_id"),
    )


def _record_test_session_closed(session_id: str, session: dict[str, Any]) -> None:
    status = _session_status(session)
    if status is None or session.get("telemetry_closed"):
        return

    _load_env()
    session_view = session.get("session") or {}
    telemetry.record_session_closed(
        session_id=session_id,
        stage=session_view.get("stage"),
        state=session_view.get("state"),
        turns_count=session.get("turn_count", 0),
        status=status,
        pilot_id=session.get("pilot_id"),
    )
    session["telemetry_closed"] = True


def _extract_pilot_id(client_context: Any) -> str | None:
    """Test-backend hook for simulating a production-resolved pilot context."""
    if not isinstance(client_context, dict):
        return None

    value = client_context.get("pilot_id") or client_context.get("pilotId")
    if not isinstance(value, str):
        return None

    stripped = value.strip()
    if not PILOT_ID_PATTERN.fullmatch(stripped):
        return None
    return stripped


def _extract_access_token(client_context: Any) -> str | None:
    if not isinstance(client_context, dict):
        return None

    value = (
        client_context.get("access_token")
        or client_context.get("accessToken")
        or client_context.get("token")
    )
    if not isinstance(value, str):
        return None

    stripped = value.strip()
    if not ACCESS_TOKEN_PATTERN.fullmatch(stripped):
        return None
    return stripped


def _hash_access_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


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
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+|192\.168\.\d+\.\d+):\d+$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/session_initialise")
async def session_initialise() -> dict[str, Any]:
    session_id = f"test-{uuid4()}"
    session_view = _session("classification", "evaluating", session_id=session_id)
    _store_session(
        session_view,
        debug_message="static_test_backend.session_initialise",
        turn_count=0,
        stage_turn_count=0,
    )

    return session_view


@app.post("/user_message")
async def user_message(payload: UserMsg) -> dict[str, Any]:
    await _simulate_loading()
    session = _SESSIONS.get(payload.session_id)

    if session is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {payload.session_id}")

    incoming_access_token = _extract_access_token(payload.client_context)
    if incoming_access_token:
        pilot_id = _resolve_glimpse_pilot_id(incoming_access_token)
        if not pilot_id:
            raise HTTPException(
                status_code=403,
                detail="Invalid or inactive Glimpse participant access token.",
            )
        if session.get("pilot_id") is not None and session.get("pilot_id") != pilot_id:
            raise HTTPException(
                status_code=403,
                detail="Glimpse participant token does not match this session.",
            )
        session["pilot_id"] = pilot_id

    incoming_pilot_id = _extract_pilot_id(payload.client_context)
    if incoming_pilot_id and session.get("pilot_id") is None:
        session["pilot_id"] = incoming_pilot_id

    next_turn = int(session.get("turn_count") or 0) + 1
    _record_test_session_started(payload.session_id, session)

    response = _turn_response(
        session_id=payload.session_id,
        turn_count=next_turn,
        user_message_text=payload.user_message,
    )
    updated_session = _SESSIONS[payload.session_id]
    _record_test_session_updated(payload.session_id, updated_session)
    _record_test_session_closed(payload.session_id, updated_session)
    return response


@app.get("/coach/v2/feedback-form")
async def feedback_form(session_id: str) -> dict[str, Any]:
    session = _SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    return _feedback_form_response(session)


@app.post("/coach/v2/feedback")
async def submit_feedback(submission: FeedbackSubmission) -> dict[str, str]:
    session = _SESSIONS.get(submission.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session_not_found")

    _validate_feedback_submission(submission)
    session["feedback_pack_id"] = submission.feedback_pack_id
    session["feedback_responses"] = submission.responses
    _load_env()
    telemetry.record_feedback_submitted(
        session_id=submission.session_id,
        feedback_pack_id=submission.feedback_pack_id,
        feedback_responses=submission.responses,
        pilot_id=session.get("pilot_id"),
    )
    return {"status": "ok"}


@app.post("/telemetry/session_event")
async def session_telemetry_event(event: ClientTelemetryEvent) -> dict[str, str]:
    session = _SESSIONS.get(event.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {event.session_id}")

    session_view = session.get("session") or {}
    if event.event == "pdf_downloaded":
        _load_env()
        telemetry.record_session_updated(
            session_id=event.session_id,
            stage=session_view.get("stage"),
            state=session_view.get("state"),
            turns_count=session.get("turn_count", 0),
            pdf_downloaded=True,
            status=_session_status(session),
            pilot_id=session.get("pilot_id"),
        )
        return {"status": "ok"}

    _load_env()
    telemetry.record_feedback_submitted(
        session_id=event.session_id,
        feedback_pack_id="legacy_fixed_feedback",
        feedback_responses={
            "answer_1": event.answer_1,
            "answer_2": event.answer_2,
            "dropdown_values": event.dropdown_values or [],
        },
        pilot_id=session.get("pilot_id"),
    )
    return {"status": "ok"}


@app.get("/admin/telemetry/export.xlsx")
async def export_telemetry_workbook(
    token: str | None = Query(default=None),
    limit: int = Query(default=5_000, ge=1, le=20_000),
) -> Response:
    expected_token = os.getenv("TELEMETRY_EXPORT_TOKEN")
    if not expected_token:
        raise HTTPException(status_code=503, detail="Telemetry export is not configured.")

    if token is None or token != expected_token:
        raise HTTPException(status_code=403, detail="Forbidden.")

    content = (
        "Static test backend telemetry export\n"
        f"Generated: {datetime.now(timezone.utc).isoformat()}\n"
        f"Limit: {limit}\n"
    ).encode("utf-8")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    headers = {
        "Content-Disposition": (
            f'attachment; filename="aether-glimpse-telemetry-test-{timestamp}.xlsx"'
        )
    }
    return Response(content=content, media_type=XLSX_CONTENT_TYPE, headers=headers)


@app.get("/debug_trace/{session_id}")
async def debug_trace(session_id: str) -> dict[str, Any]:
    session = _SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    return {
        "session": session["session"],
        "user_message": session.get("user_message"),
        "evaluation_message": session.get("evaluation_message"),
        "coach_message": session.get("coach_message"),
        "debug_message": session.get("debug_message"),
        "turn_count": session.get("turn_count", 0),
        "stage_turn_count": session.get("stage_turn_count", 0),
        "stage_context": session.get("stage_context", {}),
    }


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


def _feedback_form_response(session: dict[str, Any]) -> dict[str, Any]:
    config = _load_feedback_config()
    if config is None:
        return {"show_feedback": False, "questions": []}

    pack_id = _select_feedback_pack_id(session, config)
    pack = config["feedback_packs"][pack_id]
    return {
        "show_feedback": True,
        "feedback_pack_id": pack_id,
        "title": pack.get("title"),
        "survey_query": pack.get("survey_query"),
        "description": pack.get("description"),
        "questions": pack.get("questions", []),
    }


def _select_feedback_pack_id(session: dict[str, Any], config: dict[str, Any]) -> str:
    default_pack_id = config["default_feedback_pack_id"]
    pilot_id = _clean_optional_string(session.get("pilot_id"))
    if not pilot_id:
        return default_pack_id

    pilot_pack_id = _get_pilot_feedback_pack_id(pilot_id)
    if not pilot_pack_id:
        return default_pack_id

    if pilot_pack_id not in config["feedback_packs"]:
        logger.warning(
            "Test backend falling back to default feedback pack because pilot "
            "pack is unknown pilot_id=%s feedback_pack_id=%s",
            pilot_id,
            pilot_pack_id,
        )
        return default_pack_id

    return pilot_pack_id


def _validate_feedback_submission(submission: FeedbackSubmission) -> None:
    pack = _get_feedback_pack(submission.feedback_pack_id)
    if pack is None:
        raise HTTPException(status_code=422, detail="unknown_feedback_pack_id")

    questions = pack.get("questions", [])
    question_ids = {question["id"] for question in questions}
    unknown_question_ids = sorted(set(submission.responses) - question_ids)
    if unknown_question_ids:
        raise HTTPException(
            status_code=422,
            detail=f"unknown_feedback_question_id:{unknown_question_ids[0]}",
        )

    questions_by_id = {question["id"]: question for question in questions}
    for question_id, value in submission.responses.items():
        _validate_feedback_value(questions_by_id[question_id], value)


def _load_feedback_config() -> dict[str, Any] | None:
    try:
        raw_config = yaml.safe_load(FEEDBACK_CONFIG_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, yaml.YAMLError):
        return None

    if not isinstance(raw_config, dict):
        return None

    feedback_packs = raw_config.get("feedback_packs")
    default_pack_id = raw_config.get("default_feedback_pack_id")
    if not isinstance(feedback_packs, dict) or not isinstance(default_pack_id, str):
        return None

    if default_pack_id not in feedback_packs:
        return None

    for pack in feedback_packs.values():
        if not _is_valid_feedback_pack(pack):
            return None

    return raw_config


def _database_url() -> str | None:
    _load_env()
    return os.getenv("ADMIN_DATABASE_URL") or os.getenv("TELEMETRY_DATABASE_URL")


def _clean_optional_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _get_pilot_feedback_pack_id(pilot_id: str) -> str | None:
    database_url = _database_url()
    if not database_url:
        return None

    connection = None
    try:
        import psycopg
        from psycopg.rows import dict_row

        connection = psycopg.connect(
            database_url,
            connect_timeout=2,
            options="-c statement_timeout=2000",
            row_factory=dict_row,
        )
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT feedback_pack_id
                FROM admin_pilots
                WHERE id = %s
                LIMIT 1
                """,
                (pilot_id,),
            )
            row = cursor.fetchone()
            connection.commit()
            if row is None:
                return None

            return _clean_optional_string(row.get("feedback_pack_id"))
    except Exception as exc:
        if connection is not None:
            try:
                connection.rollback()
            except Exception:
                pass
        logger.warning(
            "Test backend pilot feedback pack lookup failed "
            "pilot_id=%s error_type=%s error=%s",
            pilot_id,
            type(exc).__name__,
            str(exc)[:300],
        )
        return None
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass


def _resolve_glimpse_pilot_id(access_token: str) -> str | None:
    database_url = _database_url()
    if not database_url:
        logger.warning("Test backend pilot token validation requested without a database URL.")
        return None

    connection = None
    try:
        import psycopg
        from psycopg.rows import dict_row

        connection = psycopg.connect(
            database_url,
            connect_timeout=2,
            options="-c statement_timeout=2000",
            row_factory=dict_row,
        )
        token_hash = _hash_access_token(access_token)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, pilot_id
                FROM admin_access_tokens
                WHERE token_hash = %s
                  AND token_type = 'glimpse_app'
                  AND status = 'active'
                  AND (expires_at IS NULL OR expires_at > NOW())
                LIMIT 1
                """,
                (token_hash,),
            )
            row = cursor.fetchone()
            if row is None:
                connection.commit()
                return None

            cursor.execute(
                """
                UPDATE admin_access_tokens
                SET last_used_at = NOW(), updated_at = NOW()
                WHERE id = %s
                """,
                (row["id"],),
            )
            connection.commit()
            return str(row["pilot_id"])
    except Exception as exc:
        if connection is not None:
            try:
                connection.rollback()
            except Exception:
                pass
        logger.warning(
            "Test backend pilot token validation failed error_type=%s error=%s",
            type(exc).__name__,
            str(exc)[:300],
        )
        return None
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass


def _get_default_feedback_pack() -> tuple[str, dict[str, Any]] | None:
    config = _load_feedback_config()
    if config is None:
        return None

    pack_id = config["default_feedback_pack_id"]
    return pack_id, config["feedback_packs"][pack_id]


def _get_feedback_pack(pack_id: str) -> dict[str, Any] | None:
    config = _load_feedback_config()
    if config is None:
        return None

    pack = config["feedback_packs"].get(pack_id)
    if not isinstance(pack, dict):
        return None
    return pack


def _is_valid_feedback_pack(pack: Any) -> bool:
    if not isinstance(pack, dict):
        return False

    questions = pack.get("questions")
    if not isinstance(pack.get("title"), str) or not isinstance(pack.get("survey_query"), str):
        return False
    if not isinstance(questions, list):
        return False

    question_ids: set[str] = set()
    for question in questions:
        if not _is_valid_feedback_question(question):
            return False
        question_id = question["id"]
        if question_id in question_ids:
            return False
        question_ids.add(question_id)

    return True


def _is_valid_feedback_question(question: Any) -> bool:
    if not isinstance(question, dict):
        return False

    question_id = question.get("id")
    question_type = question.get("type")
    text = question.get("text")
    required = question.get("required", False)
    options = question.get("options", [])

    if not isinstance(question_id, str) or not isinstance(question_type, str):
        return False
    if question_type not in SUPPORTED_QUESTION_TYPES or not isinstance(text, str):
        return False
    if not isinstance(required, bool) or not isinstance(options, list):
        return False
    if question_type in SELECT_QUESTION_TYPES and not options:
        return False
    if question_type not in SELECT_QUESTION_TYPES and options:
        return False

    option_values: set[str] = set()
    for option in options:
        if not _is_valid_feedback_option(option):
            return False
        option_value = option["value"]
        if option_value in option_values:
            return False
        option_values.add(option_value)

    return True


def _is_valid_feedback_option(option: Any) -> bool:
    if not isinstance(option, dict):
        return False

    if not isinstance(option.get("value"), str):
        return False
    if not isinstance(option.get("label"), str):
        return False

    numeric_value = option.get("numeric_value")
    return numeric_value is None or isinstance(numeric_value, int | float)


def _validate_feedback_value(question: dict[str, Any], value: Any) -> None:
    question_id = question["id"]
    question_type = question["type"]

    if value is None or value == "" or value == []:
        if question.get("required", False):
            raise HTTPException(
                status_code=422,
                detail=f"required_feedback_question_missing:{question_id}",
            )
        return

    if question_type == "boolean" and not isinstance(value, bool):
        raise HTTPException(status_code=422, detail=f"invalid_boolean_feedback:{question_id}")

    if question_type == "likert_1_5":
        if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > 5:
            raise HTTPException(status_code=422, detail=f"invalid_likert_feedback:{question_id}")

    if question_type == "single_select":
        option_values = {option["value"] for option in question.get("options", [])}
        if not isinstance(value, str):
            raise HTTPException(
                status_code=422,
                detail=f"invalid_single_select_feedback:{question_id}",
            )
        if value not in option_values:
            raise HTTPException(
                status_code=422,
                detail=f"invalid_single_select_option:{question_id}",
            )

    if question_type == "multi_select":
        option_values = {option["value"] for option in question.get("options", [])}
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise HTTPException(
                status_code=422,
                detail=f"invalid_multi_select_feedback:{question_id}",
            )
        invalid_values = [item for item in value if item not in option_values]
        if invalid_values:
            raise HTTPException(
                status_code=422,
                detail=f"invalid_multi_select_option:{question_id}",
            )

    if question_type in {"short_text", "free_text"} and not isinstance(value, str):
        raise HTTPException(status_code=422, detail=f"invalid_text_feedback:{question_id}")


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
