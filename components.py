"""
components.py
Reusable UI components for the Streamlit sentence labeling app.
"""

import streamlit as st
from typing import Dict, List, Optional
from utils import calculate_stats, CODE_TO_LABEL_DISPLAY


def render_property_header(prop: str, domain: str, range_val: str):
    """Render the property header with domain and range information."""
    st.markdown(f"### **{prop}**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Domain:** {domain}")
    with col2:
        st.markdown(f"**Range:** {range_val}")

def render_progress_stats(current_idx: int, texts: List[str], labels: Dict[str, str]):
    """Render progress and statistics information."""
    total = len(texts)
    labeled, _, percentage = calculate_stats(texts, labels)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.info(f"**Progress:** {current_idx + 1} / {total}")
    with col2:
        st.success(f"**Labeled:** {labeled} / {total} ({percentage}%)")

def render_sentence_display(sentence: str):
    """Render the current sentence in a prominent display."""
    st.markdown("#### Sentence to Label")
    st.text_area(
        label="Current Sentence",
        value=sentence,
        height=150,
        disabled=True,
        label_visibility="collapsed"
    )

def render_label_selector(current_label: str, label_choices: List[str], key: str = "label_radio"):
    """
    Render the label selection radio buttons.
    Returns the selected label display text.
    """
    # Convert code to display if current_label is a code
    if current_label and current_label in CODE_TO_LABEL_DISPLAY:
        current_display = CODE_TO_LABEL_DISPLAY[current_label]
    else:
        current_display = current_label if current_label in label_choices else None
    
    selected = st.radio(
        label="Select Label",
        options=label_choices,
        index=label_choices.index(current_display) if current_display in label_choices else None,
        key=key
    )
    
    return selected

def render_navigation_buttons():
    """
    Render navigation buttons and return which button was clicked.
    Returns: tuple (prev, next, jump_prev, jump_next)
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        prev = st.button("⬅️ Previous", use_container_width=True)
    with col2:
        next_btn = st.button("Next ➡️", use_container_width=True)
    with col3:
        jump_prev = st.button("⏮️ Jump Prev Unlabeled", use_container_width=True)
    with col4:
        jump_next = st.button("Jump Next Unlabeled ⏭️", use_container_width=True)
    
    return prev, next_btn, jump_prev, jump_next

def render_legend():
    """Render the label legend."""
    with st.expander("📖 Label Legend", expanded=False):
        st.markdown("""
**Legend → code mapping**
- i. Full alignment p(D, R) → `pdr`  
- ii. Correct Domain p(D, ?) → `pd`  
- iii. Correct Range p(?, R) → `pr`  
- iv. Incorrect D & R p(?, ?) → `p`  
- v. No alignment → `n`
        """)

def render_login_form() -> Optional[str]:
    """
    Render login form with username and Google OAuth options.
    
    Returns:
        Username if form submitted, None otherwise
    """
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
    st.markdown("#### Or login with username")
    
    # Traditional username login
    with st.form("login_form"):
        username = st.text_input(
            "Username",
            placeholder="Enter your username",
            help="Your username will be used to track your labeling progress"
        )
        submitted = st.form_submit_button("Login with Username", type="secondary", use_container_width=True)
        
        if submitted:
            if username and username.strip():
                return username.strip()
            else:
                st.error("Please enter a valid username")
                return None
    
    return None

def render_user_info(username: str, stats: Dict):
    """
    Render current user information and logout button.
    
    Args:
        username: Current logged-in username
        stats: User statistics dictionary
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("👤 User Info")
    
    st.sidebar.markdown(f"**Logged in as:** {username}")
    
    if stats:
        st.sidebar.metric("Total Labels", stats.get("total_labels", 0))
        st.sidebar.metric("Properties Labeled", stats.get("properties_count", 0))
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

def render_word_selection_interface(sentence: str, selected_subject: List[int], 
                                   selected_property: List[int], selected_object: List[int],
                                   key_prefix: str = "word_sel",
                                   session_state_key: tuple = None):
    """
    Render token-based word selection interface with Subject/Property/Object modes.
    
    Args:
        sentence: The sentence to tokenize and display
        selected_subject: List of word indices selected as subject
        selected_property: List of word indices selected as property
        selected_object: List of word indices selected as object
        key_prefix: Unique key prefix for this instance
        session_state_key: Tuple of (prop, sentence) to update session state directly
        
    Returns:
        Tuple of (selection_mode, updated_subject, updated_property, updated_object)
    """
    # Tokenize sentence into words
    words = sentence.split()
    
    # Selection mode buttons
    st.markdown("#### 🎯 Word Selection Mode")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        subject_mode = st.button("📘 Subject", key=f"{key_prefix}_subject_btn", 
                                use_container_width=True,
                                type="primary" if st.session_state.get(f"{key_prefix}_mode") == "subject" else "secondary")
    with col2:
        property_mode = st.button("📗 Property", key=f"{key_prefix}_property_btn",
                                 use_container_width=True,
                                 type="primary" if st.session_state.get(f"{key_prefix}_mode") == "property" else "secondary")
    with col3:
        object_mode = st.button("📙 Object", key=f"{key_prefix}_object_btn",
                               use_container_width=True,
                               type="primary" if st.session_state.get(f"{key_prefix}_mode") == "object" else "secondary")
    with col4:
        clear_mode = st.button("🔄 Clear Mode", key=f"{key_prefix}_clear_btn",
                              use_container_width=True)
    
    # Update selection mode
    if subject_mode:
        st.session_state[f"{key_prefix}_mode"] = "subject"
        st.rerun()
    elif property_mode:
        st.session_state[f"{key_prefix}_mode"] = "property"
        st.rerun()
    elif object_mode:
        st.session_state[f"{key_prefix}_mode"] = "object"
        st.rerun()
    elif clear_mode:
        st.session_state[f"{key_prefix}_mode"] = None
        st.rerun()
    
    current_mode = st.session_state.get(f"{key_prefix}_mode")
    
    # Display current mode
    if current_mode:
        mode_labels = {"subject": "📘 Subject", "property": "📗 Property", "object": "📙 Object"}
        st.info(f"**Active Mode:** {mode_labels.get(current_mode)} - Click words to select/deselect")
    else:
        st.info("**Select a mode above to start marking words**")
    
    # Add custom CSS for colored buttons
    st.markdown("""
    <style>
    /* Subject buttons - Blue */
    div[data-testid="column"] button[kind="primary"].subject-btn {
        background-color: #4A90E2 !important;
        border-color: #4A90E2 !important;
        color: white !important;
    }
    div[data-testid="column"] button[kind="primary"].subject-btn:hover {
        background-color: #357ABD !important;
        border-color: #357ABD !important;
    }
    
    /* Property buttons - Green */
    div[data-testid="column"] button[kind="primary"].property-btn {
        background-color: #50C878 !important;
        border-color: #50C878 !important;
        color: white !important;
    }
    div[data-testid="column"] button[kind="primary"].property-btn:hover {
        background-color: #3DA35D !important;
        border-color: #3DA35D !important;
    }
    
    /* Object buttons - Orange */
    div[data-testid="column"] button[kind="primary"].object-btn {
        background-color: #FF8C42 !important;
        border-color: #FF8C42 !important;
        color: white !important;
    }
    div[data-testid="column"] button[kind="primary"].object-btn:hover {
        background-color: #E67A35 !important;
        border-color: #E67A35 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Render clickable word tokens
    st.markdown("#### Sentence (Click words to select)")
    
    # Render words as buttons in columns
    cols = st.columns(min(len(words), 10))  # Max 10 columns per row
    
    for idx, word in enumerate(words):
        col_idx = idx % 10
        
        # Determine button style and color based on selection
        is_subject = idx in selected_subject
        is_property = idx in selected_property
        is_object = idx in selected_object
        
        # Create button with appropriate styling
        if is_subject:
            # Blue background for subject
            button_label = word
            button_type = "primary"
            # Add CSS class identifier in the key
            css_class = "subject-word"
        elif is_property:
            # Green background for property
            button_label = word
            button_type = "primary"
            css_class = "property-word"
        elif is_object:
            # Orange background for object
            button_label = word
            button_type = "primary"
            css_class = "object-word"
        else:
            button_label = word
            button_type = "secondary"
            css_class = "unselected-word"
        
        with cols[col_idx]:
            # Use markdown with colored background for selected words
            if is_subject or is_property or is_object:
                # Determine color
                if is_subject:
                    bg_color = "#4A90E2"  # Blue
                elif is_property:
                    bg_color = "#50C878"  # Green
                else:  # is_object
                    bg_color = "#FF8C42"  # Orange
                
                # Display colored badge
                st.markdown(f"""
                <div style="background-color: {bg_color}; color: white; padding: 8px 12px; 
                            border-radius: 6px; text-align: center; margin-bottom: 4px; 
                            font-weight: 500; cursor: pointer;">
                    {word}
                </div>
                """, unsafe_allow_html=True)
            
            # Always render the button (invisible if colored badge shown)
            if st.button(button_label if not (is_subject or is_property or is_object) else f"✓ {word}", 
                        key=f"{key_prefix}_word_{idx}", 
                        type=button_type, 
                        use_container_width=True,
                        disabled=False):
                # Handle word click based on current mode
                # Update session state BEFORE rerun
                if session_state_key and current_mode:
                    prop, sentence = session_state_key
                    current_selections = st.session_state.word_selections[prop][sentence]
                    
                    if current_mode == "subject":
                        if idx in current_selections["subject"]:
                            current_selections["subject"].remove(idx)
                        else:
                            current_selections["subject"].append(idx)
                            # Remove from other categories
                            if idx in current_selections["property"]:
                                current_selections["property"].remove(idx)
                            if idx in current_selections["object"]:
                                current_selections["object"].remove(idx)
                        
                    elif current_mode == "property":
                        if idx in current_selections["property"]:
                            current_selections["property"].remove(idx)
                        else:
                            current_selections["property"].append(idx)
                            # Remove from other categories
                            if idx in current_selections["subject"]:
                                current_selections["subject"].remove(idx)
                            if idx in current_selections["object"]:
                                current_selections["object"].remove(idx)
                        
                    elif current_mode == "object":
                        if idx in current_selections["object"]:
                            current_selections["object"].remove(idx)
                        else:
                            current_selections["object"].append(idx)
                            # Remove from other categories
                            if idx in current_selections["subject"]:
                                current_selections["subject"].remove(idx)
                            if idx in current_selections["property"]:
                                current_selections["property"].remove(idx)
                    
                    # Update session state
                    st.session_state.word_selections[prop][sentence] = current_selections
                
                st.rerun()
        
        # Start new row after 10 words
        if (idx + 1) % 10 == 0 and idx + 1 < len(words):
            cols = st.columns(min(len(words) - idx - 1, 10))
    
    # Display selected words summary
    st.markdown("---")
    st.markdown("#### Selected Words Summary")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        subject_words = [words[i] for i in sorted(selected_subject)]
        st.markdown(f"**📘 Subject:** {' '.join(subject_words) if subject_words else '(none)'}")
    with col2:
        property_words_list = [words[i] for i in sorted(selected_property)]
        st.markdown(f"**📗 Property:** {' '.join(property_words_list) if property_words_list else '(none)'}")
    with col3:
        object_words = [words[i] for i in sorted(selected_object)]
        st.markdown(f"**📙 Object:** {' '.join(object_words) if object_words else '(none)'}")
    
    return current_mode, selected_subject, selected_property, selected_object