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

from fastapi import FastAPI, HTTPException

from backend.controller import get_debug, handle_user_msg, init_session
from backend.models import DebugReply, SessionView, UserMsg, UserMsgReply


app = FastAPI(title="Coach V3 API")


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
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return UserMsgReply(
        session=_build_session_view(session),
        coach_message=session.coach_message,
    )


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
