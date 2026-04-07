import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(layout="wide")

# ------------------------------------------------
# Styling (safe but closer to spec)
# ------------------------------------------------
st.markdown("""
<style>
.block-container {
    max-width: 680px;
    margin: auto;
    padding-top: 3rem;
}

h1, h2 {
    text-align: center;
}

.section {
    margin-top: 2rem;
    padding: 1.5rem;
    border-radius: 12px;
    background-color: #ffffff;
    border: 1px solid #eaeaea;
}

.button-primary button {
    width: 100%;
    background: linear-gradient(90deg, #7ed957, #c1fba4);
    color: black;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# Session state
# ------------------------------------------------
if "ui_screen" not in st.session_state:
    st.session_state.ui_screen = "welcome"

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "coach_message" not in st.session_state:
    st.session_state.coach_message = ""

if "input_text" not in st.session_state:
    st.session_state.input_text = ""

# ------------------------------------------------
# API
# ------------------------------------------------
def api_init_session():
    return requests.get(f"{API_URL}/session_initialise").json()

def api_send_message(msg):
    return requests.post(
        f"{API_URL}/user_message",
        json={"session_id": st.session_state.session_id, "user_message": msg},
    ).json()

# ------------------------------------------------
# Debug
# ------------------------------------------------
with st.sidebar:
    st.markdown("### 🧠 Debug")
    if st.checkbox("Show debug") and st.session_state.session_id:
        st.json(requests.get(f"{API_URL}/debug_trace/{st.session_state.session_id}").json())

# ------------------------------------------------
# Mapping
# ------------------------------------------------
def map_backend_to_screen(session):
    return {
        "classification": "coaching",
        "coaching": "coaching",
        "synthesis": "synthesis_review",
        "pathways": "pathways",
        "closure": "feedback",
    }.get(session["stage"], "coaching")

# ------------------------------------------------
# Screens
# ------------------------------------------------

def render_welcome():
    st.title("Aether")

    st.write("### Welcome to Aether")
    st.write("Together we’ll explore a challenge you’re facing at work.")
    st.write("Before we get stuck in, there’s a few things we need to agree on.")

    if st.button("Start"):
        st.session_state.ui_screen = "confidentiality"
        st.rerun()


def render_confidentiality():
    st.markdown("### 🔒 Confidential Thinking Space")

    st.markdown("""
Aether is a confidential thinking space.

The thoughts you share with us during this session are used solely to guide your coaching conversation.

It is not stored beyond your active session, not shared with any third party, and not used to train AI models.

You are in control of what you share.  
Take your time. Think clearly.
""")

    consent = st.checkbox(
        "I understand that my session content is confidential and used only for this coaching conversation."
    )

    if st.button("Next", disabled=not consent):
        st.session_state.ui_screen = "intro"
        st.rerun()


def render_intro():
    st.markdown("### 🧭 Before we begin")

    st.write("""
This is a space to explore one professional challenge with clarity and depth.

Aether will ask you questions that help you understand your problem more fully before presenting a set of pathways you can take away and act on.

🔵 You = your thinking  
🟢 Aether = your guide
""")

    if st.button("Start Session"):
        data = api_init_session()
        st.session_state.session_id = data["session_id"]
        st.session_state.ui_screen = "problem_input"
        st.rerun()


def render_problem_input():
    st.markdown("### 💭 Let’s think this through together")

    st.write("""
In the field below, describe a professional challenge, problem, or unresolved issue you are currently facing.
""")

    st.markdown("### 🔵")
    st.caption("You")

    if "problem_input_box" not in st.session_state:
        st.session_state.problem_input_box = ""

    user_input = st.text_area(
        "Your response here...",
        key="problem_input_box"
    )

    if st.button("Continue") and user_input:
        data = api_send_message(user_input)

        st.session_state.coach_message = data["coach_message"]
        st.session_state.ui_screen = map_backend_to_screen(data["session"])

        del st.session_state["problem_input_box"]
        st.rerun()


def render_coaching():
    st.markdown("### 🟢 Aether")
    st.write(st.session_state.coach_message)

    st.markdown("### 🔵")
    st.caption("You")

    if "coaching_input_box" not in st.session_state:
        st.session_state.coaching_input_box = ""

    user_input = st.text_area(
        "Your response here...",
        key="coaching_input_box"
    )

    if st.button("Continue") and user_input:
        data = api_send_message(user_input)

        st.session_state.coach_message = data["coach_message"]
        st.session_state.ui_screen = map_backend_to_screen(data["session"])

        del st.session_state["coaching_input_box"]
        st.rerun()


def render_synthesis_review():
    st.write("""
We’ve made considerable progress, and based on the reflective conversation, the challenge you are navigating is:
""")

    st.markdown(f"> {st.session_state.coach_message}")

    st.write("Have we captured this accurately?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("That’s it"):
            data = api_send_message("yes")
            st.session_state.coach_message = data["coach_message"]
            st.session_state.ui_screen = map_backend_to_screen(data["session"])
            st.rerun()

    with col2:
        feedback = st.text_input("Not quite")
        if st.button("Submit") and feedback:
            data = api_send_message(feedback)
            st.session_state.coach_message = data["coach_message"]
            st.session_state.ui_screen = map_backend_to_screen(data["session"])
            st.rerun()


def render_pathways():
    st.write("""
Based on everything we have explored, here are the pathways available to you.

Each one represents a distinct direction. They are not ranked and none is the right answer.
Expand each pathway for more detail.
""")

    # simulate 4 pathway buttons (visual proxy)
    col1, col2 = st.columns(2)

    with col1:
        st.button("BUILD THE EVIDENCE FIRST")
        st.button("ACTIVATE THROUGH CENTRALISED CAPABILITY")

    with col2:
        st.button("REFRAME THE BUSINESS CASE")
        st.button("CREATE A LOW-BARRIER MODEL")

    if st.button("Next"):
        st.session_state.ui_screen = "feedback"
        st.rerun()


def render_feedback():
    st.write("### Before you go, please tell us what you thought of the Aether experience.")

    st.radio("Did Aether help you think about your challenge in a new way?", ["Yes", "No"])

    st.radio("Can this kind of thinking support benefit an organisation?", ["Yes", "No"])

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
    )

    if st.button("Close"):
        st.session_state.ui_screen = "closed"
        st.rerun()


def render_closed():
    st.write("Session complete")


# ------------------------------------------------
# Router
# ------------------------------------------------
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