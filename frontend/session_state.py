"""Pure frontend session-state helpers for the Streamlit migration path."""

from __future__ import annotations

from typing import Any, Mapping

from session_flow import map_backend_to_screen


MISSING_SESSION_NOTICE = (
    "Your previous session is no longer available, likely because the backend "
    "restarted or was redeployed. Please start a new session."
)

_VERSION_COUNTER_KEYS = (
    "problem_input_version",
    "coaching_input_version",
    "synthesis_feedback_version",
    "pathways_selection_version",
)


def default_frontend_state() -> dict[str, Any]:
    """Return the default frontend session-state values."""
    return {
        "ui_screen": "welcome",
        "session_id": None,
        "session_view": None,
        "coach_message": "",
        "cached_pathways_message": "",
        "debug_history": [],
        "latest_debug": None,
        "latest_debug_fingerprint": None,
        "frontend_error": None,
        "frontend_notice": None,
        "awaiting_pathways_after_refinement": False,
        "problem_input_version": 0,
        "coaching_input_version": 0,
        "synthesis_feedback_version": 0,
        "pathways_selection_version": 0,
    }


def build_cached_pathways_message(
    session: Mapping[str, Any],
    coach_message: str,
    current_cached_pathways_message: str = "",
) -> str:
    """Return the cached pathways message after applying the current backend state."""
    if session.get("stage") == "pathways" and coach_message:
        return coach_message
    return current_cached_pathways_message


def build_backend_turn_state_update(
    data: dict[str, Any],
    current_cached_pathways_message: str = "",
) -> dict[str, Any]:
    """Compute the frontend state changes for one successful backend turn."""
    session = data.get("session", {})
    coach_message = data.get("coach_message") or ""
    return {
        "session_view": session,
        "coach_message": coach_message,
        "ui_screen": map_backend_to_screen(session),
        "cached_pathways_message": build_cached_pathways_message(
            session,
            coach_message,
            current_cached_pathways_message=current_cached_pathways_message,
        ),
    }


def build_missing_session_reset_state(
    current_state: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the frontend state reset used when the backend has lost the session."""
    reset_state = {
        "session_id": None,
        "session_view": None,
        "coach_message": "",
        "cached_pathways_message": "",
        "debug_history": [],
        "latest_debug": None,
        "latest_debug_fingerprint": None,
        "awaiting_pathways_after_refinement": False,
        "ui_screen": "intro",
        "frontend_error": None,
        "frontend_notice": MISSING_SESSION_NOTICE,
    }

    for key in _VERSION_COUNTER_KEYS:
        reset_state[key] = int(current_state.get(key, 0) or 0) + 1

    return reset_state
