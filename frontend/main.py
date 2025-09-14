import streamlit as st
import time
import requests
import os
import json
from datetime import datetime
import hashlib

st.set_page_config(layout="wide", page_title="FinanceHub AI Assistant")

API_URL = os.environ.get("API_URL", "http://localhost:8000")

# Generate a unique session key for this page load
# This will be different on every refresh
def get_page_session_key():
    return hashlib.md5(str(time.time()).encode()).hexdigest()[:8]

# Initialize or get page session key
if "page_session_key" not in st.session_state:
    st.session_state.page_session_key = get_page_session_key()
    st.session_state.page_load_time = time.time()
    # Reset all tab timers on new page load
    st.session_state.tab_visit_time = {}
    st.session_state.nudge_shown = {}
    st.session_state.nudge_dismissed = {}

# Check if this is a page refresh (new page load)
current_time = time.time()
if "last_activity_time" not in st.session_state:
    st.session_state.last_activity_time = current_time

# If more than 2 seconds have passed since last activity, treat as new page load
if current_time - st.session_state.last_activity_time > 2:
    st.session_state.page_session_key = get_page_session_key()
    st.session_state.page_load_time = time.time()
    st.session_state.tab_visit_time = {}
    st.session_state.nudge_shown = {}
    st.session_state.nudge_dismissed = {}

st.session_state.last_activity_time = current_time

# Custom CSS for better chat display
st.markdown("""
<style>
    .stChatMessage {
        background-color: transparent !important;
    }
    div[data-testid="stSidebarContent"] {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Load config.json
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except:
        return {}

config = load_config()

# Initialize session states (these persist across refreshes)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "focus_chat" not in st.session_state:
    st.session_state.focus_chat = False
if "question_count" not in st.session_state:
    st.session_state.question_count = 0
if "lead_captured" not in st.session_state:
    st.session_state.lead_captured = False
if "user_intent_score" not in st.session_state:
    st.session_state.user_intent_score = 0
if "interaction_log" not in st.session_state:
    st.session_state.interaction_log = []
if "active_tab" not in st.session_state:
    st.session_state.active_tab = None

# Configuration for nudge timing (in seconds)
NUDGE_DELAY_SECONDS = 15  # Nudge appears after 15 seconds

# Function to calculate user intent score
def calculate_intent_score(query):
    high_intent_keywords = ["price", "cost", "apply", "eligibility", "documents", "loan", "interest", "emi", "process"]
    score = 0
    query_lower = query.lower()
    for keyword in high_intent_keywords:
        if keyword in query_lower:
            score += 2
    return score

# Function to save lead to JSON file
def save_lead(name, email, phone=""):
    lead_data = {
        "name": name,
        "email": email,
        "phone": phone,
        "timestamp": datetime.now().isoformat(),
        "source": "chatbot",
        "questions_asked": st.session_state.question_count,
        "intent_score": st.session_state.user_intent_score,
        "user_type": "HOT_LEAD" if st.session_state.user_intent_score > 5 else "WARM_LEAD"
    }
    
    try:
        with open('leads.json', 'a') as f:
            json.dump(lead_data, f)
            f.write('\n')
        return True
    except:
        return False

# Function to save conversation history
def save_conversation_history():
    """Save the current conversation to a JSON file"""
    conversation_data = {
        "session_id": "streamlit_session",
        "timestamp": datetime.now().isoformat(),
        "question_count": st.session_state.question_count,
        "intent_score": st.session_state.user_intent_score,
        "user_type": "HOT_LEAD" if st.session_state.user_intent_score > 5 else "WARM_LEAD" if st.session_state.user_intent_score > 0 else "BROWSING",
        "lead_captured": st.session_state.lead_captured,
        "messages": st.session_state.messages,
        "interaction_log": st.session_state.interaction_log
    }
    
    try:
        # Read existing conversations
        try:
            with open('conversation_history.json', 'r') as f:
                conversations = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            conversations = []
        
        # Check if this session already exists and update it
        session_exists = False
        for i, conv in enumerate(conversations):
            if conv.get("session_id") == "streamlit_session":
                conversations[i] = conversation_data
                session_exists = True
                break
        
        # If new session, append it
        if not session_exists:
            conversations.append(conversation_data)
        
        # Write back to file
        with open('conversation_history.json', 'w') as f:
            json.dump(conversations, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving conversation: {e}")
        return False

# Function to load conversation history
def load_conversation_history():
    """Load existing conversation history if available"""
    try:
        with open('conversation_history.json', 'r') as f:
            conversations = json.load(f)
            
        # Find the current session
        for conv in conversations:
            if conv.get("session_id") == "streamlit_session":
                # Restore session state
                st.session_state.messages = conv.get("messages", [])
                st.session_state.question_count = conv.get("question_count", 0)
                st.session_state.user_intent_score = conv.get("intent_score", 0)
                st.session_state.lead_captured = conv.get("lead_captured", False)
                st.session_state.interaction_log = conv.get("interaction_log", [])
                return True
    except:
        pass
    return False

st.sidebar.markdown("## 💬 FinanceHub AI Assistant")
st.sidebar.markdown("---")

# Show user type indicator (for demo - remove in production)
if st.session_state.user_intent_score > 0:
    if st.session_state.user_intent_score > 5:
        st.sidebar.success(f"🔥 Hot Lead (Score: {st.session_state.user_intent_score})")
    else:
        st.sidebar.info(f"👤 Interested User (Score: {st.session_state.user_intent_score})")

# Show welcome message if user clicked "Chat with us"
if st.session_state.focus_chat:
    st.sidebar.success("👋 Hi! I'm here to help with all your finance queries!")
    st.session_state.focus_chat = False

# Lead capture form - shows after 2 questions for high-intent users
if st.session_state.question_count >= 2 and not st.session_state.lead_captured and st.session_state.user_intent_score > 3:
    with st.sidebar.container():
        st.warning("💡 I can provide personalized loan options for you! Quick details please:")
        
        with st.form("lead_form", clear_on_submit=False):
            lead_name = st.text_input("Name*")
            lead_email = st.text_input("Email*")
            lead_phone = st.text_input("Phone (optional)")
            
            if st.form_submit_button("Get Personalized Quote"):
                if lead_name and lead_email:
                    if save_lead(lead_name, lead_email, lead_phone):
                        st.session_state.lead_captured = True
                        save_conversation_history()
                        success_msg = config.get('lead_capture', {}).get('success_message', 
                                                'Thank you! Our team will contact you within 2 hours.')
                        st.sidebar.success(success_msg)
                        st.session_state.last_activity_time = time.time()
                        st.rerun()
                else:
                    st.sidebar.error("Please fill Name and Email")

# Chat container with proper scrolling
chat_container = st.sidebar.container()

# Display all messages in order
with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Chat input at the bottom
user_input = st.sidebar.chat_input("Ask about loans, interest rates, eligibility...")

if user_input:
    # Update activity time
    st.session_state.last_activity_time = time.time()
    
    # Calculate intent score
    intent_score = calculate_intent_score(user_input)
    st.session_state.user_intent_score += intent_score
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.question_count += 1
    
    # Log interaction
    st.session_state.interaction_log.append({
        "timestamp": datetime.now().isoformat(),
        "query": user_input,
        "intent_score": intent_score
    })
    
    # Call backend API
    payload = {
        "user_query": user_input, 
        "session_id": "streamlit_session"
    }
    
    try:
        response = requests.post(f"{API_URL}/ask", json=payload)
        if response.status_code == 200:
            data = response.json()
            ai_message = data.get("bot_response", "No response from model")
            
            # Add instant FAQ indicator
            if data.get("is_instant_faq"):
                ai_message = f"✨ {ai_message}"
            
            # Add source information if available (for both FAQ and RAG)
            sources = data.get("sources", [])
            if sources and sources != [None] and sources != ['']:
                ai_message += f"\n\n📚 *Source: {', '.join(sources)}*"
                
            # Add nudge if present
            if data.get("nudge"):
                ai_message += f"\n\n{data['nudge']}"
                
        else:
            ai_message = config.get('fallback_responses', {}).get('no_answer', 
                                   f"⚠️ Error {response.status_code}")
    except requests.exceptions.RequestException as e:
        ai_message = config.get('fallback_responses', {}).get('no_answer', 
                               f"⚠️ Connection error: {e}")

    # Add assistant message
    st.session_state.messages.append({"role": "assistant", "content": ai_message})
    
    # Save conversation after each interaction
    save_conversation_history()
    
    # Check for automatic lead prompt
    if st.session_state.question_count == 3 and not st.session_state.lead_captured:
        nudge_msg = "\n\n💼 I notice you have several questions. Would you like personalized assistance from our loan experts?"
        st.session_state.messages.append({"role": "assistant", "content": nudge_msg})
        save_conversation_history()
    
    st.rerun()

# --- Main Page Content ---
st.markdown("# Welcome to FinanceHub Solutions")
st.markdown("### Your Trusted Partner for All Financial Needs")

# Define page content
page_content = {
    "🏠 Home Loans": {
        "text": """
        **Make Your Dream Home a Reality**
        
        • Lowest interest rates starting at 8.5% p.a.
        • Loan amounts up to ₹5 Crores
        • Flexible tenure up to 30 years
        • Quick approval in 48 hours
        • Minimal documentation
        """,
        "nudge": "🏠 Looking to buy your dream home? I can help calculate your EMI and check eligibility instantly!"
    },
    "💰 Personal Loans": {
        "text": """
        **Instant Personal Loans for Your Needs**
        
        • Get up to ₹40 Lakhs instantly
        • Interest rates from 10.5% p.a.
        • No collateral required
        • Same day disbursal
        • Minimal documentation
        """,
        "nudge": "💳 Need quick funds? Let me check your eligibility in just 30 seconds!"
    },
    "🚗 Car Loans": {
        "text": """
        **Drive Your Dream Car Today**
        
        • 100% on-road funding
        • Interest rates from 9% p.a.
        • Tenure up to 7 years
        • Quick processing
        • Easy EMI options
        """,
        "nudge": "🚗 Ready to buy your dream car? I can help you with the best loan options and instant EMI calculation!"
    },
    "💼 Business Loans": {
        "text": """
        **Grow Your Business with Easy Financing**
        
        • Collateral-free loans up to ₹50 Lakhs
        • Interest rates from 12% p.a.
        • Quick disbursal in 3 days
        • Flexible repayment options
        • Dedicated relationship manager
        """,
        "nudge": "📈 Want to expand your business? Let's discuss the best loan options tailored for your needs!"
    }
}

# Create tabs
tabs = st.tabs(list(page_content.keys()))

# Process each tab
for idx, (tab, (tab_name, content)) in enumerate(zip(tabs, page_content.items())):
    with tab:
        # Initialize tab timer when first visiting this tab
        if tab_name not in st.session_state.tab_visit_time:
            st.session_state.tab_visit_time[tab_name] = time.time()
        
        # Display content
        st.markdown(content["text"])
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📊 Calculate EMI", key=f"emi_{tab_name}"):
                st.session_state.user_intent_score += 3
                st.session_state.focus_chat = True
                st.session_state.last_activity_time = time.time()
                save_conversation_history()
                st.rerun()
        with col2:
            if st.button("✅ Check Eligibility", key=f"elig_{tab_name}"):
                st.session_state.user_intent_score += 3
                st.session_state.focus_chat = True
                st.session_state.last_activity_time = time.time()
                save_conversation_history()
                st.rerun()
        with col3:
            if st.button("📄 Required Documents", key=f"docs_{tab_name}"):
                st.session_state.user_intent_score += 2
                st.session_state.focus_chat = True
                st.session_state.last_activity_time = time.time()
                save_conversation_history()
                st.rerun()
        
        st.markdown("---")
        
        # Create unique keys for nudge state
        nudge_dismissed_key = f"nudge_dismissed_{tab_name}"
        
        # Initialize nudge state if not exists
        if nudge_dismissed_key not in st.session_state.nudge_dismissed:
            st.session_state.nudge_dismissed[nudge_dismissed_key] = False
        
        # Calculate time spent on this tab (from page load, not tab visit)
        time_since_page_load = time.time() - st.session_state.page_load_time
        
        # Show nudge logic
        if not st.session_state.nudge_dismissed[nudge_dismissed_key]:
            if time_since_page_load >= NUDGE_DELAY_SECONDS:
                # Show the nudge
                st.success(content["nudge"])
                
                # Nudge action buttons
                col1, col2, col3 = st.columns([1, 1, 5])
                with col1:
                    if st.button("💬 Chat Now", key=f"chat_btn_{tab_name}"):
                        st.session_state.focus_chat = True
                        st.session_state.user_intent_score += 1
                        st.session_state.last_activity_time = time.time()
                        save_conversation_history()
                        st.rerun()
                with col2:
                    if st.button("Dismiss", key=f"dismiss_btn_{tab_name}"):
                        st.session_state.nudge_dismissed[nudge_dismissed_key] = True
                        st.session_state.last_activity_time = time.time()
                        save_conversation_history()
                        st.rerun()
            else:
                # Show countdown
                remaining_time = NUDGE_DELAY_SECONDS - int(time_since_page_load)
                if remaining_time > 0:
                    # Create an empty container for auto-refresh
                    placeholder = st.empty()
                    with placeholder.container():
                        st.info(f"💡 Want to know more? Chat option available in {remaining_time} seconds...")
                    
                    # Auto-refresh every second
                    time.sleep(1)
                    st.rerun()

# Analytics Dashboard
with st.expander("📊 Session Analytics & History"):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Questions Asked", st.session_state.question_count)
    
    with col2:
        user_type = "Hot Lead" if st.session_state.user_intent_score > 5 else "Warm Lead" if st.session_state.user_intent_score > 0 else "Browsing"
        st.metric("User Type", user_type)
    
    with col3:
        st.metric("Intent Score", st.session_state.user_intent_score)
    
    with col4:
        st.metric("Lead Captured", "Yes" if st.session_state.lead_captured else "No")
    
    # Show interaction log if available
    if st.session_state.interaction_log:
        st.markdown("### Recent Interactions")
        for log in st.session_state.interaction_log[-5:]:
            st.text(f"• {log['query'][:50]}... (Score: +{log['intent_score']})")
    
    # Button to manually save conversation
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("💾 Save Conversation"):
            if save_conversation_history():
                st.success("Conversation saved!")
            else:
                st.error("Failed to save conversation")
    
    with col2:
        if st.button("🗑️ Clear History"):
            st.session_state.messages = []
            st.session_state.question_count = 0
            st.session_state.user_intent_score = 0
            st.session_state.interaction_log = []
            st.session_state.lead_captured = False
            st.session_state.nudge_shown = {}
            st.session_state.nudge_dismissed = {}
            st.session_state.tab_visit_time = {}
            st.session_state.page_load_time = time.time()
            save_conversation_history()
            st.rerun()
    
    # Show saved conversations count
    try:
        with open('conversation_history.json', 'r') as f:
            conversations = json.load(f)
            st.markdown(f"**Total saved conversations:** {len(conversations)}")
    except:
        st.markdown("**No saved conversations yet**")