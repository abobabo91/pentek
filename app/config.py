"""
Configuration and client utilities for the Streamlit app.
Handles page setup, navigation, and OpenAI client creation.
"""

import os
import streamlit as st
from typing import Optional, Any


# -------------------------
# Page setup and navigation
# -------------------------

def setup_page() -> None:
    """Configure Streamlit page and title."""
    st.set_page_config(page_title="AgentLab & AgentWorkspace", layout="wide")
    st.title("🤖 AI Agent Workspace")


def get_section() -> str:
    """Render sidebar navigation and return selected section."""
    return st.sidebar.radio("Navigation", ["AgentLab", "AgentWorkspace"])


# -------------------------
# OpenAI configuration
# -------------------------

def get_api_key() -> str:
    """Fetch OpenAI API key from Streamlit secrets or environment."""
    try:
        return st.secrets["openai"]["OPENAI_API_KEY"]
    except Exception:
        return os.environ.get("OPENAI_API_KEY", "")


def get_client(timeout: int = 600) -> Optional[Any]:
    """
    Construct an OpenAI client with proper timeout.
    Will stop the app if API key is missing.
    """
    api_key = get_api_key()
    if not api_key:
        st.error("Missing OpenAI API key. Please set OPENAI_API_KEY in env or Streamlit secrets.")
        st.stop()

    try:
        from openai import OpenAI  # type: ignore
        return OpenAI(api_key=api_key, timeout=timeout)
    except Exception:
        # Legacy SDK detected; services will use legacy openai module directly.
        return None
