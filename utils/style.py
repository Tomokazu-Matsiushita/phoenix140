import streamlit as st

def apply_theme():
    st.markdown("""
    <style>
    .block-container { padding-top: 1.8rem; padding-bottom: 2rem; }
    div[data-testid="stMetric"] {
        background: rgba(128,128,128,0.08);
        padding: 16px;
        border-radius: 18px;
        border: 1px solid rgba(128,128,128,0.15);
    }
    </style>
    """, unsafe_allow_html=True)
