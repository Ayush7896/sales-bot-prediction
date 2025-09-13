import streamlit as st
import requests
import os

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.title("Chatbot")

if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

# Display chat history
for message in st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
user_input = st.chat_input("Type your question...")

if user_input:
    # Add user query
    st.session_state["message_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # MODIFY THIS LINE:
    payload = {"user_query": user_input, "session_id": "streamlit_session"}

    try:
        response = requests.post(f"{API_URL}/ask", json=payload)

        if response.status_code == 200:
            data = response.json()
            ai_message = data.get("bot_response", "No response from model")

            st.session_state["message_history"].append({"role": "assistant", "content": ai_message})
            with st.chat_message("assistant"):
                st.markdown(ai_message)
        else:
            st.error(f"Server error ({response.status_code}): {response.text}")

    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")