# streamlit_lead_widget.py (Frontend-only, widget-style)
# Lightweight Streamlit frontend demo styled like a real widget.
# - Live Q&A demo pane (input + placeholder answer)
# - Nudges UI (linger/scroll/interaction simulation)
# - Lead capture form (low friction)

import streamlit as st
import time
import uuid

# --- Utils

def now_iso():
    import datetime
    return datetime.datetime.utcnow().isoformat() + "Z"

# --- Streamlit UI

st.set_page_config(page_title="Lead Widget - Frontend Demo", layout="centered")

# Initialize session state for tracking
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.start_time = time.time()
    st.session_state.ask_count = 0
    st.session_state.clicked_sources = 0
    st.session_state.history = []

def mock_answer(query: str):
    return f"[Demo answer for] {query} — (Backend RAG would respond here with trusted source)."

# --- Chat-like UI container
st.markdown("<style> div.stButton > button { width: 100%; } </style>", unsafe_allow_html=True)

chat_container = st.container()
lead_container = st.container()

with chat_container:
    st.text_input("Ask a question", key="query")
    if st.button("Send") and st.session_state.query:
        st.session_state.ask_count += 1
        answer_text = mock_answer(st.session_state.query)

        st.session_state.history.append({
            "query": st.session_state.query,
            "answer": answer_text,
            "timestamp": now_iso(),
        })

    # Display chat history
    for item in st.session_state.history:
        with st.chat_message("user"):
            st.write(item["query"])
        with st.chat_message("assistant"):
            st.write(item["answer"])
            st.caption("Source: https://example.com")

    if st.button("I clicked a source (simulate)"):
        st.session_state.clicked_sources += 1

    # Nudges simulation
    elapsed = time.time() - st.session_state.start_time
    if elapsed > 10 or st.session_state.ask_count >= 2 or st.session_state.clicked_sources > 0:
        st.info("Looks like you're interested — want a personalized quote or demo?")
        if st.button("Yes, I'm interested"):
            st.session_state.show_lead_modal = True
            st.rerun()

# --- Lead capture form
with lead_container:
    if st.session_state.get("show_lead_modal", False):
        st.subheader("Share your details")
        name = st.text_input("Name (optional)")
        email = st.text_input("Email (optional)")
        phone = st.text_input("Phone (optional)")
        interest = st.selectbox("Interest level", ["Curious", "Considering", "Ready to talk"], index=0)

        if st.button("Submit"):
            st.success("Lead submitted (demo only, not saved).")
            st.session_state.show_lead_modal = False