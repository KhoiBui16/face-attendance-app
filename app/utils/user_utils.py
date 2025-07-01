import streamlit as st

def is_logged_in():
    return st.session_state.get("logged_in", False)

def is_admin():
    return st.session_state.get("is_admin", False) and is_logged_in()

def is_allowed():
    return st.session_state.get("is_allowed", False) and is_logged_in()