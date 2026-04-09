import json
import os
import html
import re
from pathlib import Path
from typing import Any

import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)


LOCAL_API_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT_SECONDS = 20
USER_MESSAGE_TIMEOUT_SECONDS = 120


def _resolve_api_url() -> str:
    """Prefer Streamlit secrets, then environment variables, then localhost."""
    try:
        secrets_url = st.secrets.get("API_BASE_URL")
    except Exception:
        secrets_url = None

    return secrets_url or os.getenv("API_BASE_URL", LOCAL_API_URL)


def _debug_enabled() -> bool:
    """Show the debug panel only when DEBUG is explicitly TRUE."""
    try:
        debug_value = st.secrets.get("DEBUG")
    except Exception:
        debug_value = None

    if debug_value is None:
        debug_value = os.getenv("DEBUG", "")

    return str(debug_value).strip().upper() == "TRUE"


API_URL = _resolve_api_url()

st.set_page_config(layout="wide", page_title="Aether")


# ------------------------------------------------
# Styling
# ------------------------------------------------
st.markdown(
    """
<style>
.block-container {
    max-width: 760px;
    margin: auto;
    padding-top: 2.5rem;
}

h1, h2, h3 {
    text-align: center;
}

[data-testid="stSidebar"] {
    min-width: 380px;
    max-width: 380px;
}

.debug-kicker {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #5f6b7a;
}

.debug-card {
    border: 1px solid #d7deea;
    border-radius: 12px;
    padding: 0.85rem 0.95rem;
    background: linear-gradient(180deg, #fbfcfe 0%, #f4f7fb 100%);
    margin-bottom: 0.8rem;
}

.pathways-box {
    border: 1px solid #d7deea;
    border-radius: 14px;
    background: #f8fbff;
    padding: 1rem 1rem 0.2rem 1rem;
}

.message-card {
    border: 1px solid #d7deea;
    border-radius: 14px;
    padding: 1rem 1.05rem;
    background: #ffffff;
    margin-bottom: 1rem;
    line-height: 1.55;
    white-space: pre-wrap;
}

.coach-card {
    border-left: 5px solid #7ed957;
    background: linear-gradient(180deg, #fbfff8 0%, #f5ffef 100%);
}

.text-panel {
    border: 1px solid #dde5f0;
    border-radius: 12px;
    background: #ffffff;
    padding: 0.9rem 1rem;
    line-height: 1.55;
    white-space: pre-wrap;
}

.text-preview {
    background: #f9fbfe;
}

.pending-card {
    border: 1px solid #d9dee7;
    border-radius: 14px;
    background: #f5f7fa;
    color: #5a6473;
    padding: 0.95rem 1rem;
    margin: 0.75rem 0 1rem 0;
}

.pending-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-weight: 600;
    margin-bottom: 0.55rem;
}

.pending-dot {
    width: 10px;
    height: 10px;
    border-radius: 999px;
    background: #7ed957;
    animation: pending-pulse 1.1s ease-in-out infinite;
}

@keyframes pending-pulse {
    0% { opacity: 0.35; transform: scale(0.9); }
    50% { opacity: 1; transform: scale(1.1); }
    100% { opacity: 0.35; transform: scale(0.9); }
}

.stButton > button {
    width: 100%;
    background: linear-gradient(90deg, #7ed957, #c1fba4);
    color: #15220d;
    border-radius: 10px;
    border: 1px solid #b7d7a5;
    font-weight: 600;
}

.stTextArea textarea, .stTextInput input {
    border-radius: 10px;
}
</style>
""",
    unsafe_allow_html=True,
)


# ------------------------------------------------
# Session state
# ------------------------------------------------
DEFAULTS = {
    "ui_screen": "welcome",
    "session_id": None,
    "session_view": None,
    "coach_message": "",
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

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ------------------------------------------------
# API
# ------------------------------------------------
def _request_json(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
) -> dict[str, Any] | None:
    """Call the backend and return parsed JSON or surface a readable error."""
    try:
        if method == "GET":
            response = requests.get(f"{API_URL}{path}", timeout=timeout_seconds)
        else:
            response = requests.post(
                f"{API_URL}{path}",
                json=payload,
                timeout=timeout_seconds,
            )
        if response.status_code == 404 and path.startswith(("/user_message", "/debug_trace/")):
            _reset_missing_session()
            st.rerun()
        response.raise_for_status()
        st.session_state.frontend_error = None
        st.session_state.frontend_notice = None
        return response.json()
    except requests.RequestException as exc:
        st.session_state.frontend_error = str(exc)
        return None


def _reset_missing_session() -> None:
    """Reset local UI state when the backend no longer knows the session id."""
    st.session_state.session_id = None
    st.session_state.session_view = None
    st.session_state.coach_message = ""
    st.session_state.debug_history = []
    st.session_state.latest_debug = None
    st.session_state.latest_debug_fingerprint = None
    st.session_state.awaiting_pathways_after_refinement = False
    st.session_state.ui_screen = "intro"
    st.session_state.problem_input_version += 1
    st.session_state.coaching_input_version += 1
    st.session_state.synthesis_feedback_version += 1
    st.session_state.pathways_selection_version += 1
    st.session_state.frontend_error = None
    st.session_state.frontend_notice = (
        "Your previous session is no longer available, likely because the backend "
        "restarted or was redeployed. Please start a new session."
    )


def api_init_session() -> dict[str, Any] | None:
    """Create a backend session."""
    return _request_json("GET", "/session_initialise")


def api_send_message(message: str) -> dict[str, Any] | None:
    """Send one user turn to the backend."""
    return _request_json(
        "POST",
        "/user_message",
        {
            "session_id": st.session_state.session_id,
            "user_message": message,
        },
        timeout_seconds=USER_MESSAGE_TIMEOUT_SECONDS,
    )


def api_get_debug_trace() -> dict[str, Any] | None:
    """Retrieve the current session debug payload."""
    if not st.session_state.session_id:
        return None
    return _request_json("GET", f"/debug_trace/{st.session_state.session_id}")


# ------------------------------------------------
# Debug helpers
# ------------------------------------------------
def _render_text_panel(
    label: str,
    value: str | None,
    *,
    preview_chars: int = 240,
    expanded: bool = False,
    empty_caption: str | None = None,
) -> None:
    """Render readable text with a preview plus an expandable full view."""
    if not value:
        st.caption(empty_caption or f"{label}: none")
        return

    text = str(value).strip()
    if not text:
        st.caption(empty_caption or f"{label}: none")
        return

    preview_source = " ".join(text.split())
    preview = preview_source if len(preview_source) <= preview_chars else f"{preview_source[:preview_chars]}..."

    st.markdown(f"**{label}**")
    st.markdown(
        (
            '<div class="text-panel text-preview">'
            f"{html.escape(preview).replace(chr(10), '<br>')}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    if len(preview_source) > preview_chars or "\n" in text:
        with st.expander(f"Expand {label.lower()}", expanded=expanded):
            st.markdown(
                (
                    '<div class="text-panel">'
                    f"{html.escape(text).replace(chr(10), '<br>')}"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )


def _capture_debug_snapshot(label: str, *, force_append: bool = False) -> dict[str, Any] | None:
    """Fetch the latest debug payload and append it to the local debug history."""
    payload = api_get_debug_trace()
    if payload is None:
        return None

    snapshot = {
        "label": label,
        "session": payload.get("session", {}),
        "user_message": payload.get("user_message"),
        "evaluation_message": payload.get("evaluation_message"),
        "coach_message": payload.get("coach_message"),
        "debug_message": payload.get("debug_message"),
        "turn_count": payload.get("turn_count", 0),
        "stage_turn_count": payload.get("stage_turn_count", 0),
        "stage_context": payload.get("stage_context") or {},
    }

    fingerprint_source = {
        key: value
        for key, value in snapshot.items()
        if key != "label"
    }
    fingerprint = json.dumps(fingerprint_source, sort_keys=True, default=str)

    st.session_state.latest_debug = snapshot

    if force_append or st.session_state.latest_debug_fingerprint != fingerprint:
        st.session_state.debug_history.append(snapshot)
        st.session_state.latest_debug_fingerprint = fingerprint

    return snapshot


def _parse_debug_message(debug_message: str | None) -> dict[str, Any]:
    """Split the plain-text trace into readable debug sections."""
    if not debug_message:
        return {
            "interaction_runs": [],
            "controller_lines": [],
            "transition_lines": [],
            "summary_pairs": [],
            "stage_context_lines": [],
            "raw_trace": "",
        }

    raw_entries: dict[str, list[str | None]] = {"evaluation": [], "coaching": []}
    prompt_entries: dict[str, list[str | None]] = {"evaluation": [], "coaching": []}
    cleaned_lines: list[str] = []
    buffer: list[str] = []
    capture_kind: str | None = None
    capture_target: str | None = None

    for original_line in debug_message.splitlines():
        line = original_line.rstrip()
        if not line:
            continue

        if line == "evaluation_prompt_full_begin":
            capture_kind = "evaluation"
            capture_target = "prompt"
            buffer = []
            continue

        if line == "coaching_prompt_full_begin":
            capture_kind = "coaching"
            capture_target = "prompt"
            buffer = []
            continue

        if line == "evaluation_llm_reply_raw_begin":
            capture_kind = "evaluation"
            capture_target = "raw"
            buffer = []
            continue

        if line == "coaching_llm_reply_raw_begin":
            capture_kind = "coaching"
            capture_target = "raw"
            buffer = []
            continue

        if capture_kind is not None and capture_target is not None:
            if line == f"{capture_kind}_prompt_full_end" and capture_target == "prompt":
                prompt_entries[capture_kind].append("\n".join(buffer).strip() or None)
                capture_kind = None
                capture_target = None
                buffer = []
                continue

            if line == f"{capture_kind}_llm_reply_raw_end" and capture_target == "raw":
                raw_entries[capture_kind].append("\n".join(buffer).strip() or None)
                capture_kind = None
                capture_target = None
                buffer = []
                continue

            buffer.append(line)
            continue

        if line.startswith("evaluation_llm_reply_raw="):
            value = line.split("=", 1)[1].strip()
            raw_entries["evaluation"].append(None if value == "<none>" else value)
            continue

        if line.startswith("coaching_llm_reply_raw="):
            value = line.split("=", 1)[1].strip()
            raw_entries["coaching"].append(None if value == "<none>" else value)
            continue

        cleaned_lines.append(line)

    key_value_pairs: list[tuple[str, str]] = []
    free_lines: list[str] = []

    for line in cleaned_lines:
        if "=" in line and not line.startswith("Macro transition applied:"):
            key, value = line.split("=", 1)
            key_value_pairs.append((key.strip(), value.strip()))
        else:
            free_lines.append(line)

    latest_values: dict[str, str] = {}
    for key, value in key_value_pairs:
        latest_values[key] = value

    summary_keys = [
        ("classification_normalized_outcome", "Classification outcome"),
        ("coaching_normalized_outcome", "Coaching outcome"),
        ("classification_resolution", "Classification resolution"),
        ("coaching_resolution", "Coaching resolution"),
        ("synthesis_resolution", "Synthesis resolution"),
        ("pathways_resolution", "Pathways resolution"),
        ("closure_resolution", "Closure resolution"),
        ("controller_state_type", "State type"),
        ("next_stage", "Next stage"),
    ]
    summary_pairs = [
        (label, latest_values[key])
        for key, label in summary_keys
        if key in latest_values
    ]

    transition_lines = [
        line
        for line in cleaned_lines
        if (
            line.startswith("Macro transition applied:")
            or "_transition=" in line
            or "_resolution=" in line
            or line.startswith("next_stage=")
        )
    ]

    controller_lines = [
        line
        for line in cleaned_lines
        if line.startswith("controller_")
    ]

    stage_context_lines = [
        line
        for line in cleaned_lines
        if any(
            marker in line
            for marker in (
                "_raw_outcome=",
                "_engine_missing_fields=",
                "_fallback=",
                "_reason=",
                "_parse_status=",
                "matched_",
            )
        )
    ]

    interaction_runs: list[dict[str, Any]] = []
    pending_chunk: list[str] = []
    raw_index = {"evaluation": 0, "coaching": 0}
    prompt_index = {"evaluation": 0, "coaching": 0}

    for line in cleaned_lines:
        pending_chunk.append(line)
        if not line.startswith("prompt_preview="):
            continue

        chunk_values: dict[str, str] = {}
        for chunk_line in pending_chunk:
            if "=" in chunk_line and not chunk_line.startswith("Macro transition applied:"):
                key, value = chunk_line.split("=", 1)
                chunk_values[key.strip()] = value.strip()

        interaction_type = chunk_values.get("interaction_type", "unknown")
        if interaction_type in raw_entries:
            current_index = raw_index[interaction_type]
            raw_reply = (
                raw_entries[interaction_type][current_index]
                if current_index < len(raw_entries[interaction_type])
                else None
            )
            raw_index[interaction_type] = current_index + 1
        else:
            raw_reply = None

        if interaction_type in prompt_entries:
            current_index = prompt_index[interaction_type]
            prompt_full = (
                prompt_entries[interaction_type][current_index]
                if current_index < len(prompt_entries[interaction_type])
                else None
            )
            prompt_index[interaction_type] = current_index + 1
        else:
            prompt_full = None

        interaction_runs.append(
            {
                "interaction_type": interaction_type,
                "stage_state": chunk_values.get("stage_state"),
                "config_status": chunk_values.get("config_status"),
                "llm_call_status": chunk_values.get("llm_call_status"),
                "structured_parse_status": chunk_values.get("structured_parse_status"),
                "prompt_preview": chunk_values.get("prompt_preview"),
                "prompt_full": prompt_full,
                "raw_reply": raw_reply,
            }
        )
        pending_chunk = []

    return {
        "interaction_runs": interaction_runs,
        "controller_lines": controller_lines,
        "transition_lines": transition_lines,
        "summary_pairs": summary_pairs,
        "stage_context_lines": stage_context_lines,
        "raw_trace": debug_message,
    }


def _render_debug_snapshot(snapshot: dict[str, Any], snapshot_index: int) -> None:
    """Render one structured debug snapshot."""
    parsed = _parse_debug_message(snapshot.get("debug_message"))
    session = snapshot.get("session", {})
    stage = session.get("stage", "unknown")
    state = session.get("state", "unknown")

    status_parts = ["completed" if session.get("completed") else "active"]
    if session.get("cancelled"):
        status_parts.append("cancelled")

    st.markdown('<div class="debug-card">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="debug-kicker">{snapshot.get("label", "Turn trace")}</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        f"Stage `{stage}` · State `{state}` · "
        f"Turn {snapshot.get('turn_count', 0)} · "
        f"Stage turn {snapshot.get('stage_turn_count', 0)} · "
        f"Status: {', '.join(status_parts)}"
    )

    _render_text_panel(
        "User input",
        snapshot.get("user_message"),
        preview_chars=180,
    )
    _render_text_panel(
        "Evaluation assessment",
        snapshot.get("evaluation_message"),
        preview_chars=220,
    )
    _render_text_panel(
        "Visible coaching text",
        snapshot.get("coach_message"),
        preview_chars=220,
    )

    if parsed["summary_pairs"]:
        st.markdown("**Key decisions**")
        for label, value in parsed["summary_pairs"]:
            st.write(f"- {label}: `{value}`")

    if parsed["transition_lines"]:
        with st.expander("Transitions", expanded=False):
            for line in parsed["transition_lines"]:
                st.write(f"- {line}")

    if parsed["interaction_runs"]:
        for run_index, run in enumerate(parsed["interaction_runs"], start=1):
            title = (
                f"{run['interaction_type'].title()} call {run_index} "
                f"· state `{run.get('stage_state') or 'unknown'}`"
            )
            with st.expander(title, expanded=False):
                if run.get("llm_call_status"):
                    st.write(f"LLM status: `{run['llm_call_status']}`")
                if run.get("structured_parse_status"):
                    st.write(f"Parse status: `{run['structured_parse_status']}`")
                if run.get("config_status"):
                    st.caption(run["config_status"])
                _render_text_panel(
                    "Prompt preview",
                    run.get("prompt_preview"),
                    preview_chars=220,
                )
                _render_text_panel(
                    "Full prompt sent to LLM",
                    run.get("prompt_full"),
                    preview_chars=280,
                    expanded=True,
                    empty_caption="Full prompt: none",
                )
                _render_text_panel(
                    "Full raw LLM reply",
                    run.get("raw_reply"),
                    preview_chars=280,
                    expanded=True,
                    empty_caption="Raw LLM reply: none",
                )

    if parsed["controller_lines"]:
        with st.expander("Controller trace", expanded=False):
            for line in parsed["controller_lines"]:
                st.write(f"- {line}")

    if snapshot.get("stage_context"):
        with st.expander("Stage context", expanded=False):
            st.json(snapshot["stage_context"])

    if parsed["stage_context_lines"]:
        with st.expander("Fallback and parsing detail", expanded=False):
            for line in parsed["stage_context_lines"]:
                st.write(f"- {line}")

    with st.expander("Full raw trace", expanded=False):
        _render_text_panel(
            "Trace",
            parsed["raw_trace"],
            preview_chars=260,
            expanded=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_debug_panel() -> None:
    """Render the structured debug sidebar."""
    with st.sidebar:
        st.markdown("### Debug Panel")
        st.caption(f"Backend: `{API_URL}`")

        show_debug = st.checkbox("Show structured debug", value=True)
        if st.session_state.frontend_error:
            st.error(st.session_state.frontend_error)

        if not show_debug:
            return

        if not st.session_state.session_id:
            st.info("Start a session to inspect turn-by-turn debug output.")
            return

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Refresh trace", use_container_width=True):
                _capture_debug_snapshot("Manual refresh", force_append=False)
                st.rerun()
        with col2:
            if st.button("Clear history", use_container_width=True):
                st.session_state.debug_history = []
                st.session_state.latest_debug = None
                st.session_state.latest_debug_fingerprint = None
                st.rerun()

        latest_snapshot = _capture_debug_snapshot("Live snapshot", force_append=False)
        if latest_snapshot is None:
            latest_snapshot = st.session_state.latest_debug
        if latest_snapshot is None:
            st.warning("No debug payload is available yet.")
            return

        st.markdown("#### Latest turn")
        _render_debug_snapshot(latest_snapshot, snapshot_index=0)

        history = st.session_state.debug_history[:-1]
        if history:
            st.markdown("#### Earlier turns")
            for reverse_index, snapshot in enumerate(reversed(history), start=1):
                session = snapshot.get("session", {})
                header = (
                    f"Turn {snapshot.get('turn_count', 0)} · "
                    f"{session.get('stage', 'unknown')}/{session.get('state', 'unknown')} · "
                    f"{snapshot.get('label', 'trace')}"
                )
                with st.expander(header, expanded=False):
                    _render_debug_snapshot(snapshot, snapshot_index=reverse_index)


# ------------------------------------------------
# Mapping and response handling
# ------------------------------------------------
def map_backend_to_screen(session: dict[str, Any]) -> str:
    """Translate the backend macro-stage into the current UI screen."""
    return {
        "classification": "coaching",
        "coaching": "coaching",
        "synthesis": "synthesis_review",
        "pathways": "pathways",
        "closure": "feedback",
    }.get(session.get("stage"), "coaching")


def _apply_backend_turn(data: dict[str, Any] | None, debug_label: str) -> bool:
    """Update the frontend session state from one backend reply."""
    if data is None:
        return False

    session = data.get("session", {})
    st.session_state.session_view = session
    st.session_state.coach_message = data.get("coach_message") or ""
    st.session_state.ui_screen = map_backend_to_screen(session)
    _capture_debug_snapshot(debug_label, force_append=True)
    return True


def _send_message_with_feedback(
    message: str,
    *,
    pending_text: str,
) -> dict[str, Any] | None:
    """Show an in-page pending state while waiting for one backend reply."""
    pending_placeholder = st.empty()
    pending_placeholder.markdown(
        (
            '<div class="pending-card">'
            '<div class="pending-header"><span class="pending-dot"></span>'
            'Reply pending</div>'
            f"{html.escape(pending_text).replace(chr(10), '<br>')}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    with st.spinner("Aether is preparing the next reply..."):
        data = api_send_message(message)

    pending_placeholder.empty()
    return data


def _is_refined_synthesis_waiting_for_pathways(session: dict[str, Any]) -> bool:
    """Detect the specific backend state after a synthesis refinement reply."""
    return (
        session.get("stage") == "pathways"
        and session.get("state") == "preparing"
    )


def _parse_pathway_cards(text: str | None) -> list[dict[str, str]]:
    """Extract pathway cards from the structured pathways coach_message text."""
    source = str(text or "").strip()
    if not source:
        return []

    heading_matches = list(re.finditer(r"(?m)^##\s+(.+?)\s*$", source))
    if not heading_matches:
        return []

    cards = []
    for index, match in enumerate(heading_matches):
        title = match.group(1).strip()
        body_start = match.end()
        body_end = (
            heading_matches[index + 1].start()
            if index + 1 < len(heading_matches)
            else len(source)
        )
        body = source[body_start:body_end].strip()
        if not title or not body:
            continue
        cards.append({"title": title, "body": body})

    return cards


# ------------------------------------------------
# Screens
# ------------------------------------------------
def render_welcome() -> None:
    st.title("Aether")
    st.write("### Welcome to Aether")
    st.write("Together we’ll explore a challenge you’re facing at work.")
    st.write("Before we get stuck in, there’s a few things we need to agree on.")

    if st.button("Start"):
        st.session_state.ui_screen = "confidentiality"
        st.rerun()


def render_confidentiality() -> None:
    st.markdown("### 🔒 Confidential Thinking Space")
    st.markdown(
        """
Aether is a confidential thinking space.

The thoughts you share with us during this session are used solely to guide your coaching conversation.

It is not stored beyond your active session, not shared with any third party, and not used to train AI models.

You are in control of what you share.
Take your time. Think clearly.
"""
    )

    consent = st.checkbox(
        "I understand that my session content is confidential and used only for this coaching conversation."
    )

    if st.button("Next", disabled=not consent):
        st.session_state.ui_screen = "intro"
        st.rerun()


def render_intro() -> None:
    st.markdown("### 🧭 Before we begin")
    st.write(
        """
This is a space to explore one professional challenge with clarity and depth.

Aether will ask you questions that help you understand your problem more fully before presenting a set of pathways you can take away and act on.
"""
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🔵")
        st.caption("You = your thinking")
    with col2:
        st.markdown("### 🟢")
        st.caption("Aether = your guide")

    if st.button("Start Session"):
        data = api_init_session()
        if data is None:
            return

        st.session_state.session_id = data["session_id"]
        st.session_state.session_view = data
        st.session_state.debug_history = []
        st.session_state.latest_debug = None
        st.session_state.latest_debug_fingerprint = None
        st.session_state.awaiting_pathways_after_refinement = False
        st.session_state.problem_input_version = 0
        st.session_state.coaching_input_version = 0
        st.session_state.synthesis_feedback_version = 0
        st.session_state.pathways_selection_version = 0
        _capture_debug_snapshot("Session initialised", force_append=True)
        st.session_state.ui_screen = "problem_input"
        st.rerun()


def render_problem_input() -> None:
    st.markdown("### 💭 Let’s think this through together")
    st.write(
        """
In the field below, describe a professional challenge, problem, or unresolved issue you are currently facing.
"""
    )

    st.markdown("### 🔵 You")

    problem_input_key = f"problem_input_box_{st.session_state.problem_input_version}"
    user_input = st.text_area("Your response here...", key=problem_input_key)

    if st.button("Continue") and user_input:
        data = _send_message_with_feedback(
            user_input,
            pending_text=user_input,
        )
        if _apply_backend_turn(data, "Opening problem submitted"):
            st.session_state.problem_input_version += 1
            st.rerun()


def render_coaching() -> None:
    st.markdown("### 🟢 Aether")
    if st.session_state.coach_message:
        st.markdown(
            (
                '<div class="message-card coach-card">'
                f"{html.escape(st.session_state.coach_message).replace(chr(10), '<br>')}"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
    else:
        st.info("No coach message is available yet.")

    st.markdown("### 🔵 You")
    coaching_input_key = f"coaching_input_box_{st.session_state.coaching_input_version}"
    user_input = st.text_area("Your response here...", key=coaching_input_key)

    if st.button("Continue") and user_input:
        data = _send_message_with_feedback(
            user_input,
            pending_text=user_input,
        )
        if _apply_backend_turn(data, "Coaching response submitted"):
            st.session_state.coaching_input_version += 1
            st.rerun()


def render_synthesis_review() -> None:
    awaiting_pathways = bool(st.session_state.awaiting_pathways_after_refinement)

    st.write(
        """
We’ve made considerable progress, and based on the reflective conversation, the challenge you are navigating is:
"""
    )

    _render_text_panel(
        "Current synthesis",
        st.session_state.coach_message,
        preview_chars=280,
        expanded=True,
    )

    if awaiting_pathways:
        st.write("Your refinement has been applied. Review the updated synthesis and continue to see the pathways.")
    else:
        st.write("Have we captured this accurately?")

    col1, col2 = st.columns(2)

    with col1:
        primary_label = "Continue to pathways" if awaiting_pathways else "That’s it"
        primary_message = "continue" if awaiting_pathways else "yes"
        primary_debug_label = (
            "Refined synthesis accepted"
            if awaiting_pathways
            else "Synthesis accepted"
        )
        if st.button(primary_label):
            data = _send_message_with_feedback(
                primary_message,
                pending_text=(
                    "Your updated synthesis has been accepted. Preparing the next step..."
                    if awaiting_pathways
                    else "Synthesis accepted. Preparing the next step..."
                ),
            )
            if _apply_backend_turn(data, primary_debug_label):
                st.session_state.awaiting_pathways_after_refinement = False
                st.rerun()

    with col2:
        if awaiting_pathways:
            st.empty()
            return

        synthesis_feedback_key = (
            f"synthesis_feedback_{st.session_state.synthesis_feedback_version}"
        )
        feedback = st.text_area(
            "Not quite",
            key=synthesis_feedback_key,
            height=140,
            placeholder="Add the detail that should be reflected in the updated synthesis...",
        )
        if st.button("Submit") and feedback:
            data = _send_message_with_feedback(
                feedback,
                pending_text=feedback,
            )
            if _apply_backend_turn(data, "Synthesis refinement requested"):
                session = data.get("session", {})
                st.session_state.awaiting_pathways_after_refinement = (
                    _is_refined_synthesis_waiting_for_pathways(session)
                )
                if st.session_state.awaiting_pathways_after_refinement:
                    st.session_state.ui_screen = "synthesis_review"
                st.session_state.synthesis_feedback_version += 1
                st.rerun()


def render_pathways() -> None:
    pathway_cards = _parse_pathway_cards(st.session_state.coach_message)

    st.write(
        """
Based on everything we have explored, here are the pathways available to you.

Each one represents a distinct direction. They are not ranked and none is the right answer.
Expand a pathway card for more detail, then choose one or continue.
"""
    )

    if pathway_cards:
        card_columns = st.columns(2)
        for index, card in enumerate(pathway_cards):
            with card_columns[index % 2]:
                with st.expander(f"⊕ {card['title']}", expanded=False):
                    st.markdown(
                        (
                            '<div class="text-panel">'
                            f"{html.escape(card['body']).replace(chr(10), '<br>')}"
                            "</div>"
                        ),
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "Choose this pathway",
                        key=f"pathway_choose_{index}",
                        use_container_width=True,
                    ):
                        data = _send_message_with_feedback(
                            f"pathway_selected:{card['title']}",
                            pending_text=f"Chosen pathway: {card['title']}",
                        )
                        if _apply_backend_turn(data, "Pathway choice submitted"):
                            st.session_state.pathways_selection_version += 1
                            st.rerun()
    else:
        st.markdown('<div class="pathways-box">', unsafe_allow_html=True)
        with st.expander("View the pathways text", expanded=True):
            _render_text_panel(
                "Pathways",
                st.session_state.coach_message,
                preview_chars=320,
                expanded=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("View raw pathways text", expanded=False):
        _render_text_panel(
            "Pathways",
            st.session_state.coach_message,
            preview_chars=320,
            expanded=True,
        )

    st.write("If you want, you can type the pathway name or your preferred direction.")
    pathways_selection_key = (
        f"pathways_selection_input_{st.session_state.pathways_selection_version}"
    )
    selected_pathway = st.text_input(
        "Chosen pathway or reaction",
        key=pathways_selection_key,
        placeholder="For example: Build the evidence first",
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Submit choice", use_container_width=True):
            if selected_pathway:
                data = _send_message_with_feedback(
                    f"pathway_selected:{selected_pathway}",
                    pending_text=f"Chosen pathway: {selected_pathway}",
                )
                if _apply_backend_turn(data, "Pathway choice submitted"):
                    st.session_state.pathways_selection_version += 1
                    st.rerun()
            else:
                st.warning("Type a pathway choice first, or use Continue without choosing.")

    with col2:
        if st.button("Continue", use_container_width=True):
            data = _send_message_with_feedback(
                "continue",
                pending_text="Continuing with the selected pathways step...",
            )
            if _apply_backend_turn(data, "Pathways acknowledged"):
                st.session_state.pathways_selection_version += 1
                st.rerun()


def render_feedback() -> None:
    if st.session_state.coach_message:
        st.write("### Closing message")
        _render_text_panel(
            "Closure",
            st.session_state.coach_message,
            preview_chars=260,
            expanded=True,
        )

    st.write("### Before you go, please tell us what you thought of the Aether experience.")

    st.radio(
        "Did Aether help you think about your challenge in a new way?",
        ["Yes", "No"],
        key="feedback_helpful",
        index=None,
    )

    st.radio(
        "Can this kind of thinking support benefit an organisation?",
        ["Yes", "No"],
        key="feedback_org",
        index=None,
    )

    st.multiselect(
        "What was the most valuable moment?",
        [
            "Being asked a question I hadn’t thought to ask myself",
            "The moment Aether reflected my challenge back to me accurately",
            "Seeing my problem restated clearly in one place",
            "Receiving structured pathways rather than a generic answer",
            "The feeling that I was being guided rather than just given information",
            "Having a confidential space to think without judgement",
        ],
        key="feedback_value",
    )

    if st.button("Close"):
        st.session_state.ui_screen = "closed"
        st.rerun()


def render_closed() -> None:
    st.write("Session complete")


# ------------------------------------------------
# Layout
# ------------------------------------------------
if _debug_enabled():
    render_debug_panel()

if st.session_state.frontend_notice:
    st.warning(st.session_state.frontend_notice)

if st.session_state.frontend_error:
    st.error(st.session_state.frontend_error)


{
    "welcome": render_welcome,
    "confidentiality": render_confidentiality,
    "intro": render_intro,
    "problem_input": render_problem_input,
    "coaching": render_coaching,
    "synthesis_review": render_synthesis_review,
    "pathways": render_pathways,
    "feedback": render_feedback,
    "closed": render_closed,
}[st.session_state.ui_screen]()
