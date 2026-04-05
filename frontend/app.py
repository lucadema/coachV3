"""
Streamlit frontend for Coach V3.

This UI is intentionally minimal and aligned with the current POC API
contracts:

- GET  /session_initialise -> returns a flat SessionView
- POST /user_message       -> expects {session_id, user_message}
- GET  /debug_trace/{id}   -> returns debug information for that session

Design goals:
- keep concerns separated
- encapsulate API calls in small functions
- persist session_id in Streamlit session state
- use the sidebar as a simple development log
"""

import os

import requests
import streamlit as st


LOCAL_API_URL = "http://127.0.0.1:8000"
API_BASE_URL = os.getenv("API_BASE_URL", LOCAL_API_URL)


# ============================================================================
# Page config
# ============================================================================

st.set_page_config(page_title="Coach V3", page_icon="💬")


# ============================================================================
# Session state
# ============================================================================

if "log_messages" not in st.session_state:
    st.session_state.log_messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "session_view" not in st.session_state:
    st.session_state.session_view = None


# ============================================================================
# Logging
# ============================================================================

def WriteLog(message: str) -> None:
    """Append a message to the sidebar log."""
    st.session_state.log_messages.append(str(message))


def ClearLog() -> None:
    """Clear the sidebar log."""
    st.session_state.log_messages = []


# ============================================================================
# API calling points
# ============================================================================

def InitialiseSession():
    """
    Create a new backend session.

    On success:
    - stores the returned session_id
    - stores the returned session view
    """
    try:
        WriteLog("Calling /session_initialise")

        response = requests.get(f"{API_BASE_URL}/session_initialise", timeout=10)
        response.raise_for_status()

        payload = response.json()

        st.session_state.session_id = payload["session_id"]
        st.session_state.session_view = payload

        WriteLog(f"Session initialised: {st.session_state.session_id}")
        return payload

    except requests.RequestException as e:
        WriteLog(f"ERROR in InitialiseSession: {e}")
        return None


def SendMessage(user_message: str):
    """
    Send a user message to the backend.

    The backend expects:
    {
        "session_id": "...",
        "user_message": "..."
    }
    """
    try:
        if not st.session_state.session_id:
            WriteLog("ERROR in SendMessage: no session has been initialised yet")
            return None

        request_payload = {
            "session_id": st.session_state.session_id,
            "user_message": user_message,
        }

        WriteLog(f"Calling /user_message for session {st.session_state.session_id}")

        response = requests.post(
            f"{API_BASE_URL}/user_message",
            json=request_payload,
            timeout=10,
        )
        response.raise_for_status()

        payload = response.json()

        if "session" in payload:
            st.session_state.session_view = payload["session"]

        WriteLog("User message handled successfully")
        return payload

    except requests.RequestException as e:
        WriteLog(f"ERROR in SendMessage: {e}")
        return None


def GetDebugTrace():
    """
    Retrieve debug information for the current session.

    The backend debug endpoint requires a session_id in the URL path.
    """
    try:
        if not st.session_state.session_id:
            WriteLog("ERROR in GetDebugTrace: no session has been initialised yet")
            return None

        session_id = st.session_state.session_id
        WriteLog(f"Calling /debug_trace/{session_id}")

        response = requests.get(
            f"{API_BASE_URL}/debug_trace/{session_id}",
            timeout=10,
        )
        response.raise_for_status()

        payload = response.json()
        WriteLog("Debug trace retrieved successfully")
        return payload

    except requests.RequestException as e:
        WriteLog(f"ERROR in GetDebugTrace: {e}")
        return None


# ============================================================================
# Debug trace handling
# ============================================================================

def LoadDebugTraceIntoLog() -> None:
    """Fetch debug data and append it to the sidebar log."""
    debug_payload = GetDebugTrace()

    if debug_payload is None:
        WriteLog("Failed to retrieve debug trace")
        return

    debug_message = debug_payload.get("debug_message")
    session = debug_payload.get("session", {})

    if session:
        WriteLog(
            f"DEBUG SESSION: id={session.get('session_id')} "
            f"stage={session.get('stage')} state={session.get('state')}"
        )

    if debug_message:
        WriteLog(f"DEBUG: {debug_message}")
    else:
        WriteLog("DEBUG: no debug_message returned")


# ============================================================================
# Sidebar panel
# ============================================================================

def RenderLogPanel() -> None:
    """Render the left sidebar log and debug controls."""
    st.sidebar.title("Log")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Get debug trace", key="get_debug_trace"):
            LoadDebugTraceIntoLog()
    with col2:
        if st.button("Clear log", key="clear_log"):
            ClearLog()

    st.sidebar.markdown("---")

    if not st.session_state.log_messages:
        st.sidebar.write("No log entries yet.")
        return

    for entry in st.session_state.log_messages:
        st.sidebar.write(entry)


# ============================================================================
# Main page
# ============================================================================

RenderLogPanel()

st.title("Coach V3")
st.write("Basic local UI to test the backend API endpoints.")
st.write(f"Using API: {API_BASE_URL}")

st.markdown("### Current session")
st.write(f"session_id: {st.session_state.session_id}")

if st.session_state.session_view is not None:
    st.json(st.session_state.session_view)

if st.button("Initialise session"):
    result = InitialiseSession()
    if result is not None:
        st.success("Session initialise called successfully.")
        st.json(result)
    else:
        st.error("Error calling session_initialise. See log for details.")

st.subheader("Send user message")
user_text = st.text_input("Message", placeholder="Type a message here...")

if st.button("Send message"):
    result = SendMessage(user_text)
    if result is not None:
        st.success("user_message called successfully.")
        st.json(result)
    else:
        st.error("Error calling user_message. See log for details.")
