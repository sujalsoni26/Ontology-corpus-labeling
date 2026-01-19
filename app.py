import streamlit as st
from auth import init_db, signup, login
from file_store import read_labels, write_labels, get_next_unlabeled_sentence
from ui import inject_css
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=3000, key="refresh")

init_db()
inject_css()

# st.query_params(refresh="true")
# st.autorefresh(interval=3000)

st.set_page_config("Sentence Labeler", layout="wide")

# ---------- Session ----------
if "user" not in st.session_state:
    st.session_state.user = None

# ---------- AUTH ----------
if not st.session_state.user:
    st.title("🔐 Login / Signup")

    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if login(u, p):
                st.session_state.user = u
                st.experimental_set_query_params()  # Trigger rerun
            else:
                st.error("Invalid credentials")

    with tab2:
        u = st.text_input("New Username")
        p = st.text_input("New Password", type="password")
        if st.button("Signup"):
            if signup(u, p):
                st.success("Account created. Login now.")
            else:
                st.error("Username already exists")

    st.stop()

# ---------- APP ----------
st.sidebar.success(f"Logged in as {st.session_state.user}")
if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.experimental_set_query_params()  # Trigger rerun

st.title("🧠 Property Sentence Labeler (Real-Time)")

labels = read_labels()

if not labels:
    st.warning("No data found in labels.json. Please ensure the file is not empty or corrupted.")

# Dropdown to select a property
property_name = st.selectbox("Select Property", options=[""] + list(labels.keys()))

# Display the next unlabeled sentence
if property_name:
    annotations = labels.setdefault(property_name, {}).setdefault("annotations", {})
    sentences = labels[property_name].get("texts", [])
    total_sentences = len(sentences)
    labeled_sentences = sum(
        1 for sentence in sentences if sentence in annotations and annotations[sentence]
    )
    progress = labeled_sentences / total_sentences if total_sentences > 0 else 0

    # Show progress bar and metric
    st.progress(progress)
    st.metric(
        label="Progress",
        value=f"{labeled_sentences}/{total_sentences} sentences labeled",
        delta=f"{progress * 100:.2f}% complete"
    )

    next_sentence = get_next_unlabeled_sentence(property_name, annotations)

    if next_sentence:
        st.text_area("Sentence", value=next_sentence, height=120, disabled=True)

        # Label selection and explanation
        st.markdown("""
        **Alignment Explanation:**
        - **p(D, R)**: Full alignment - The property is expressed, and the textual entities or their references comply with the domain and range.
        - **p(D, ?)**: Property and domain are aligned - The property is expressed, and the domain aligns, but the range does not.
        - **p(?, R)**: Property and range are aligned - The property is expressed, and the range aligns, but the domain does not.
        - **p(?, ?)**: Property expressed, but both domain and range do not align.
        - **n**: No alignment - The property is not expressed in the sentence.
        """)

        label = st.radio(
            "Choose alignment:",
            ["p(D, R)", "p(D, ?)", "p(?, R)", "p(?, ?)", "No alignment"],
            horizontal=False
        )

        if st.button("💾 Save"):
            annotations.setdefault(st.session_state.user, {})[next_sentence] = label
            write_labels(labels)
            st.success("Saved (real-time)")
            st.experimental_set_query_params()  # Trigger rerun
    else:
        st.info("All sentences for this property have been labeled.")
else:
    st.info("Please select a property to begin labeling.")

st.divider()
st.caption("🔄 Updates sync automatically for all users")
