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
    # Filter by global label_count: "up_to" N (count <= N), "exactly" K (count == K), or "all". Checked at login.
    if "label_filter_mode" not in st.session_state:
        st.session_state.label_filter_mode = "up_to"  # Default: unlabeled only
    if "label_filter_value" not in st.session_state:
        st.session_state.label_filter_value = 0
    if "hide_properties_with_none_below_threshold" not in st.session_state:
        st.session_state.hide_properties_with_none_below_threshold = True


def _sentence_matches_filter(prop: str, sentence_id: int) -> bool:
    """True if sentence's global label_count matches the current filter (up_to N, exactly K, or all)."""
    mode = st.session_state.get("label_filter_mode", "up_to")
    value = st.session_state.get("label_filter_value", 0)
    if mode == "all":
        return True
    count = st.session_state.data_raw[prop].get("label_counts", {}).get(sentence_id, 0)
    if mode == "up_to":
        return count <= value
    if mode == "exactly":
        return count == value
    return True


def get_filtered_property_list():
    """Properties to show: optionally hide properties with no sentences matching the current filter."""
    if st.session_state.get("label_filter_mode") == "all":
        return st.session_state.property_list
    hide_empty = st.session_state.get("hide_properties_with_none_below_threshold", True)
    if not hide_empty:
        return st.session_state.property_list
    return [
        prop for prop in st.session_state.property_list
        if any(_sentence_matches_filter(prop, sid) for sid in st.session_state.data_raw[prop].get("sentence_ids", []))
    ]


def _run_scroll_to_top():
    """Scroll page to top after save. Tries st.html(unsafe_allow_javascript=True) (Streamlit 1.52+); fallback: scroll-to-top component button."""
    scroll_html = """
    <script>
    (function() {
        function scrollToTop() {
            try {
                document.body.scrollTop = 0;
                document.documentElement.scrollTop = 0;
                window.scrollTo(0, 0);
                var app = document.querySelector('[data-testid="stAppViewContainer"]');
                if (app) app.scrollTop = 0;
                var main = document.querySelector('main');
                if (main) main.scrollTop = 0;
                if (window.parent && window.parent !== window) {
                    window.parent.scrollTo(0, 0);
                    var anchor = window.parent.document.getElementById('top-anchor');
                    if (anchor) anchor.scrollIntoView({behavior: 'smooth', block: 'start'});
                }
                var anchor = document.getElementById('top-anchor');
                if (anchor) anchor.scrollIntoView({behavior: 'smooth', block: 'start'});
            } catch (e) {}
        }
        scrollToTop();
        if (document.readyState !== 'complete') window.addEventListener('load', scrollToTop);
        setTimeout(scrollToTop, 150);
        setTimeout(scrollToTop, 500);
    })();
    </script>
    """
    try:
        st.html(scroll_html, unsafe_allow_javascript=True)
    except (TypeError, AttributeError):
        st.markdown(scroll_html, unsafe_allow_html=True)
    # Fallback: show a button so user can scroll to top if JS did not run (e.g. Streamlit < 1.52 or iframe)
    try:
        from streamlit_scroll_to_top import scroll_to_here
        scroll_to_here(delay=0, key="scroll_after_save")
    except Exception:
        pass


def get_filtered_texts(prop: str):
    """Sentence texts to show for a property: those matching the current filter (up_to N, exactly K, or all)."""
    texts = st.session_state.data_raw[prop]["texts"]
    ids = st.session_state.data_raw[prop].get("sentence_ids", [])
    return [t for t, sid in zip(texts, ids) if _sentence_matches_filter(prop, sid)]


def load_data_from_database():
    """Load data from database (properties and sentences). Filter by global label_count < threshold (checked once at login)."""
    # Force reload if cached data lacks sentence_ids or label_counts (e.g. from before threshold-based filtering).
    if st.session_state.data_loaded and st.session_state.property_list:
        first_prop = st.session_state.property_list[0]
        raw = st.session_state.data_raw.get(first_prop, {})
        if not raw.get("sentence_ids") or "label_counts" not in raw:
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
        
        # Build data structure with sentence IDs and global label_count per sentence (for threshold filtering)
        st.session_state.data_raw = {}
        st.session_state.property_list = []
        
        for prop in properties:
            prop_name = prop["property_name"]
            st.session_state.property_list.append(prop_name)
            
            # Get sentences for this property (each has id, sentence, label_count from DB)
            sentences = get_sentences_by_property(prop["id"])
            
            st.session_state.data_raw[prop_name] = {
                "domain": prop["property_domain"] or "",
                "range": prop["property_range"] or "",
                "texts": [s["sentence"] for s in sentences],
                "sentence_ids": [s["id"] for s in sentences],
                "label_counts": {s["id"]: s.get("label_count", 0) for s in sentences},
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
    
    # Display mode: Up to N labels / Exactly K labels / All (counts fixed at login)
    if st.session_state.data_loaded:
        st.sidebar.markdown("---")
        st.sidebar.subheader("🌐 Display mode")
        filter_type_options = ["Up to N labels", "Exactly K labels", "All sentences"]
        current_mode = st.session_state.get("label_filter_mode", "up_to")
        current_value = st.session_state.get("label_filter_value", 0)
        mode_to_option = {"up_to": "Up to N labels", "exactly": "Exactly K labels", "all": "All sentences"}
        option_to_mode = {v: ("up_to" if v == "Up to N labels" else "exactly" if v == "Exactly K labels" else "all") for v in filter_type_options}
        try:
            type_index = filter_type_options.index(mode_to_option.get(current_mode, "Up to N labels"))
        except ValueError:
            type_index = 0
        new_type = st.sidebar.selectbox(
            "Show sentences with",
            options=filter_type_options,
            index=type_index,
            key="global_display_mode",
            help="Up to N: sentences with 0..N complete labelings. Exactly K: sentences with exactly K labelings. Counts are fixed at login."
        )
        new_mode = option_to_mode[new_type]
        new_value = current_value
        if new_mode in ("up_to", "exactly"):
            label_n = st.sidebar.number_input(
                "N" if new_mode == "up_to" else "K",
                min_value=0,
                max_value=100,
                value=current_value,
                step=1,
                key="label_filter_value_input",
                help="Up to N: show sentences with 0 to N labels. Exactly K: show only sentences with exactly K labels."
            )
            new_value = int(label_n)
        filter_changed = (new_mode != current_mode) or (new_value != current_value)
        if filter_changed:
            st.session_state.label_filter_mode = new_mode
            st.session_state.label_filter_value = new_value
            filtered_props = get_filtered_property_list()
            for prop in st.session_state.property_list:
                texts = get_filtered_texts(prop)
                st.session_state.indices[prop] = find_first_unlabeled(texts, st.session_state.labels[prop]) if texts else 0
            current_prop = st.session_state.current_prop
            if filtered_props and current_prop in filtered_props:
                st.session_state.current_prop = current_prop
            else:
                st.session_state.current_prop = filtered_props[0] if filtered_props else (st.session_state.property_list[0] if st.session_state.property_list else None)
            st.rerun()
        hide_empty = st.sidebar.checkbox(
            "Hide properties with no matching sentences",
            value=st.session_state.get("hide_properties_with_none_below_threshold", True),
            key="hide_properties_below_threshold",
            help="When enabled, properties with no sentences matching the current filter are hidden."
        )
        if hide_empty != st.session_state.get("hide_properties_with_none_below_threshold", True):
            st.session_state.hide_properties_with_none_below_threshold = hide_empty
            filtered_props = get_filtered_property_list()
            for prop in st.session_state.property_list:
                texts = get_filtered_texts(prop)
                st.session_state.indices[prop] = find_first_unlabeled(texts, st.session_state.labels[prop]) if texts else 0
            current_prop = st.session_state.current_prop
            if filtered_props and current_prop in filtered_props:
                st.session_state.current_prop = current_prop
            else:
                st.session_state.current_prop = filtered_props[0] if filtered_props else (st.session_state.property_list[0] if st.session_state.property_list else None)
            st.rerun()
    
    # Show dataset statistics (counts from data loaded at login)
    if st.session_state.data_loaded:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Dataset Statistics")
        filtered_props = get_filtered_property_list()
        visible_sentences = sum(len(get_filtered_texts(prop)) for prop in filtered_props)
        st.sidebar.metric("Properties", len(filtered_props))
        st.sidebar.metric("Total Sentences (in view)", visible_sentences)
        mode = st.session_state.get("label_filter_mode", "up_to")
        value = st.session_state.get("label_filter_value", 0)
        if mode != "all":
            total_in_db = sum(len(st.session_state.data_raw[p]["texts"]) for p in st.session_state.property_list)
            count_matching = sum(
                1 for p in st.session_state.property_list
                for sid in st.session_state.data_raw[p].get("sentence_ids", [])
                if _sentence_matches_filter(p, sid)
            )
            if mode == "up_to":
                st.sidebar.caption(
                    f"**Label count (at login):** {total_in_db} total · **{count_matching}** with ≤ {value} label(s)."
                )
            else:
                st.sidebar.caption(
                    f"**Label count (at login):** {total_in_db} total · **{count_matching}** with exactly {value} label(s)."
                )
            if count_matching == 0 and total_in_db > 0:
                st.sidebar.info("No sentences match the filter. Change N/K or switch to **All sentences**, or reload after more labeling.")
    
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
    
    # On next run after "Save and next", scroll to top so user sees the new sentence from the start
    if st.session_state.pop("scroll_to_top_after_save", False):
        _run_scroll_to_top()
    
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
    
    # Render progress and stats (use full property totals when view is filtered by threshold)
    full_texts = st.session_state.data_raw[prop]["texts"]
    full_total = len(full_texts)
    full_labeled = sum(
        1 for t in full_texts
        if st.session_state.labels[prop].get(t, "") != ""
    )
    use_full_stats = (st.session_state.get("label_filter_mode") != "all") and (full_total != len(texts))
    render_progress_stats(
        current_idx,
        texts,
        st.session_state.labels[prop],
        full_property_total=full_total if use_full_stats else None,
        full_property_labeled=full_labeled if use_full_stats else None,
    )
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
        st.success("✅ **Label is complete!** Click **Save and next** to save and move on.")
    elif error_message:
        st.warning(error_message)
    
    st.markdown("---")
    st.markdown("#### 💾 Save & navigate")
    
    # Save and next: persist to DB then advance to next sentence
    subject_str = ",".join(map(str, subject_list)) if subject_list else None
    object_str = ",".join(map(str, object_list)) if object_list else None
    sentence_record = get_sentence_by_text(current_sentence, prop)
    
    save_and_next_clicked = st.button("Save and next", type="primary", use_container_width=True, key="save_and_next_btn")
    if save_and_next_clicked and sentence_record:
        sentence_id = sentence_record["id"]
        db_save_label_new(
            user_id=st.session_state.user_id,
            sentence_id=sentence_id,
            label_code=current_label_code if current_label_code else "",
            subject_words=subject_str,
            object_words=object_str,
            is_complete=is_valid,
        )
        # Advance to next sentence (prefer next unlabeled). No in-session update of label_count; checked at login only.
        next_idx = find_next_unlabeled(texts, st.session_state.labels[prop], current_idx)
        if next_idx == current_idx and current_idx < len(texts) - 1:
            next_idx = current_idx + 1
        st.session_state.indices[prop] = next_idx
        st.session_state["scroll_to_top_after_save"] = True
        st.rerun()
    elif save_and_next_clicked and not sentence_record:
        st.error(f"⚠️ Sentence not found in database for property '{prop}'.")
    
    st.markdown("---")
    
    # Navigation buttons (no save; just move)
    prev_btn, next_btn, jump_prev_btn, jump_next_btn = render_navigation_buttons()
    
    if prev_btn and current_idx > 0:
        st.session_state.indices[prop] = current_idx - 1
        st.session_state["scroll_to_top_after_save"] = True
        st.rerun()
    
    if next_btn and current_idx < len(texts) - 1:
        st.session_state.indices[prop] = current_idx + 1
        st.session_state["scroll_to_top_after_save"] = True
        st.rerun()
    
    if jump_prev_btn:
        new_idx = find_prev_unlabeled(texts, st.session_state.labels[prop], current_idx)
        if new_idx != current_idx:
            st.session_state.indices[prop] = new_idx
            st.session_state["scroll_to_top_after_save"] = True
            st.rerun()
        else:
            st.info("No previous unlabeled sentence found")
    
    if jump_next_btn:
        new_idx = find_next_unlabeled(texts, st.session_state.labels[prop], current_idx)
        if new_idx != current_idx:
            st.session_state.indices[prop] = new_idx
            st.session_state["scroll_to_top_after_save"] = True
            st.rerun()
        else:
            st.info("No next unlabeled sentence found")
    


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
