"""
pages/home.py
Main labeling interface for the Property Sentence Labeler application.
"""

import streamlit as st
import json
from pathlib import Path

from utils import (
    LABEL_CHOICES,
    LABEL_DISPLAY_TO_CODE,
    normalize_input_data,
    initialize_labels,
    find_first_unlabeled,
    find_next_unlabeled,
    find_prev_unlabeled,
    create_output_object,
)

from components import (
    render_property_header,
    render_progress_stats,
    render_sentence_display,
    render_label_selector,
    render_navigation_buttons,
    render_user_info,
    render_word_selection_interface,
)

from database import (
    save_label as db_save_label_new,
    get_user_labels,
    get_user_stats,
    get_property_by_name,
    get_sentences_by_property,
    get_sentence_by_text,
    get_all_properties,
)

from validation import (
    validate_label_completeness,
    get_completion_summary,
)




def initialize_data():
    """Initialize session state variables for the home page."""
    if "data_raw" not in st.session_state:
        st.session_state.data_raw = {}
    if "labels" not in st.session_state:
        st.session_state.labels = {}
    if "word_selections" not in st.session_state:
        st.session_state.word_selections = {}
    if "current_prop" not in st.session_state:
        st.session_state.current_prop = None
    if "indices" not in st.session_state:
        st.session_state.indices = {}
    if "property_list" not in st.session_state:
        st.session_state.property_list = []
    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False


def load_data_from_database():
    """Load data from database (properties and sentences)."""
    if st.session_state.data_loaded:
        return
    
    try:
        from database import get_all_properties, get_sentences_by_property, get_user_labels
        
        # Get all properties from database
        properties = get_all_properties()
        
        if not properties:
            st.sidebar.error("❌ No properties found in database. Please run migration script first.")
            st.session_state.data_loaded = False
            return
        
        # Build data structure similar to JSON format
        st.session_state.data_raw = {}
        st.session_state.property_list = []
        
        for prop in properties:
            prop_name = prop["property_name"]
            st.session_state.property_list.append(prop_name)
            
            # Get sentences for this property
            sentences = get_sentences_by_property(prop["id"])
            
            st.session_state.data_raw[prop_name] = {
                "domain": prop["property_domain"] or "",
                "range": prop["property_range"] or "",
                "texts": [s["sentence"] for s in sentences],
                "property_iri": prop.get("property_iri"),
                "domain_iri": prop.get("domain_iri"),
                "range_iri": prop.get("range_iri")
            }
        
        # Sort property list
        st.session_state.property_list = sorted(st.session_state.property_list)
        
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
                            object_str = label_data.get("object_words", "")
                            
                            st.session_state.word_selections[prop][sentence] = {
                                "subject": [int(i) for i in subject_str.split(",") if i.strip()] if subject_str else [],
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
        else:
            st.sidebar.error("❌ No properties found in database")
            st.session_state.data_loaded = False
            
    except Exception as e:
        st.sidebar.error(f"❌ Error loading data from database: {e}")
        st.session_state.data_loaded = False


def render_sidebar():
    """Render sidebar with user info and export functionality."""
    # User info
    user_stats = get_user_stats(st.session_state.user_id)
    render_user_info(st.session_state.username, user_stats)
    
    # Show dataset statistics if data is loaded
    if st.session_state.data_loaded:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Dataset Statistics")
        total_sentences = sum(len(st.session_state.data_raw[prop]["texts"]) for prop in st.session_state.property_list)
        st.sidebar.metric("Properties", len(st.session_state.property_list))
        st.sidebar.metric("Total Sentences", total_sentences)
    
    # Export functionality
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


def render_labeling_interface():
    """Render the main labeling interface."""
    if not st.session_state.data_loaded:
        st.info("⏳ Loading data from database...")
        return
    
    # Add scroll anchor at the top of labeling section
    st.markdown('<div id="top-anchor"></div>', unsafe_allow_html=True)
    
    # Property Selection
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
        return
    
    # Render property header
    render_property_header(
        prop, 
        prop_data["domain"], 
        prop_data["range"],
        property_iri=prop_data.get("property_iri"),
        domain_iri=prop_data.get("domain_iri"),
        range_iri=prop_data.get("range_iri")
    )
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
    mode, new_subject, new_object = render_word_selection_interface(
        current_sentence,
        current_selections["subject"],
        current_selections["object"],
        key_prefix=word_sel_key,
        session_state_key=(prop, current_sentence)
    )
    
    # Get the current label code
    current_label_code = st.session_state.labels[prop].get(current_sentence, "")
    
    # Check if label changed
    if selected_label:
        label_code = LABEL_DISPLAY_TO_CODE[selected_label]
        if current_label_code != label_code:
            st.session_state.labels[prop][current_sentence] = label_code
            current_label_code = label_code
    
    # Get current word selections
    subject_list = st.session_state.word_selections[prop][current_sentence]["subject"]
    object_list = st.session_state.word_selections[prop][current_sentence]["object"]
    
    # Validate label completeness
    is_valid, error_message = validate_label_completeness(
        current_label_code,
        subject_list,
        object_list
    )
    
    # Display validation feedback
    st.markdown("---")
    st.markdown("#### 📋 Validation Status")
    
    if is_valid:
        st.success("✅ **Label is complete!** This sentence is ready to be saved.")
    elif error_message:
        st.warning(error_message)
    
    # Convert word indices to comma-separated strings for database
    subject_str = ",".join(map(str, subject_list)) if subject_list else None
    object_str = ",".join(map(str, object_list)) if object_list else None
    
    # Save to database with new schema
    # Look up sentence_id from database
    sentence_record = get_sentence_by_text(current_sentence, prop)
    
    if sentence_record:
        sentence_id = sentence_record["id"]
        
        # Save label with validation status
        db_save_label_new(
            user_id=st.session_state.user_id,
            sentence_id=sentence_id,
            label_code=current_label_code if current_label_code else "",
            subject_words=subject_str,
            object_words=object_str,
            is_complete=is_valid
        )
    else:
        # Sentence not found in database - this shouldn't happen if migration ran correctly
        st.error(f"⚠️ Sentence not found in database for property '{prop}'. Please contact admin.")

    
    st.markdown("---")
    
    # Navigation buttons
    prev_btn, next_btn, jump_prev_btn, jump_next_btn = render_navigation_buttons()
    
    # Handle navigation
    if prev_btn and current_idx > 0:
        st.session_state.indices[prop] = current_idx - 1
        st.rerun()
    
    if next_btn and current_idx < len(texts) - 1:
        st.session_state.indices[prop] = current_idx + 1
        st.rerun()
    
    if jump_prev_btn:
        new_idx = find_prev_unlabeled(texts, st.session_state.labels[prop], current_idx)
        if new_idx != current_idx:
            st.session_state.indices[prop] = new_idx
            st.rerun()
        else:
            st.info("No previous unlabeled sentence found")
    
    if jump_next_btn:
        new_idx = find_next_unlabeled(texts, st.session_state.labels[prop], current_idx)
        if new_idx != current_idx:
            st.session_state.indices[prop] = new_idx
            st.rerun()
        else:
            st.info("No next unlabeled sentence found")
    
    # Add JavaScript to scroll to top after page loads
    st.markdown("""
    <script>
    // Scroll to top anchor
    window.parent.document.getElementById('top-anchor')?.scrollIntoView({behavior: 'smooth', block: 'start'});
    // Alternative: scroll to top of page
    window.parent.scrollTo({top: 0, behavior: 'smooth'});
    </script>
    """, unsafe_allow_html=True)


def render_home_page():
    """Main entry point for the home page."""
    # Initialize data structures
    initialize_data()
    
    # Render sidebar
    render_sidebar()
    
    # Load data from database
    load_data_from_database()
    
    # Main content
    st.title("🏷️ Property Sentence Labeler")
    st.markdown("Label sentences with property-specific categories. Navigate through sentences and assign labels.")
    
    # Render labeling interface
    render_labeling_interface()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>Built with Streamlit • Ready for Hugging Face Spaces</div>",
        unsafe_allow_html=True
    )
