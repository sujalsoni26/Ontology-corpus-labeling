"""
components.py
Reusable UI components for the Streamlit sentence labeling app.
"""

import streamlit as st
from typing import Dict, List, Optional
from utils import calculate_stats, CODE_TO_LABEL_DISPLAY


def render_property_header(prop: str, domain: str, range_val: str, 
                          property_iri: str = None, domain_iri: str = None, range_iri: str = None):
    """
    Render the property header with domain and range information.
    Makes property, domain, and range names clickable if IRIs are provided.
    
    Args:
        prop: Property name
        domain: Domain class name
        range_val: Range class name
        property_iri: Optional IRI/URL for the property
        domain_iri: Optional IRI/URL for the domain class
        range_iri: Optional IRI/URL for the range class
    """
    # Render property name (clickable if IRI exists)
    if property_iri:
        st.markdown(f"### **[{prop}]({property_iri})** 🔗", unsafe_allow_html=True)
    else:
        st.markdown(f"### **{prop}**")
    
    # Render domain and range in columns
    col1, col2 = st.columns(2)
    
    with col1:
        if domain_iri:
            st.markdown(f"**Domain:** [{domain}]({domain_iri}) 🔗", unsafe_allow_html=True)
        else:
            st.markdown(f"**Domain:** {domain}")
    
    with col2:
        if range_iri:
            st.markdown(f"**Range:** [{range_val}]({range_iri}) 🔗", unsafe_allow_html=True)
        else:
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
        st.sidebar.metric("Sentences Labeled", stats.get("sentences_labeled", 0))
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

def render_word_selection_interface(sentence: str, selected_subject: List[int], 
                                   selected_object: List[int],
                                   key_prefix: str = "word_sel",
                                   session_state_key: tuple = None):
    """
    Render token-based word selection interface with Subject/Object modes.
    Uses first/last word selection for multi-word spans.
    
    Args:
        sentence: The sentence to tokenize and display
        selected_subject: List of word indices selected as subject
        selected_object: List of word indices selected as object
        key_prefix: Unique key prefix for this instance
        session_state_key: Tuple of (prop, sentence) to update session state directly
        
    Returns:
        Tuple of (selection_mode, updated_subject, updated_object)
    """
    # Tokenize sentence into words
    words = sentence.split()
    
    # Selection mode buttons
    st.markdown("#### 🎯 Word Selection Mode")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        subject_mode = st.button("📘 Subject", key=f"{key_prefix}_subject_btn", 
                                use_container_width=True,
                                type="primary" if st.session_state.get(f"{key_prefix}_mode") == "subject" else "secondary")
    with col2:
        object_mode = st.button("📙 Object", key=f"{key_prefix}_object_btn",
                               use_container_width=True,
                               type="primary" if st.session_state.get(f"{key_prefix}_mode") == "object" else "secondary")
    with col3:
        clear_mode = st.button("🔄 Clear Mode", key=f"{key_prefix}_clear_btn",
                              use_container_width=True)
    
    # Update selection mode
    if subject_mode:
        st.session_state[f"{key_prefix}_mode"] = "subject"
        st.session_state[f"{key_prefix}_first_word"] = None  # Reset first word
        st.rerun()
    elif object_mode:
        st.session_state[f"{key_prefix}_mode"] = "object"
        st.session_state[f"{key_prefix}_first_word"] = None  # Reset first word
        st.rerun()
    elif clear_mode:
        st.session_state[f"{key_prefix}_mode"] = None
        st.session_state[f"{key_prefix}_first_word"] = None
        st.rerun()
    
    current_mode = st.session_state.get(f"{key_prefix}_mode")
    first_word_idx = st.session_state.get(f"{key_prefix}_first_word")
    
    # Display current mode with instructions
    if current_mode:
        mode_labels = {"subject": "📘 Subject", "object": "📙 Object"}
        if first_word_idx is None:
            st.info(f"**Active Mode:** {mode_labels.get(current_mode)} - Click the **first word** of the span")
        else:
            st.info(f"**Active Mode:** {mode_labels.get(current_mode)} - Click the **last word** of the span (First word: '{words[first_word_idx]}')")
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
    
    /* First word indicator - Yellow border */
    .first-word-indicator {
        border: 3px solid #FFD700 !important;
        box-shadow: 0 0 10px rgba(255, 215, 0, 0.5) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Render clickable word tokens
    st.markdown("#### Sentence (Click first word, then last word)")
    
    # Render words as buttons in columns
    cols = st.columns(min(len(words), 10))  # Max 10 columns per row
    
    for idx, word in enumerate(words):
        col_idx = idx % 10
        
        # Determine button style and color based on selection
        is_subject = idx in selected_subject
        is_object = idx in selected_object
        is_first_word = (first_word_idx == idx)
        
        # Create button with appropriate styling
        if is_subject:
            button_label = word
            button_type = "primary"
            css_class = "subject-word"
            bg_color = "#4A90E2"  # Blue
        elif is_object:
            button_label = word
            button_type = "primary"
            css_class = "object-word"
            bg_color = "#FF8C42"  # Orange
        else:
            button_label = word
            button_type = "secondary"
            css_class = "unselected-word"
            bg_color = None
        
        with cols[col_idx]:
            # Use markdown with colored background for selected words
            if is_subject or is_object:
                # Add yellow border if this is the first word
                border_style = "border: 3px solid #FFD700; box-shadow: 0 0 10px rgba(255, 215, 0, 0.5);" if is_first_word else ""
                
                # Display colored badge
                st.markdown(f"""
                <div style="background-color: {bg_color}; color: white; padding: 8px 12px; 
                            border-radius: 6px; text-align: center; margin-bottom: 4px; 
                            font-weight: 500; cursor: pointer; {border_style}">
                    {word}
                </div>
                """, unsafe_allow_html=True)
            elif is_first_word:
                # Show first word indicator for unselected words
                st.markdown(f"""
                <div style="background-color: #FFF9C4; color: #333; padding: 8px 12px; 
                            border: 3px solid #FFD700; border-radius: 6px; text-align: center; 
                            margin-bottom: 4px; font-weight: 500; cursor: pointer;
                            box-shadow: 0 0 10px rgba(255, 215, 0, 0.5);">
                    {word} (First)
                </div>
                """, unsafe_allow_html=True)
            
            # Always render the button
            button_display = f"✓ {word}" if (is_subject or is_object) else (f"→ {word}" if is_first_word else word)
            if st.button(button_display, 
                        key=f"{key_prefix}_word_{idx}", 
                        type=button_type, 
                        use_container_width=True,
                        disabled=False):
                # Handle word click based on current mode
                if session_state_key and current_mode:
                    prop, sentence = session_state_key
                    current_selections = st.session_state.word_selections[prop][sentence]
                    
                    if first_word_idx is None:
                        # First click - store the first word index
                        st.session_state[f"{key_prefix}_first_word"] = idx
                        st.rerun()
                    else:
                        # Second click - select range from first to last
                        start_idx = min(first_word_idx, idx)
                        end_idx = max(first_word_idx, idx)
                        
                        # Create range of indices
                        selected_range = list(range(start_idx, end_idx + 1))
                        
                        if current_mode == "subject":
                            # Check if clicking on already selected subject words
                            if all(i in current_selections["subject"] for i in selected_range):
                                # Deselect the range
                                for i in selected_range:
                                    if i in current_selections["subject"]:
                                        current_selections["subject"].remove(i)
                            else:
                                # Select the range and remove from object
                                current_selections["subject"] = sorted(list(set(current_selections["subject"] + selected_range)))
                                # Remove from object if any overlap
                                for i in selected_range:
                                    if i in current_selections["object"]:
                                        current_selections["object"].remove(i)
                        
                        elif current_mode == "object":
                            # Check if clicking on already selected object words
                            if all(i in current_selections["object"] for i in selected_range):
                                # Deselect the range
                                for i in selected_range:
                                    if i in current_selections["object"]:
                                        current_selections["object"].remove(i)
                            else:
                                # Select the range and remove from subject
                                current_selections["object"] = sorted(list(set(current_selections["object"] + selected_range)))
                                # Remove from subject if any overlap
                                for i in selected_range:
                                    if i in current_selections["subject"]:
                                        current_selections["subject"].remove(i)
                        
                        # Update session state
                        st.session_state.word_selections[prop][sentence] = current_selections
                        
                        # Reset first word
                        st.session_state[f"{key_prefix}_first_word"] = None
                        st.rerun()
        
        # Start new row after 10 words
        if (idx + 1) % 10 == 0 and idx + 1 < len(words):
            cols = st.columns(min(len(words) - idx - 1, 10))
    
    # Display selected words summary
    st.markdown("---")
    st.markdown("#### Selected Words Summary")
    
    col1, col2 = st.columns(2)
    with col1:
        subject_words = [words[i] for i in sorted(selected_subject)]
        st.markdown(f"**📘 Subject:** {' '.join(subject_words) if subject_words else '(none)'}")
    with col2:
        object_words = [words[i] for i in sorted(selected_object)]
        st.markdown(f"**📙 Object:** {' '.join(object_words) if object_words else '(none)'}")
    
    return current_mode, selected_subject, selected_object