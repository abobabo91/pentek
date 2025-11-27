"""
AgentWorkspace view: operations UI for inbound processing, manual uploads, and export.
"""

import streamlit as st


def render_agentops() -> None:
    # Sidebar: choose AgentWorkspace sub-page
    with st.sidebar:
        view = st.selectbox("AgentWorkspace View", ["Automatic", "Manual Upload"], index=0, key="agentops_view")

    st.header(f"⚙️ AgentWorkspace – {view}")

    if view == "Automatic":
        st.markdown("## 📥 Automatic Inbox")
        st.caption("New deals processed automatically based on your AgentLab rules.")

        # Sample inbox table with additional columns
        auto_rows = [
            {
                "Company": "AtWork",
                "Source": "Gmail",
                "Stage": "Seed",
                "Status": "Ready",
                "Fit": 82,
                "Summary": "SaaS HR tools; strong MRR growth; clear ICP.",
            },
            {
                "Company": "NovaCRM",
                "Source": "Drive",
                "Stage": "Series A",
                "Status": "Needs Review",
                "Fit": 41,
                "Summary": "CRM vertical; limited traction; unclear pricing.",
            },
            {
                "Company": "FlowOps",
                "Source": "Email",
                "Stage": "Seed",
                "Status": "Ready",
                "Fit": 67,
                "Summary": "Ops automation; repeat founders; promising pilots.",
            },
            {
                "Company": "EdgeAI",
                "Source": "Webform",
                "Stage": "Seed",
                "Status": "Ready",
                "Fit": 74,
                "Summary": "Applied AI; early revenue; strong technical moat.",
            },
        ]

        # Header
        h = st.columns([1, 1, 1, 1, 4, 1])
        with h[0]:
            st.markdown("**Company**")
        with h[1]:
            st.markdown("**Source**")
        with h[2]:
            st.markdown("**Stage**")
        with h[3]:
            st.markdown("**Fit**")
        with h[4]:
            st.markdown("**Summary**")
        with h[5]:
            st.markdown("**Action**")

        # Rows
        for i, r in enumerate(auto_rows):
            c = st.columns([1, 1, 1, 1, 4, 1])
            with c[0]:
                st.text(r["Company"])
            with c[1]:
                st.text(r["Source"])
            with c[2]:
                st.text(r["Stage"])
            with c[3]:
                st.text(f'{r["Fit"]}%')
            with c[4]:
                st.text(r["Summary"])
            with c[5]:
                st.button("Open", key=f"auto_open_{i}")

    else:
        st.markdown("## 🧳 Manual Upload")

        # Select an existing workstream from AgentLab
        ws_names = list(st.session_state.get("inbound_workstreams", {}).keys())
        if ws_names:
            st.selectbox(
                "Select workstream",
                ws_names,
                index=0,
                key="agentops_selected_workstream",
                help="Choose which workstream configuration to apply to this manual upload",
            )
        else:
            st.info("No workstreams found. Create one in AgentLab (Sourcing → Inbound) then return here.")

        uploaded_files = st.file_uploader(
            "Upload decks, IMs, transcripts for instant manual analysis.",
            accept_multiple_files=True,
            key="agentops_manual_uploads",
        )

        if uploaded_files:
            st.write("Uploaded Files:")
            for f in uploaded_files:
                st.write("•", f.name)

        if st.button("Run Analysis", key="agentops_run_manual"):
            selected_ws = st.session_state.get("agentops_selected_workstream")
            # Proceed without warning if not selected (matches latest user preference)
            if selected_ws:
                st.success(f"Manual analysis started for workstream '{selected_ws}' (stub).")
            else:
                st.success("Manual analysis started (stub).")

        st.markdown("### Recent Uploads")
        # Sample recent uploads with inline Run buttons
        manual_rows = [
            {
                "File": "AtWork_Deck_v3.pdf",
                "Company": "AtWork",
                "Status": "Ready",
                "Summary": "Deck parsed; ready to run AI extraction.",
            },
            {
                "File": "NovaCRM_IM.pdf",
                "Company": "NovaCRM",
                "Status": "Needs Setup",
                "Summary": "Missing stage and ticket size; edit thesis.",
            },
            {
                "File": "FlowOps_KPIs.xlsx",
                "Company": "FlowOps",
                "Status": "Ready",
                "Summary": "KPIs table detected; ready for extraction.",
            },
        ]

        # Header
        mh = st.columns([2, 1, 1, 4, 1])
        with mh[0]:
            st.markdown("**File**")
        with mh[1]:
            st.markdown("**Company**")
        with mh[2]:
            st.markdown("**Status**")
        with mh[3]:
            st.markdown("**Summary**")
        with mh[4]:
            st.markdown("**Action**")

        # Rows
        for i, r in enumerate(manual_rows):
            rc = st.columns([2, 1, 1, 4, 1])
            with rc[0]:
                st.text(r["File"])
            with rc[1]:
                st.text(r["Company"])
            with rc[2]:
                st.text(r["Status"])
            with rc[3]:
                st.text(r["Summary"])
            with rc[4]:
                st.button("Run", key=f"manual_run_{i}")

    # Common export section
    st.markdown("---")
    st.markdown("## 📤 Download & Export")

    # Export Format (multi-choice via checkboxes, arranged in 6 columns)
    st.markdown("### Export Format")
    fmt_options = ["Web View", "PDF", "Word (.docx)", "PowerPoint (.pptx)", "Notion Page", "Slack Share"]
    fmt_default = {"Web View"}
    fmt_cols = st.columns(6)
    selected_formats = []
    for i, fmt in enumerate(fmt_options):
        with fmt_cols[i % 6]:
            if st.checkbox(fmt, value=(fmt in fmt_default), key=f"agentops_fmt_{fmt}"):
                selected_formats.append(fmt)

    # Included in Export (multi-choice via checkboxes, arranged in 6 columns)
    st.markdown("### Included in Export")
    inc_options = [
        "1-page summary",
        "KPI extraction table",
        "Fit score + explanation",
        "Red / yellow flags",
        "Claim vs Reality section",
        "Suggested questions",
        "Management profiles",
        "Attach original files",
    ]
    inc_default = {
        "1-page summary",
        "KPI extraction table",
        "Fit score + explanation",
        "Red / yellow flags",
        "Claim vs Reality section",
        "Suggested questions",
    }
    inc_cols = st.columns(6)
    selected_included = []
    for i, opt in enumerate(inc_options):
        with inc_cols[i % 6]:
            if st.checkbox(opt, value=(opt in inc_default), key=f"agentops_inc_{opt}"):
                selected_included.append(opt)
    st.markdown("### Other Options")

    st.checkbox("Remove internal notes", value=True, key="agentops_export_rm_notes")
    st.checkbox("Show scoring model", key="agentops_export_show_model")
    st.checkbox("Include timestamp & analyst initials", key="agentops_export_meta")

    st.markdown("---")
