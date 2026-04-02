import streamlit as st
import requests

API_BASE_URL = "http://127.0.0.1:8000"


st.set_page_config(page_title="Coach V3", page_icon="💬")
st.title("Coach V3")

st.write("Basic local UI to test the backend API endpoints.")

if st.button("Initialise session"):
    try:
        response = requests.get(f"{API_BASE_URL}/session_initialise", timeout=10)
        response.raise_for_status()
        st.success("Session initialise called successfully.")
        st.json(response.json())
    except requests.RequestException as e:
        st.error(f"Error calling session_initialise: {e}")


st.subheader("Send user message")
user_text = st.text_input("Message", placeholder="Type a message here...")

if st.button("Send message"):
    try:
        response = requests.post(f"{API_BASE_URL}/user_message", timeout=10)
        response.raise_for_status()
        st.success("user_message called successfully.")
        st.json(response.json())
    except requests.RequestException as e:
        st.error(f"Error calling user_message: {e}")