import streamlit as st

def inject_css():
    st.markdown("""
    <style>
        .block-container { padding-top: 2rem; }
        .sentence-box {
            font-size: 18px;
            padding: 16px;
            border-radius: 10px;
            background-color: #f6f6f6;
        }
    </style>
    """, unsafe_allow_html=True)
