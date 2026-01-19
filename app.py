"""
app.py
Main Streamlit application for property sentence labeling.
"""

import streamlit as st
import json
from pathlib import Path
from io import BytesIO

from utils import (
    LABEL_CHOICES,
    LABEL_DISPLAY_TO_CODE,
    normalize_input_data,
    initialize_labels,
    load_existing_labels,
    create_output_object,
    find_first_unlabeled,
    find_next_unlabeled,
    find_prev_unlabeled,
)

from components import (
    render_property_header,
    render_progress_stats,
    render_sentence_display,
    render_label_selector,
    render_navigation_buttons,
    render_legend,
    render_login_form,
    render_user_info,
    render_word_selection_interface,
)

from database import (
    create_user,
    get_user,
    save_label as db_save_label,
    get_user_labels,
    get_user_stats,
)

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
    """Initialize all session state variables."""
    if "data_raw" not in st.session_state:
        st.session_state.data_raw = {}
    if "labels" not in st.session_state:
        st.session_state.labels = {}
    if "word_selections" not in st.session_state:
        st.session_state.word_selections = {}  # {prop: {sentence: {subject: [], property: [], object: []}}}
    if "current_prop" not in st.session_state:
        st.session_state.current_prop = None
    if "indices" not in st.session_state:
        st.session_state.indices = {}
    if "property_list" not in st.session_state:
        st.session_state.property_list = []
    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = None

initialize_session_state()

# ----------------------------
# AUTHENTICATION CHECK
# ----------------------------
if st.session_state.user_id is None:
    # User not logged in - show login page
    st.title("🏷️ Property Sentence Labeler")
    st.markdown("Label sentences with property-specific categories. Navigate through sentences and assign labels.")
    st.markdown("---")
    
    username = render_login_form()
    
    if username:
        # Create or get user
        user_id = create_user(username)
        st.session_state.user_id = user_id
        st.session_state.username = username
        st.success(f"✅ Logged in as {username}")
        st.rerun()
    
    # Stop execution here if not logged in
    st.stop()

# ----------------------------
# SIDEBAR - USER INFO
# ----------------------------
user_stats = get_user_stats(st.session_state.user_id)
render_user_info(st.session_state.username, user_stats)

# ----------------------------
# SIDEBAR - DATA INFO
# ----------------------------
st.sidebar.subheader("Data Source")
st.sidebar.info("**File:** property_text_corpus_full_resolved.json")

# Show dataset statistics if data is loaded
if st.session_state.data_loaded:
    total_sentences = sum(len(st.session_state.data_raw[prop]["texts"]) for prop in st.session_state.property_list)
    st.sidebar.metric("Properties", len(st.session_state.property_list))
    st.sidebar.metric("Total Sentences", total_sentences)

# ----------------------------
# AUTO-LOAD DATA ON FIRST RUN
# ----------------------------
if not st.session_state.data_loaded:
    try:
        # Path to the fixed input file
        input_file_path = Path("/Users/manojk/Desktop/IIIT Delhi/08 IP/Labeling Interface/property_text_corpus_full_resolved.json")
        
        if not input_file_path.exists():
            st.sidebar.error(f"❌ Data file not found: {input_file_path}")
        else:
            # Load and normalize input data
            with open(input_file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            st.session_state.data_raw = normalize_input_data(raw_data)
            st.session_state.property_list = sorted(list(st.session_state.data_raw.keys()))
            
            # Initialize labels structure
            st.session_state.labels = initialize_labels(st.session_state.data_raw)
            
            # Load user's existing labels from database
            db_labels = get_user_labels(st.session_state.user_id)
            
            # Initialize word selections structure
            st.session_state.word_selections = {}
            for prop in st.session_state.property_list:
                st.session_state.word_selections[prop] = {}
            
            # Merge database labels and word selections with initialized labels
            for prop in st.session_state.property_list:
                if prop in db_labels:
                    for sentence, label_data in db_labels[prop].items():
                        if sentence in st.session_state.labels[prop]:
                            # Handle both old format (string) and new format (dict)
                            if isinstance(label_data, str):
                                st.session_state.labels[prop][sentence] = label_data
                            elif isinstance(label_data, dict):
                                st.session_state.labels[prop][sentence] = label_data.get("label_code", "")
                                
                                # Load word selections
                                subject_str = label_data.get("subject_words", "")
                                property_str = label_data.get("property_words", "")
                                object_str = label_data.get("object_words", "")
                                
                                st.session_state.word_selections[prop][sentence] = {
                                    "subject": [int(i) for i in subject_str.split(",") if i.strip()] if subject_str else [],
                                    "property": [int(i) for i in property_str.split(",") if i.strip()] if property_str else [],
                                    "object": [int(i) for i in object_str.split(",") if i.strip()] if object_str else []
                                }
            
            # Initialize indices for each property (start at first unlabeled)
            st.session_state.indices = {}
            for prop in st.session_state.property_list:
                texts = st.session_state.data_raw[prop]["texts"]
                st.session_state.indices[prop] = find_first_unlabeled(
                    texts,
                    st.session_state.labels[prop]
                )
            
            # Set current property to first one
            if st.session_state.property_list:
                st.session_state.current_prop = st.session_state.property_list[0]
                st.session_state.data_loaded = True
                st.sidebar.success("✅ Data loaded successfully!")
            else:
                st.sidebar.error("❌ No properties found in input JSON")
                st.session_state.data_loaded = False
                
    except Exception as e:
        st.sidebar.error(f"❌ Error loading data: {e}")
        st.session_state.data_loaded = False

# Property selection moved to main section

# ----------------------------
# SIDEBAR - EXPORT
# ----------------------------
if st.session_state.data_loaded:
    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 Export Data")
    
    # Create output object
    output_data = create_output_object(st.session_state.data_raw, st.session_state.labels)
    output_json = json.dumps(output_data, ensure_ascii=False, indent=2)
    
    st.sidebar.download_button(
        label="⬇️ Download Labeled JSON",
        data=output_json,
        file_name="labeled_output.json",
        mime="application/json",
        use_container_width=True
    )

# ----------------------------
# MAIN CONTENT
# ----------------------------
st.title("🏷️ Property Sentence Labeler")
st.markdown("Label sentences with property-specific categories. Navigate through sentences and assign labels.")

if not st.session_state.data_loaded:
    st.info("⏳ Loading data from property_text_corpus_full_resolved.json...")
else:
    # Add scroll anchor at the top of labeling section
    st.markdown('<div id="top-anchor"></div>', unsafe_allow_html=True)
    
    # Property Selection in Main Section
    st.markdown("### 🔍 Select Property")
    selected_prop = st.selectbox(
        "Choose a property to label",
        options=st.session_state.property_list,
        index=st.session_state.property_list.index(st.session_state.current_prop)
        if st.session_state.current_prop in st.session_state.property_list else 0,
        key="property_selector_main"
    )
    
    # Update current property if changed
    if selected_prop != st.session_state.current_prop:
        st.session_state.current_prop = selected_prop
        st.rerun()
    
    # Get current property data
    prop = st.session_state.current_prop
    prop_data = st.session_state.data_raw[prop]
    texts = prop_data["texts"]
    current_idx = st.session_state.indices.get(prop, 0)
    
    # Ensure index is valid
    if current_idx >= len(texts):
        current_idx = len(texts) - 1
        st.session_state.indices[prop] = current_idx
    
    if not texts:
        st.warning(f"No sentences found for property: {prop}")
    else:
        # Render property header
        render_property_header(prop, prop_data["domain"], prop_data["range"])
        
        st.markdown("---")
        
        # Render progress and stats
        render_progress_stats(current_idx, texts, st.session_state.labels[prop])
        
        st.markdown("---")
        
        # Get current sentence and its label
        current_sentence = texts[current_idx]
        current_label = st.session_state.labels[prop].get(current_sentence, "")
        
        # Get current word selections
        if prop not in st.session_state.word_selections:
            st.session_state.word_selections[prop] = {}
        if current_sentence not in st.session_state.word_selections[prop]:
            st.session_state.word_selections[prop][current_sentence] = {
                "subject": [],
                "property": [],
                "object": []
            }
        
        current_selections = st.session_state.word_selections[prop][current_sentence]
        
        # Render sentence display
        render_sentence_display(current_sentence)
        
        # Render label selector with unique key for each sentence
        radio_key = f"label_radio_{prop}_{current_idx}"
        selected_label = render_label_selector(current_label, LABEL_CHOICES, key=radio_key)
        
        st.markdown("---")
        
        # Render word selection interface
        word_sel_key = f"word_sel_{prop}_{current_idx}"
        mode, new_subject, new_property, new_object = render_word_selection_interface(
            current_sentence,
            current_selections["subject"],
            current_selections["property"],
            current_selections["object"],
            key_prefix=word_sel_key,
            session_state_key=(prop, current_sentence)  # Pass key to update session state
        )
        
        # Note: new_subject, new_property, new_object are the SAME as current_selections
        # because the component returns what was passed in. The actual updates happen
        # via st.rerun() inside the component when buttons are clicked.
        
        # Get the current label code
        current_label_code = st.session_state.labels[prop].get(current_sentence, "")
        
        # Check if label changed
        if selected_label:
            label_code = LABEL_DISPLAY_TO_CODE[selected_label]
            if current_label_code != label_code:
                st.session_state.labels[prop][current_sentence] = label_code
                current_label_code = label_code
        
        # Always save to database with current state
        # (This ensures word selections are saved even if label hasn't changed)
        subject_list = st.session_state.word_selections[prop][current_sentence]["subject"]
        property_list = st.session_state.word_selections[prop][current_sentence]["property"]
        object_list = st.session_state.word_selections[prop][current_sentence]["object"]
        
        # Convert word indices to comma-separated strings
        subject_str = ",".join(map(str, subject_list)) if subject_list else None
        property_str = ",".join(map(str, property_list)) if property_list else None
        object_str = ",".join(map(str, object_list)) if object_list else None
        
        # Save to database (will update if exists, insert if new)
        db_save_label(
            st.session_state.user_id,
            prop,
            current_sentence,
            current_label_code,
            subject_words=subject_str,
            property_words=property_str,
            object_words=object_str
        )
        
        st.markdown("---")
        
        # Navigation buttons
        prev_btn, next_btn, jump_prev_btn, jump_next_btn = render_navigation_buttons()
        
        # Handle navigation
        navigated = False
        
        if prev_btn and current_idx > 0:
            st.session_state.indices[prop] = current_idx - 1
            navigated = True
            st.rerun()
        
        if next_btn and current_idx < len(texts) - 1:
            st.session_state.indices[prop] = current_idx + 1
            navigated = True
            st.rerun()
        
        if jump_prev_btn:
            new_idx = find_prev_unlabeled(texts, st.session_state.labels[prop], current_idx)
            if new_idx != current_idx:
                st.session_state.indices[prop] = new_idx
                navigated = True
                st.rerun()
            else:
                st.info("No previous unlabeled sentence found")
        
        if jump_next_btn:
            new_idx = find_next_unlabeled(texts, st.session_state.labels[prop], current_idx)
            if new_idx != current_idx:
                st.session_state.indices[prop] = new_idx
                navigated = True
                st.rerun()
            else:
                st.info("No next unlabeled sentence found")
        
        # Add JavaScript to scroll to top after page loads (on rerun after navigation)
        st.markdown("""
        <script>
        // Scroll to top anchor
        window.parent.document.getElementById('top-anchor')?.scrollIntoView({behavior: 'smooth', block: 'start'});
        // Alternative: scroll to top of page
        window.parent.scrollTo({top: 0, behavior: 'smooth'});
        </script>
        """, unsafe_allow_html=True)

# ----------------------------
# FOOTER
# ----------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>Built with Streamlit • Ready for Hugging Face Spaces</div>",
    unsafe_allow_html=True
)
