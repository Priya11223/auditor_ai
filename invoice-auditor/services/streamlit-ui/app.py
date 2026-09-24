"""
Streamlit UI - Main Application

Entry point for the Streamlit dashboard.
Sets up page configuration and sidebar navigation.
"""

import streamlit as st

from views.inbox import render_inbox
from views.review import render_review

# Configure the page
st.set_page_config(
    page_title="Invoice Auditor AI",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar Navigation
with st.sidebar:
    st.title("🧾 AI Auditor")
    st.markdown("---")
    
    # We use session state to track the current page, 
    # though for Phase 13 we only have one page.
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Inbox"
        
    if st.button("📥 Inbox", use_container_width=True):
        st.session_state.current_page = "Inbox"
        
        
    if st.button("🔍 Review Document", use_container_width=True):
        st.session_state.current_page = "Review"

# Route to the correct view
if st.session_state.current_page == "Inbox":
    render_inbox()
elif st.session_state.current_page == "Review":
    render_review()
