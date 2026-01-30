"""
pages/login.py
Login page for the Property Sentence Labeler application.
"""

import streamlit as st
import os
from database import create_user

def render_login_page():
    """Render the login page with username and Google OAuth options."""
    
    st.title("🏷️ Property Sentence Labeler")
    st.markdown("Label sentences with property-specific categories. Navigate through sentences and assign labels.")
    st.markdown("---")
    
    st.markdown("### 🔐 Login to Continue")
    st.markdown("Please choose a login method to access the labeling interface.")
    
    # Google OAuth Login Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            from google_oauth import get_authorization_url
            
            if st.button("🔐 Login with Google", type="primary", use_container_width=True, key="google_login_btn"):
                # Get Google OAuth URL
                auth_url = get_authorization_url()
                
                # Display link and instructions
                st.markdown(f"""
                ### Click the link below to login with Google:
                
                [🔗 Login with Google]({auth_url})
                
                After logging in, you'll be redirected back to this page.
                """)
                
                # Store that we're waiting for OAuth callback
                st.session_state.awaiting_oauth = True
                
        except Exception as e:
            st.warning(f"Google OAuth not configured: {e}")
            st.info("💡 To enable Google login, add your credentials to `.streamlit/secrets.toml`")
    
    st.markdown("---")
    st.markdown("#### Or login with username and password")
    
    # Traditional username + password login
    with st.form("login_form"):
        username = st.text_input(
            "Username",
            placeholder="Enter your username",
            help="Your username will be used to track your labeling progress"
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            help="For new users, this will be your password. For existing users, enter your password to login."
        )
        submitted = st.form_submit_button("Login", type="secondary", use_container_width=True)
        
        if submitted:
            if username and username.strip() and password:
                username = username.strip()
                
                # Check if user exists
                from database import get_user, authenticate_user, create_user
                existing_user = get_user(username)
                
                if existing_user:
                    # User exists - authenticate
                    user_id = authenticate_user(username, password)
                    if user_id:
                        # Successful login
                        st.session_state.user_id = user_id
                        st.session_state.username = username
                        st.success(f"✅ Welcome back, {username}!")
                        st.rerun()
                    else:
                        # Wrong password
                        st.error("❌ Incorrect password. Please try again.")
                else:
                    # New user - create account
                    try:
                        user_id = create_user(username, password)
                        st.session_state.user_id = user_id
                        st.session_state.username = username
                        st.success(f"✅ Account created! Welcome, {username}!")
                        st.rerun()
                    except ValueError as e:
                        st.error(f"❌ Error creating account: {e}")
            else:
                st.warning("⚠️ Please enter both username and password")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>Built with Streamlit • Ready for Hugging Face Spaces</div>",
        unsafe_allow_html=True
    )


def handle_oauth_callback():
    """Handle OAuth callback from Google."""
    try:
        from google_oauth import handle_oauth_callback as process_callback
        from database import create_oauth_user
        import urllib.parse
        
        # Get query parameters
        query_params = st.query_params
        
        # Check if this is an OAuth callback
        if 'code' in query_params and st.session_state.user_id is None:
            try:
                # Get the full callback URL
                code = query_params['code']
                state = query_params.get('state', '')
                
                # Construct the authorization response URL
                # Detect base URL dynamically
                if os.getenv('SPACE_ID'):  # Running on HF Spaces
                    space_author = os.getenv('SPACE_AUTHOR_NAME')
                    space_name = os.getenv('SPACE_REPO_NAME')
                    base_url = f"https://{space_author}-{space_name}.hf.space"
                else:  # Local development
                    base_url = "http://localhost:8501"
                auth_response = f"{base_url}/?code={code}&state={state}"
                
                # Handle the callback
                user_info = process_callback(auth_response)
                
                # Use email as username
                username = user_info['email']
                
                # Create or get OAuth user (with placeholder password)
                user_id = create_oauth_user(username)
                st.session_state.user_id = user_id
                st.session_state.username = username
                st.session_state.google_user_info = user_info
                
                # Clear OAuth state
                if hasattr(st.session_state, 'oauth_state'):
                    del st.session_state.oauth_state
                if hasattr(st.session_state, 'awaiting_oauth'):
                    del st.session_state.awaiting_oauth
                
                # Clear query parameters and reload
                st.query_params.clear()
                st.success(f"✅ Logged in with Google as {username}")
                st.rerun()
                    
            except Exception as e:
                st.error(f"OAuth login failed: {e}")
                st.info("Please try the username login method instead.")
                
    except ImportError:
        pass  # Google OAuth not available
