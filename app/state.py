"""
Session state initialization and helpers.
Keeps Streamlit session_state keys centralized.
"""

import streamlit as st


DEFAULT_INBOUND_WORKSTREAMS = {
    "Inbound Email Screening": {"status": "Active"},
    "Manual Upload Screening": {"status": "Active"},
    "Advisor/Dealroom Sync": {"status": "Paused"},
    "Founder Webform Intake": {"status": "Active"},
}


def init_session_state() -> None:
    """Initialize required session_state keys with defaults if missing."""
    if "inbound_workstreams" not in st.session_state:
        st.session_state.inbound_workstreams = dict(DEFAULT_INBOUND_WORKSTREAMS)

    if "current_workstream" not in st.session_state:
        st.session_state.current_workstream = None

    if "creating_workstream" not in st.session_state:
        st.session_state.creating_workstream = False

    if "parsed_thesis_markdown" not in st.session_state:
        st.session_state.parsed_thesis_markdown = ""
