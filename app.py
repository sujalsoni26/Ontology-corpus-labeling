"""
app.py
Main router for the Property Sentence Labeler application.
Handles authentication and delegates to page modules.
"""

import streamlit as st

# Import page modules
from page_modules import render_login_page, handle_oauth_callback, render_home_page

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(
    page_title="Property Sentence Labeler",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------
# SESSION STATE INITIALIZATION
# ----------------------------
def initialize_session_state():
    """Initialize core session state variables."""
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = None

initialize_session_state()

# ----------------------------
# OAUTH CALLBACK HANDLER
# ----------------------------
# Check for OAuth callback in URL parameters
handle_oauth_callback()

# ----------------------------
# ROUTING LOGIC
# ----------------------------
if st.session_state.user_id is None:
    # User not authenticated - show login page
    render_login_page()
else:
    # User authenticated - show home page
    render_home_page()