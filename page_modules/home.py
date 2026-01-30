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
    CODE_TO_LABEL_DISPLAY,
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
    get_sentence_ids_labeled_by_anyone,
    get_labeled_sentence_stats,
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
    if "show_unlabeled_only" not in st.session_state:
        st.session_state.show_unlabeled_only = True  # Default: show only sentences not labeled by anybody


def get_filtered_property_list():
    """Properties that have at least one sentence to show (all, or only unlabeled-by-anyone)."""
    if not st.session_state.get("show_unlabeled_only"):
        return st.session_state.property_list
    labeled_ids = st.session_state.get("labeled_sentence_ids", set())
    return [
        prop for prop in st.session_state.property_list
        if any(sid not in labeled_ids for sid in st.session_state.data_raw[prop].get("sentence_ids", []))
    ]


def get_filtered_texts(prop: str):
    """Sentence texts to show for a property (all, or only unlabeled-by-anyone)."""
    if not st.session_state.get("show_unlabeled_only"):
        return st.session_state.data_raw[prop]["texts"]
    labeled_ids = st.session_state.get("labeled_sentence_ids", set())
    texts = st.session_state.data_raw[prop]["texts"]
    ids = st.session_state.data_raw[prop].get("sentence_ids", [])
    return [t for t, sid in zip(texts, ids) if sid not in labeled_ids]


def load_data_from_database():
    """Load data from database (properties and sentences)."""
    # If we have cached data but no sentence_ids (e.g. session from before unlabeled-only mode),
    # force a reload so filtering works correctly.
    if st.session_state.data_loaded and st.session_state.property_list:
        first_prop = st.session_state.property_list[0]
        if not st.session_state.data_raw.get(first_prop, {}).get("sentence_ids"):
            st.session_state.data_loaded = False
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
        
        # Build data structure with sentence IDs (for global unlabeled-only filtering)
        st.session_state.data_raw = {}
        st.session_state.property_list = []
        
        for prop in properties:
            prop_name = prop["property_name"]
            st.session_state.property_list.append(prop_name)
            
            # Get sentences for this property (keep ids for filtering)
            sentences = get_sentences_by_property(prop["id"])
            
            st.session_state.data_raw[prop_name] = {
                "domain": prop["property_domain"] or "",
                "range": prop["property_range"] or "",
                "texts": [s["sentence"] for s in sentences],
                "sentence_ids": [s["id"] for s in sentences],
                "property_iri": prop.get("property_iri"),
                "domain_iri": prop.get("domain_iri"),
                "range_iri": prop.get("range_iri")
            }
        
        # Sort property list
        st.session_state.property_list = sorted(st.session_state.property_list)
        
        # Load set of sentence IDs that have been labeled by any user (for unlabeled-only mode)
        st.session_state.labeled_sentence_ids = get_sentence_ids_labeled_by_anyone()
        
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
        
        # Initialize indices using filtered view (unlabeled-only affects which sentences exist)
        st.session_state.indices = {}
        for prop in st.session_state.property_list:
            texts = get_filtered_texts(prop)
            st.session_state.indices[prop] = find_first_unlabeled(
                texts,
                st.session_state.labels[prop]
            )
        
        # Set current property to first in filtered list
        filtered_props = get_filtered_property_list()
        if filtered_props:
            st.session_state.current_prop = filtered_props[0]
            st.session_state.data_loaded = True
        else:
            st.session_state.current_prop = st.session_state.property_list[0] if st.session_state.property_list else None
            st.session_state.data_loaded = True
            
    except Exception as e:
        st.sidebar.error(f"❌ Error loading data from database: {e}")
        st.session_state.data_loaded = False


def render_sidebar():
    """Render sidebar with user info and export functionality."""
    # User info
    user_stats = get_user_stats(st.session_state.user_id)
    render_user_info(st.session_state.username, user_stats)
    
    # Global mode: show only sentences not labeled by anybody (default)
    if st.session_state.data_loaded:
        st.sidebar.markdown("---")
        st.sidebar.subheader("🌐 Display mode")
        mode_options = ["Unlabeled only (default)", "All sentences"]
        mode_index = 0 if st.session_state.show_unlabeled_only else 1
        new_mode = st.sidebar.selectbox(
            "Show properties and sentences",
            options=mode_options,
            index=mode_index,
            key="global_display_mode",
            help="Unlabeled only: only properties and sentences that have not been labeled by any user. All: show everything."
        )
        if (new_mode == "Unlabeled only (default)") != st.session_state.show_unlabeled_only:
            st.session_state.show_unlabeled_only = (new_mode == "Unlabeled only (default)")
            # Reset indices and current_prop so we don't point to wrong sentence after filter change
            filtered_props = get_filtered_property_list()
            for prop in st.session_state.property_list:
                texts = get_filtered_texts(prop)
                st.session_state.indices[prop] = find_first_unlabeled(texts, st.session_state.labels[prop]) if texts else 0
            st.session_state.current_prop = filtered_props[0] if filtered_props else (st.session_state.property_list[0] if st.session_state.property_list else None)
            st.rerun()
    
    # Show dataset statistics if data is loaded (filtered when in unlabeled-only mode)
    if st.session_state.data_loaded:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Dataset Statistics")
        filtered_props = get_filtered_property_list()
        visible_sentences = sum(len(get_filtered_texts(prop)) for prop in filtered_props)
        st.sidebar.metric("Properties", len(filtered_props))
        st.sidebar.metric("Total Sentences", visible_sentences)
        if st.session_state.show_unlabeled_only:
            total_in_db, labeled_by_anyone = get_labeled_sentence_stats()
            unlabeled_count = total_in_db - labeled_by_anyone
            st.sidebar.caption(
                f"**Labeling stats:** {total_in_db} total sentences · "
                f"**{labeled_by_anyone}** labeled by at least one user · **{unlabeled_count}** unlabeled."
            )
            if unlabeled_count == 0 and total_in_db > 0:
                st.sidebar.info("All sentences have been labeled by someone. Switch to **All sentences** to view or edit them.")
    
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
    
    # Use filtered property list and texts (global unlabeled-only mode)
    filtered_property_list = get_filtered_property_list()
    if not filtered_property_list:
        st.warning("No properties or sentences to show in the current display mode. Switch to **All sentences** in the sidebar to see everything.")
        return
    
    # Ensure current_prop is in the filtered list (e.g. after mode switch)
    if st.session_state.current_prop not in filtered_property_list:
        st.session_state.current_prop = filtered_property_list[0]
        st.session_state.indices[st.session_state.current_prop] = 0
        st.rerun()
    
    # Property Selection
    st.markdown("### 🔍 Select Property")
    selected_prop = st.selectbox(
        "Choose a property to label",
        options=filtered_property_list,
        index=filtered_property_list.index(st.session_state.current_prop),
        key="property_selector_main"
    )
    
    # Update current property if changed
    if selected_prop != st.session_state.current_prop:
        st.session_state.current_prop = selected_prop
        st.rerun()
    
    # Get current property data (filtered texts)
    prop = st.session_state.current_prop
    prop_data = st.session_state.data_raw[prop]
    texts = get_filtered_texts(prop)
    current_idx = st.session_state.indices.get(prop, 0)
    
    # Ensure index is valid for filtered list
    if current_idx >= len(texts):
        current_idx = max(0, len(texts) - 1)
        st.session_state.indices[prop] = current_idx
    
    if not texts:
        st.warning(f"No sentences found for property: {prop} in the current display mode.")
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
        # Keep global unlabeled-only view in sync: this sentence is now labeled by someone
        if "labeled_sentence_ids" in st.session_state:
            st.session_state.labeled_sentence_ids.add(sentence_id)
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


def render_my_labels_tab():
    """Render the 'My Labels' tab: view and edit sentences that have already been labelled."""
    # Show persisted save confirmation (survives rerun)
    if st.session_state.pop("my_labels_save_success", None):
        st.success("Your changes have been saved.")

    user_id = st.session_state.user_id
    db_labels = get_user_labels(user_id)

    # Flatten to list of (property, sentence, label_data)
    labelled_entries = []
    for prop, sentences_dict in db_labels.items():
        for sentence, label_data in sentences_dict.items():
            label_code = label_data.get("label_code", "") if isinstance(label_data, dict) else label_data
            if not label_code:
                continue
            labelled_entries.append({
                "property": prop,
                "sentence": sentence,
                "label_code": label_code,
                "subject_words": label_data.get("subject_words", "") if isinstance(label_data, dict) else "",
                "object_words": label_data.get("object_words", "") if isinstance(label_data, dict) else "",
                "is_complete": label_data.get("is_complete", False) if isinstance(label_data, dict) else False,
                "labeled_at": label_data.get("labeled_at") if isinstance(label_data, dict) else None,
                "updated_at": label_data.get("updated_at") if isinstance(label_data, dict) else None,
            })

    if not labelled_entries:
        st.info("You haven't labelled any sentences yet. Use the **Label Sentences** tab to get started.")
        return

    # Filter by property and search phrase
    all_props = sorted(set(e["property"] for e in labelled_entries))
    col_filter, col_search, col_sort = st.columns([1, 2, 1])
    with col_filter:
        filter_prop = st.selectbox(
            "Filter by property",
            options=["All"] + all_props,
            key="my_labels_property_filter"
        )
    with col_search:
        search_phrase = st.text_input(
            "Search in sentence",
            placeholder="Type a word or phrase to filter sentences…",
            key="my_labels_search_phrase"
        )
    with col_sort:
        sort_by = st.selectbox(
            "Sort by time",
            options=["Newest first", "Oldest first"],
            key="my_labels_sort_by"
        )

    if filter_prop != "All":
        labelled_entries = [e for e in labelled_entries if e["property"] == filter_prop]
    if search_phrase and search_phrase.strip():
        phrase = search_phrase.strip().lower()
        labelled_entries = [e for e in labelled_entries if phrase in e["sentence"].lower()]

    # Sort by labeled_at (use labeled_at, fallback to updated_at or empty string for missing)
    def sort_key(e):
        t = e.get("labeled_at") or e.get("updated_at") or ""
        return t

    labelled_entries.sort(key=sort_key, reverse=(sort_by == "Newest first"))

    st.caption(f"Showing {len(labelled_entries)} labelled sentence(s). Expand a row to edit.")

    if not labelled_entries:
        st.info("No sentences match your search. Try a different phrase or property filter.")

    for i, entry in enumerate(labelled_entries):
        prop = entry["property"]
        sentence = entry["sentence"]
        label_code = entry["label_code"]
        subject_str = entry["subject_words"] or ""
        object_str = entry["object_words"] or ""
        subject_list = [int(x) for x in subject_str.split(",") if x.strip()] if subject_str else []
        object_list = [int(x) for x in object_str.split(",") if x.strip()] if object_str else []

        label_display = CODE_TO_LABEL_DISPLAY.get(label_code, label_code)
        words = sentence.split()
        subject_preview = " ".join(words[j] for j in subject_list) if subject_list else "(none)"
        object_preview = " ".join(words[j] for j in object_list) if object_list else "(none)"
        sent_preview = (sentence[:60] + "…") if len(sentence) > 60 else sentence

        # Unique key for this entry
        entry_key = f"my_labels_{prop}_{i}_{abs(hash(sentence)) % 10**6}"

        with st.expander(f"**{prop}** · {label_display[:35]}… · {sent_preview}", expanded=False):
            st.markdown("#### Sentence")
            st.text_area("Sentence", value=sentence, height=100, disabled=True, key=f"{entry_key}_sent", label_visibility="collapsed")

            st.markdown("#### Current label")
            st.markdown(f"**{label_display}** (`{label_code}`)")

            st.markdown("#### Edit label and spans")
            # Ensure word_selections exist for this prop/sentence when editing (don't overwrite in-session edits)
            if "word_selections" not in st.session_state:
                st.session_state.word_selections = {}
            if prop not in st.session_state.word_selections:
                st.session_state.word_selections[prop] = {}
            if sentence not in st.session_state.word_selections[prop]:
                st.session_state.word_selections[prop][sentence] = {"subject": list(subject_list), "object": list(object_list)}

            current_selections = st.session_state.word_selections[prop][sentence]
            new_label_display = render_label_selector(label_code, LABEL_CHOICES, key=f"{entry_key}_radio")
            new_label_code = LABEL_DISPLAY_TO_CODE.get(new_label_display, label_code)

            mode, new_subject, new_object = render_word_selection_interface(
                sentence,
                current_selections["subject"],
                current_selections["object"],
                key_prefix=f"{entry_key}_word",
                session_state_key=(prop, sentence)
            )

            # Sync back from session state (word_selection updates it)
            new_subject = st.session_state.word_selections[prop][sentence]["subject"]
            new_object = st.session_state.word_selections[prop][sentence]["object"]

            is_valid, err_msg = validate_label_completeness(new_label_code, new_subject, new_object)
            if not is_valid and err_msg:
                st.warning(err_msg)
            else:
                st.success("Label is complete.")

            if st.button("Save changes", key=f"{entry_key}_save", type="primary"):
                sentence_record = get_sentence_by_text(sentence, prop)
                if not sentence_record:
                    st.error("Sentence not found in database.")
                else:
                    sub_str = ",".join(map(str, new_subject)) if new_subject else None
                    obj_str = ",".join(map(str, new_object)) if new_object else None
                    db_save_label_new(
                        user_id=user_id,
                        sentence_id=sentence_record["id"],
                        label_code=new_label_code,
                        subject_words=sub_str,
                        object_words=obj_str,
                        is_complete=is_valid,
                    )
                    # Keep session state in sync if labels/data are loaded
                    if st.session_state.get("data_loaded") and prop in st.session_state.get("labels", {}):
                        st.session_state.labels[prop][sentence] = new_label_code
                        st.session_state.word_selections[prop][sentence] = {"subject": new_subject, "object": new_object}
                    st.session_state["my_labels_save_success"] = True
                    st.rerun()


def render_home_page():
    """Main entry point for the home page."""
    # Initialize data structures
    initialize_data()
    
    # Load data from database before rendering sidebar so display mode and stats show on first load
    load_data_from_database()
    
    # Render sidebar (now data_loaded is set, so all sidebar sections appear)
    render_sidebar()
    
    # Main content
    st.title("🏷️ Property Sentence Labeler")
    st.markdown("Label sentences with property-specific categories. Navigate through sentences and assign labels.")

    tab_label, tab_my_labels = st.tabs(["Label Sentences", "My Labels (view & edit)"])

    with tab_label:
        render_labeling_interface()

    with tab_my_labels:
        render_my_labels_tab()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>Built with Streamlit • Ready for Hugging Face Spaces</div>",
        unsafe_allow_html=True
    )
