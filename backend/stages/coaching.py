"""
Coaching stage module for Coach V3.

Purpose
-------
This module owns the local FSM and stage-specific behaviour for the Coaching
macro-stage.

Current scaffold status
-----------------------
This file intentionally implements only a minimal placeholder handler.
It does not yet contain:
- local state transition logic
- calls into engine.py
- prompt construction
- stage-specific validation
- macro-stage advancement logic

Design rule
-----------
The controller owns macro-stage orchestration and passes the in-memory Session
directly to this stage module. This stage module updates the session locally
and returns a StageReply only because that reply may also carry an optional
next_stage request.
"""

from backend.models import Session, StageReply


def handle_stage(session: Session) -> StageReply:
    """
    Handle one turn for the Coaching stage.

    Input
    -----
    session:
        The current in-memory session already loaded by controller.py.

    Output
    ------
    StageReply:
        The updated session, plus an optional next_stage when this stage later
        becomes able to request a macro-stage transition.

    Notes
    -----
    For now this is a no-op placeholder that only records a stage-specific
    debug message.
    """
    session.debug_message = "Coaching stage handler invoked."

    return StageReply(session=session)
