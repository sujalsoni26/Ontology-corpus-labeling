"""
google_oauth.py
Google OAuth authentication helper for Streamlit
"""

import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import json
import os
from pathlib import Path

# Allow OAuth over HTTP for local development (localhost only)
# WARNING: Never use this in production with a public domain
# On Hugging Face Spaces, SPACE_ID environment variable is set
if os.getenv('SPACE_ID') is None:  # Not on HF Spaces - local development
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# OAuth 2.0 configuration
SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']

def get_redirect_uri():
    """
    Get the appropriate redirect URI based on environment.
    
    Returns:
        str: Redirect URI for OAuth
    """
    # Check if running on Hugging Face Spaces
    if os.getenv('SPACE_ID'):
        space_author = os.getenv('SPACE_AUTHOR_NAME')
        space_name = os.getenv('SPACE_REPO_NAME')
        # Use the direct app URL (not the Space URL which shows code)
        # Format: https://SPACE_AUTHOR-SPACE_NAME.hf.space
        space_url = f"https://{space_author}-{space_name}.hf.space"
        return space_url
    
    # Check if explicitly set in environment
    if os.getenv('GOOGLE_REDIRECT_URI'):
        return os.getenv('GOOGLE_REDIRECT_URI')
    
    # Default to localhost for development
    return "http://localhost:8501"

def get_google_oauth_config():
    """
    Get Google OAuth configuration from Streamlit secrets or environment variables.
    
    Returns:
        dict: OAuth configuration with client_id and client_secret
    """
    # Get dynamic redirect URI
    default_redirect = get_redirect_uri()
    
    # Try to get from Streamlit secrets first
    if hasattr(st, 'secrets') and 'google_oauth' in st.secrets:
        return {
            'client_id': st.secrets['google_oauth']['client_id'],
            'client_secret': st.secrets['google_oauth']['client_secret'],
            'redirect_uri': st.secrets['google_oauth'].get('redirect_uri', default_redirect)
        }
    
    # Fallback to environment variables
    return {
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'redirect_uri': default_redirect
    }

def create_oauth_flow(redirect_uri=None):
    """
    Create Google OAuth flow.
    
    Args:
        redirect_uri: Optional redirect URI override
        
    Returns:
        Flow: Google OAuth flow object
    """
    config = get_google_oauth_config()
    
    if not config['client_id'] or not config['client_secret']:
        raise ValueError("Google OAuth credentials not configured. Please set up secrets.toml or environment variables.")
    
    # Create client config
    client_config = {
        "web": {
            "client_id": config['client_id'],
            "client_secret": config['client_secret'],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri or config['redirect_uri']]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri or config['redirect_uri']
    )
    
    return flow

def get_authorization_url():
    """
    Get Google OAuth authorization URL.
    
    Returns:
        str: Authorization URL to redirect user to
    """
    flow = create_oauth_flow()
    
    # Generate authorization URL
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='select_account'
    )
    
    # Store state in session for verification
    st.session_state.oauth_state = state
    
    return authorization_url

def handle_oauth_callback(authorization_response):
    """
    Handle OAuth callback and exchange code for tokens.
    
    Args:
        authorization_response: Full callback URL with code
        
    Returns:
        dict: User info (email, name, picture)
    """
    flow = create_oauth_flow()
    
    # Exchange authorization code for tokens
    flow.fetch_token(authorization_response=authorization_response)
    
    # Get credentials
    credentials = flow.credentials
    
    # Get user info
    import requests
    user_info_response = requests.get(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers={'Authorization': f'Bearer {credentials.token}'}
    )
    
    user_info = user_info_response.json()
    
    return {
        'email': user_info.get('email'),
        'name': user_info.get('name'),
        'picture': user_info.get('picture'),
        'google_id': user_info.get('id')
    }

def create_secrets_template():
    """
    Create a template .streamlit/secrets.toml file for Google OAuth configuration.
    """
    secrets_dir = Path('.streamlit')
    secrets_dir.mkdir(exist_ok=True)
    
    secrets_file = secrets_dir / 'secrets.toml'
    
    if not secrets_file.exists():
        template = """# Google OAuth Configuration
[google_oauth]
client_id = "YOUR_CLIENT_ID.apps.googleusercontent.com"
client_secret = "YOUR_CLIENT_SECRET"
redirect_uri = "http://localhost:8501"  # Change for production
"""
        secrets_file.write_text(template)
        print(f"Created secrets template at {secrets_file}")
        print("Please update with your Google OAuth credentials.")
    else:
        print(f"Secrets file already exists at {secrets_file}")