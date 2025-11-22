"""
AgentLab view: agent setup UI, workstream list, create form, and detail tabs.
"""

from typing import Optional, Any

import streamlit as st

from app.views.cards import (
    render_thesis_card,
    render_triggers_card,
    render_source_card,
    render_extraction_card,
    render_datasources_card,
    render_output_settings_card,
)


def render_agentlab(client: Optional[Any]) -> None:
    """Top-level AgentLab renderer with left navigation and right config panel."""
    # Sidebar: Category and Sub-category only
    with st.sidebar:
        _render_sidebar_nav()

    # Dynamic title based on selection
    title = st.session_state.get("selected_subcategory") or st.session_state.get("selected_category") or "AgentLab – Agent Setup"
    st.header(f"🧪 {title}")

    # Left-right layout: left = Workstreams, right = details/forms
    col_left, col_right = st.columns([2, 3], gap="large")

    with col_left:
        _render_left_panel()

    with col_right:
        if st.session_state.creating_workstream:
            render_new_workstream_form()
        elif st.session_state.current_workstream:
            render_workstream_detail(st.session_state.current_workstream, client)
        else:
            st.markdown("### No Workstream Selected")
            st.caption("Choose an existing workstream or create a new one from the left panel.")


def _render_sidebar_nav() -> None:
    """Sidebar navigation for Category and Sub-category selection."""
    categories = {
        "Sourcing": ["Inbound Sourcing Agent", "Outbound Sourcing Agent (coming soon)"],
        "Research": ["Company Research (coming soon)", "Market Research (coming soon)"],
        "Portfolio": ["Monitoring (coming soon)", "Value Creation (coming soon)"],
        "Deal Desk": ["Due Diligence (coming soon)", "Modeling (coming soon)"],
    }

    selected_category = st.selectbox("Category", list(categories.keys()), index=0)
    sub_options = categories[selected_category]
    selected_subcategory = st.selectbox("Sub-category", sub_options, index=0)

    # Persist selection
    st.session_state.selected_category = selected_category
    st.session_state.selected_subcategory = selected_subcategory


def _render_left_panel() -> None:
    """Left panel: workstreams list and actions (uses selections from sidebar)."""
    category = st.session_state.get("selected_category", "Sourcing")
    agent_type = st.session_state.get("selected_subcategory", "Inbound Sourcing Agent")

    if category == "Sourcing" and agent_type.startswith("Inbound"):
        st.markdown("#### Workstreams")
        st.caption("AgentLab > Sourcing > Inbound Agent > Workstreams")

        # Create New Workstream button
        if st.button("➕ Create New Workstream", use_container_width=True):
            st.session_state.creating_workstream = True
            st.session_state.current_workstream = None
        st.divider()

        st.markdown("**Existing Workstreams:**")
        # Compact styling for buttons and separators
        st.markdown(
            """
            <style>
            /* Make buttons smaller across the app (especially Workstreams) */
            div.stButton > button {
                padding: 0.2rem 0.5rem !important;
                font-size: 0.8rem !important;
                line-height: 1.1 !important;
                margin: 2px 0 !important;
            }
            /* Make generic separators tighter */
            hr { margin: 6px 0 !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # List existing workstreams
        to_delete: Optional[str] = None
        for name, cfg in list(st.session_state.inbound_workstreams.items()):
            status = cfg.get("status", "Active")

            st.markdown(
                f"<span style='font-size:0.9rem'><strong>{name}</strong> · <span style='opacity:0.7'>Status: {status}</span></span>",
                unsafe_allow_html=True,
            )

            # Buttons in a single row
            col_a, col_b, col_c = st.columns([1, 1, 1])
            with col_a:
                if st.button("Config", key=f"cfg_{name}"):
                    st.session_state.current_workstream = name
                    st.session_state.creating_workstream = False
            with col_b:
                toggle_label = "Pause" if status == "Active" else "Activate"
                if st.button(toggle_label, key=f"toggle_{name}"):
                    st.session_state.inbound_workstreams[name]["status"] = (
                        "Paused" if status == "Active" else "Active"
                    )
            with col_c:
                if st.button("Delete", key=f"del_{name}"):
                    to_delete = name

            st.markdown("<hr>", unsafe_allow_html=True)

        if to_delete:
            st.session_state.inbound_workstreams.pop(to_delete, None)
            if st.session_state.current_workstream == to_delete:
                st.session_state.current_workstream = None

    else:
        st.info("Select **Sourcing → Inbound Sourcing Agent** to configure inbound workstreams.")


# -------------------------
# New Workstream Form
# -------------------------

def render_new_workstream_form() -> None:
    st.markdown("### ➕ Create New Inbound Workstream")
    name = st.text_input("Workstream Name", placeholder="e.g. Inbound Email Screening")
    status = st.selectbox("Initial Status", ["Active", "Paused"], index=0)

    if st.button("Save Workstream"):
        if not name.strip():
            st.error("Please provide a name for the workstream.")
        elif name in st.session_state.inbound_workstreams:
            st.error("A workstream with this name already exists.")
        else:
            st.session_state.inbound_workstreams[name] = {"status": status}
            st.session_state.current_workstream = name
            st.session_state.creating_workstream = False
            st.success(f"Workstream '{name}' created.")
            st.experimental_rerun()


# -------------------------
# Workstream Detail View
# -------------------------

def render_workstream_detail(name: str, client: Optional[Any]) -> None:
    st.markdown(f"### ⚙️ Configure Workstream: **{name}**")
    st.caption("This is a reusable configuration. Once set, you can run it in AgentOps.")

    tabs = st.tabs(
        [
            "1. Investment Thesis",
            "2. Triggers",
            "3. Source",
            "4. What to Look For",
            "5. Data Sources",
            "6. Output Settings",
        ]
    )

    with tabs[0]:
        render_thesis_card(client)

    with tabs[1]:
        render_triggers_card()

    with tabs[2]:
        render_source_card()

    with tabs[3]:
        render_extraction_card()

    with tabs[4]:
        render_datasources_card()

    with tabs[5]:
        render_output_settings_card()
