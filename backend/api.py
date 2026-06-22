"""
FastAPI entrypoints for Coach V3.

This module defines the HTTP boundary for the frontend and translates between:
- API-facing models
- plain internal controller function calls

Design rule for this POC:
- keep internal calls simple
- keep explicit models only at the HTTP boundary or where multiple fields are
  returned together
"""

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend import telemetry
from backend.admin.telemetry_export_routes import router as telemetry_export_router
from backend.controller import get_debug, handle_user_msg, init_session
from backend.feedback import (
    FeedbackSubmission,
    FeedbackValidationError,
    get_active_feedback_form,
    store_feedback_submission,
)
from backend.models import (
    ClientTelemetryEvent,
    DebugReply,
    SessionView,
    UserMsg,
    UserMsgReply,
)


LOCAL_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def _resolve_cors_origins() -> list[str]:
    configured_origins = [
        origin.strip()
        for origin in os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
        if origin.strip()
    ]

    return list(dict.fromkeys([*LOCAL_CORS_ORIGINS, *configured_origins]))


app = FastAPI(title="Coach V3 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_resolve_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(telemetry_export_router)


# ============================================================================
# Mapping helpers
# ============================================================================

def _build_session_view(session) -> SessionView:
    """Convert the internal Session model into the reduced API-safe session view."""
    return SessionView(
        session_id=session.session_id,
        stage=session.stage,
        state=session.state,
        cancelled=session.cancelled,
        completed=session.completed,
    )


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/health")
def health() -> dict[str, str]:
    """Simple health endpoint for local and remote deployment checks."""
    return {"status": "ok"}


@app.get("/session_initialise", response_model=SessionView)
def session_initialise() -> SessionView:
    """
    Create and return a new session view.

    Only the minimum useful information is returned at initialization.
    """
    session = init_session()
    return _build_session_view(session)


@app.post("/user_message", response_model=UserMsgReply)
def user_message(user_msg: UserMsg) -> UserMsgReply:
    """
    Handle a user turn for an existing session.

    The controller returns the full internal Session; the API maps that to the
    reduced public contract.
    """
    try:
        session = handle_user_msg(
            session_id=user_msg.session_id,
            user_message=user_msg.user_message,
            client_context=user_msg.client_context,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return UserMsgReply(
        session=_build_session_view(session),
        coach_message=session.coach_message,
    )


@app.get("/coach/v2/feedback-form")
def feedback_form(session_id: str) -> dict:
    """
    Return the active feedback form for a session.

    Feedback config failures are handled inside the feedback subsystem and
    return show_feedback=false rather than breaking the session flow.
    """
    try:
        session = get_debug(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return get_active_feedback_form(session).model_dump(exclude_none=True)


@app.post("/coach/v2/feedback")
def submit_feedback(submission: FeedbackSubmission) -> dict[str, str]:
    """Validate and store a configurable feedback submission."""
    try:
        store_feedback_submission(submission)
    except FeedbackValidationError as exc:
        message = str(exc)
        status_code = 404 if message == "session_not_found" else 422
        raise HTTPException(status_code=status_code, detail=message) from exc

    return {"status": "ok"}


@app.post("/telemetry/session_event")
def session_telemetry_event(event: ClientTelemetryEvent) -> dict[str, str]:
    """
    Record a telemetry-only client event for an existing session.

    This endpoint is deliberately outside the coaching control path. It does
    not mutate session state and telemetry failures are swallowed by the
    telemetry service.
    """
    try:
        session = get_debug(event.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    session_status = None
    if session.completed:
        session_status = "completed"
    elif session.cancelled:
        session_status = "cancelled"

    if event.event == "pdf_downloaded":
        telemetry.record_session_updated(
            session_id=session.session_id,
            stage=session.stage,
            state=session.state,
            turns_count=session.turn_count,
            pdf_downloaded=True,
            status=session_status,
            session_label=session.session_label,
            pilot_id=session.pilot_id,
        )
        return {"status": "ok"}

    # Legacy Streamlit compatibility path. New React feedback uses
    # /coach/v2/feedback and stores YAML-backed response ids.
    telemetry.record_feedback_submitted(
        session_id=session.session_id,
        feedback_pack_id="legacy_fixed_feedback",
        feedback_responses={
            "answer_1": event.answer_1,
            "answer_2": event.answer_2,
            "dropdown_values": event.dropdown_values or [],
        },
        pilot_id=session.pilot_id,
    )
    return {"status": "ok"}


@app.get("/debug_trace/{session_id}", response_model=DebugReply)
def debug_trace(session_id: str) -> DebugReply:
    """
    Return current debug information for a given session.
    """
    try:
        session = get_debug(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return DebugReply(
        session=_build_session_view(session),
        user_message=session.user_message,
        evaluation_message=session.evaluation_message,
        coach_message=session.coach_message,
        debug_message=session.debug_message,
        turn_count=session.turn_count,
        stage_turn_count=session.stage_turn_count,
        stage_context=session.stage_context,
    )
