"""
Reusable card components used across views.
Each card is a focused UI section with its own controls.
"""

import streamlit as st
from typing import Optional, Any

from app.services import parse_investment_thesis


# -------------------------
# Card 1 – Investment Thesis
# -------------------------

def render_thesis_card(client: Optional[Any]) -> None:
    st.subheader("DEFINE INVESTMENT THESIS")
    st.write("Describe your fund’s investment logic. AI will extract and structure it into thesis components automatically.")

    # Initialize structured thesis state if missing
    if "thesis_struct" not in st.session_state:
        st.session_state.thesis_struct = {
            "sectors": ["SaaS", "AI", "HR Tech"],
            "geography": ["CEE", "DACH"],
            "stages": ["Seed", "Series A"],
            "ticket_min": 300_000,
            "ticket_max": 2_000_000,
            "scoring": {
                "team_quality": 9,
                "tech_readiness": 8,
                "market_size": 9,
                "geography_fit": 10,
                "traction": 5,
                "ticket_fit": 5,
            },
            "flags": ["Flag if MRR < €20k", "Flag if hardware-intensive", "Flag if founder not technical"],
            "rejects": ["Reject if outside CEE", "Reject if no revenue (for Seed+)"],
            "notes": "We prefer founder-led companies, avoid government-heavy sectors.",
        }

    thesis = st.session_state.thesis_struct

    # Free text thesis and AI parse
    example_text = (
        "We invest in CEE-based SaaS, AI and HRtech companies at Seed/Series A stage, ideally with €20–100k MRR, "
        "strong technical founders, and early signs of scalability. We avoid deep hardware, crypto, and biotech. "
        "Geography: CEE + DACH optional. Ticket size €300k–€2M."
    )
    thesis_text = st.text_area(
        "✍️ Free-Text Thesis Description",
        value=example_text,
        height=180,
        help="Write in your own language; AI will interpret.",
        key="thesis_free_text",
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Suggest Thesis Elements"):
            st.info("Template suggestions not implemented yet. Use Parse Automatically.")
    with c2:
        if st.button("Parse Automatically"):
            if not thesis_text.strip():
                st.error("Please enter a thesis description before parsing.")
            else:
                with st.spinner("Parsing thesis with AI..."):
                    data = parse_investment_thesis(thesis_text, client)
                    st.session_state.thesis_struct = data
                    thesis = data
                st.success("Thesis parsed and populated.")

    st.markdown("---")
    st.subheader("🧠 AI-EXTRACTED THESIS COMPONENTS (Editable)")

    # 1) Sector Focus
    st.markdown("##### 🎯 Sector Focus")
    sector_suggestions = ["SaaS", "AI", "HR Tech", "Fintech"]
    sector_options = sorted(set(thesis.get("sectors", []) + sector_suggestions))
    selected_sectors = st.multiselect("Select sectors", sector_options, default=thesis.get("sectors", []), key="thesis_sectors")
    suggested_only = [s for s in sector_suggestions if s not in selected_sectors]
    if suggested_only:
        st.caption("Suggested: " + ", ".join(suggested_only))
    row = st.columns([4, 1])
    with row[0]:
        new_sector = st.text_input("", key="add_sector_input", placeholder="Add custom sector", label_visibility="collapsed")
    with row[1]:
        if st.button("Add Sector", key="add_sector_btn"):
            val = new_sector.strip()
            if val and val not in selected_sectors:
                selected_sectors.append(val)
    thesis["sectors"] = selected_sectors

    # 2) Geography Fit
    st.markdown("##### 📍 Geography Fit")
    geo_suggestions = ["CEE", "DACH", "Baltics"]
    geo_options = sorted(set(thesis.get("geography", []) + geo_suggestions))
    selected_geo = st.multiselect("Allowed regions", geo_options, default=thesis.get("geography", []), key="thesis_geo")
    suggested_geo = [g for g in geo_suggestions if g not in selected_geo]
    if suggested_geo:
        st.caption("Suggested: " + ", ".join(suggested_geo))
    row = st.columns([4, 1])
    with row[0]:
        new_geo = st.text_input("", key="add_geo_input", placeholder="Add custom region", label_visibility="collapsed")
    with row[1]:
        if st.button("Add Region", key="add_geo_btn"):
            val = new_geo.strip()
            if val and val not in selected_geo:
                selected_geo.append(val)
    thesis["geography"] = selected_geo

    # 3) Stage
    st.markdown("##### 📈 Stage")
    all_stages = ["Pre-Seed", "Seed", "Series A", "Series B", "Growth"]
    stage_default = [s for s in thesis.get("stages", []) if s in all_stages]
    selected_stages = st.multiselect("Selected stages", all_stages, default=stage_default, key="thesis_stages")
    stage_suggestions = ["Pre-Seed", "Growth"]
    suggested_stages = [s for s in stage_suggestions if s not in selected_stages]
    if suggested_stages:
        st.caption("Suggested: " + ", ".join(suggested_stages))
    row = st.columns([4, 1])
    with row[0]:
        add_stage = st.text_input("", key="add_stage_input", placeholder="Add custom stage", label_visibility="collapsed")
    with row[1]:
        if st.button("Add Stage", key="add_stage_btn"):
            val = add_stage.strip()
            if val and val not in selected_stages:
                selected_stages.append(val)
    thesis["stages"] = selected_stages

    # 4) Ticket Size
    st.markdown("##### 💶 Ticket Size")
    current_min = int(thesis.get("ticket_min", 300_000))
    current_max = int(thesis.get("ticket_max", 2_000_000))
    slider_max = max(2_000_000, int(current_max * 2.0))
    t_min, t_max = st.slider("Ticket Size (€)", 0, slider_max, (current_min, current_max), step=50_000, format="%d")
    thesis["ticket_min"], thesis["ticket_max"] = int(t_min), int(t_max)

    st.markdown("---")
    # 5) Scoring Weights
    st.markdown("##### ⚖️ Scoring Weights (How much each dimension matters?)")
    s = thesis.get("scoring", {})
    cs1, cs2, cs3 = st.columns(3)
    with cs1:
        s["team_quality"] = st.slider("Team Quality", 0, 10, int(s.get("team_quality", 9)))
        s["tech_readiness"] = st.slider("Tech Readiness", 0, 10, int(s.get("tech_readiness", 8)))
    with cs2:
        s["market_size"] = st.slider("Market Size", 0, 10, int(s.get("market_size", 9)))
        s["geography_fit"] = st.slider("Geography Fit", 0, 10, int(s.get("geography_fit", 10)))
    with cs3:
        s["traction"] = st.slider("Traction", 0, 10, int(s.get("traction", 5)))
        s["ticket_fit"] = st.slider("Ticket Size Fit", 0, 10, int(s.get("ticket_fit", 5)))
    thesis["scoring"] = s

    st.markdown("---")
    # 6) Auto-Flag / Auto-Reject Rules
    st.markdown("##### 🚨 Auto-Flag / Auto-Reject Rules (AI suggested from your text)")
    flags = thesis.get("flags", [])
    rejects = thesis.get("rejects", [])

    fl_col, rj_col = st.columns(2)
    with fl_col:
        flag_suggestions = ["Flag if MRR < €20k", "Flag if hardware-intensive", "Flag if founder not technical"]
        cur = set(flags)
        flag_options = sorted(cur.union(flag_suggestions))
        updated_flags = []
        for opt in flag_options:
            checked = st.checkbox(opt, value=(opt in cur), key=f"flag_chk_{opt}")
            if checked:
                updated_flags.append(opt)
        new_flag = st.text_input("Add custom flag rule", key="add_flag_input")
        if st.button("Add Flag", key="add_flag_btn"):
            val = new_flag.strip()
            if val and val not in updated_flags:
                updated_flags.append(val)
        thesis["flags"] = updated_flags

    with rj_col:
        reject_suggestions = ["Reject if outside CEE", "Reject if no revenue (for Seed+)"]
        cur_r = set(rejects)
        reject_options = sorted(cur_r.union(reject_suggestions))
        updated_rejects = []
        for opt in reject_options:
            checked = st.checkbox(opt, value=(opt in cur_r), key=f"reject_chk_{opt}")
            if checked:
                updated_rejects.append(opt)
        new_reject = st.text_input("Add custom reject rule", key="add_reject_input")
        if st.button("Add Reject", key="add_reject_btn"):
            val = new_reject.strip()
            if val and val not in updated_rejects:
                updated_rejects.append(val)
        thesis["rejects"] = updated_rejects


    st.markdown("---")
    # 7) Additional Notes
    st.markdown("##### 🧠 Additional Notes (Optional)")
    thesis["notes"] = st.text_area("Additional notes", value=thesis.get("notes", ""), height=80, key="thesis_notes")

    st.markdown("---")
    csave, ctest = st.columns(2)
    with csave:
        if st.button("💾 Save Investment Thesis"):
            st.session_state.thesis_struct = thesis
            st.success("Structured thesis saved for this workstream (in memory).")
    with ctest:
        if st.button("🧪 Test Thesis on a Sample Deal"):
            st.info("Sample deal testing will be implemented later in AgentOps / simulation view.")


# -------------------------
# Card 2 – Triggers
# -------------------------

def render_triggers_card() -> None:
    st.subheader("2. Triggers – When Should the Agent Run?")
    manual_run = st.checkbox("Manual running – when files uploaded", value=True)

    st.markdown("##### Auto-run Settings")
    auto_new_file = st.checkbox("Run analysis when new file detected", value=True)
    auto_tag_company = st.checkbox("Auto-tag company name from email/filename", value=True)
    only_business_hours = st.checkbox("Only analyze during business hours")
    notify_partners = st.checkbox("Send notifications to Partners on new intake")

    st.markdown("##### Deal Routing")
    partner = st.selectbox("Assign to Partner", ["– None –", "Partner A", "Partner B", "Partner C"])
    analyst = st.selectbox("Assign to Analyst", ["– None –", "Analyst 1", "Analyst 2"])

    st.markdown("---")
    if st.button("💾 Save Trigger Settings"):
        st.success("Trigger settings saved (in memory).")


# -------------------------
# Card 3 – Source
# -------------------------

def render_source_card() -> None:
    st.subheader("3. Source – Where Does the Inbound Come From?")
    st.markdown("For manual flows, simply upload files. For auto-runs, connect your email or intake systems.")

    st.markdown("##### Manual Uploads")
    uploaded_files = st.file_uploader(
        "Upload pitch decks, IMs, transcripts, Excel models, etc.",
        accept_multiple_files=True,
    )
    if uploaded_files:
        st.info(f"{len(uploaded_files)} file(s) uploaded. In AgentOps, this workstream will process these.")

    st.markdown("##### Auto-run Settings (Intake Sources)")
    st.checkbox("Monitor shared inbox (e.g. deals@fund.com)", value=True)
    st.checkbox("Monitor Dealroom / Advisor feeds", value=True)
    st.checkbox("Monitor founder webform submissions", value=True)

    st.markdown("---")
    if st.button("💾 Save Source Settings"):
        st.success("Source settings saved (in memory).")


# -------------------------
# Card 4 – What to Look For
# -------------------------

def render_extraction_card() -> None:
    st.subheader("4. What to Look For – Extraction Settings")

    st.markdown("##### Extract From Pitch Deck")
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("Product Description", value=True)
        st.checkbox("Problem / Solution", value=True)
        st.checkbox("Team Slide", value=True)
        st.checkbox("KPIs", value=True)
        st.checkbox("Go-to-Market", value=True)
    with col2:
        st.checkbox("Tech Stack")
        st.checkbox("Market Overview", value=True)
        st.checkbox("Competitive Landscape", value=True)
        st.checkbox("Customer Segments", value=True)

    st.markdown("##### Extract From Transcript")
    col3, col4 = st.columns(2)
    with col3:
        st.checkbox("Team Answers", value=True)
        st.checkbox("Founder Signals (confidence, clarity, risk language)", value=True)
        st.checkbox("Revenue KPIs", value=True)
        st.checkbox("Red Flags", value=True)
    with col4:
        st.checkbox("Technical explanation depth")

    st.markdown("---")
    if st.button("💾 Save Extraction Settings"):
        st.success("Extraction settings saved (in memory).")


# -------------------------
# Card 5 – Data Sources
# -------------------------

def render_datasources_card() -> None:
    st.subheader("5. Data Sources Configuration")
    st.write(
        "Connect and configure external data providers the agent will use for market data, comps, competitors, team insights, news sentiment, and web intelligence."
    )

    st.markdown("##### 📊 Deal & Company Databases")
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("Crunchbase", value=True)
        st.checkbox("PitchBook", value=True)
        st.checkbox("CB Insights")
        st.checkbox("CapitalIQ")
    with col2:
        st.checkbox("Orbis")
        st.checkbox("MergerMarket")
        st.text_input("Add Custom API Key (name)", value="")

    st.markdown("##### 🧠 Market & Trend Data")
    col3, col4 = st.columns(2)
    with col3:
        st.checkbox("Statista")
        st.checkbox("Gartner")
        st.checkbox("IDC")
        st.checkbox("Euromonitor")
    with col4:
        st.checkbox("Google Trends", value=True)
        st.checkbox("Built-In Web Agent (internal web search)", value=True)
        st.multiselect(
            "Trend Scan Rules",
            ["Industry CAGR", "Geographic growth rates", "Search volume trends", "Consumer sentiment", "Regulatory changes"],
            default=["Industry CAGR", "Geographic growth rates", "Search volume trends"],
        )

    st.markdown("##### 🕸️ Web & Social Intelligence")
    st.checkbox("LinkedIn (Company + Team)")
    st.checkbox("GitHub")
    st.checkbox("Twitter/X")
    st.checkbox("Website Scraper")
    st.checkbox("Job Portal Scan (Indeed, Upwork, Toptal)")

    st.markdown("Web Analysis Settings")
    col5, col6 = st.columns(2)
    with col5:
        st.selectbox("Crawl depth", [1, 2, 3], index=1)
        st.text_input("Max runtime (seconds)", value="30")
    with col6:
        st.multiselect(
            "Extraction focus",
            ["Competitors", "Team", "Hiring", "Product", "Pricing"],
            default=["Competitors", "Team", "Product"],
        )

    st.markdown("##### 💼 Investor & Portfolio Data")
    st.checkbox("AngelList")
    st.checkbox("VCDB")
    st.checkbox("Fund proprietary CRM (HubSpot/Affinity/SFDC)")
    st.checkbox("Public GP Portfolios from fund websites (Auto-Scrape)")

    st.markdown("##### 📰 News & Sentiment Sources")
    col7, col8 = st.columns(2)
    with col7:
        st.checkbox("Google News", value=True)
        st.checkbox("TechCrunch")
        st.checkbox("VentureBeat")
    with col8:
        st.checkbox("Financial Times")
        st.checkbox("Bloomberg")
        st.text_input("Web Sentiment AI – keywords", value="lawsuit, regulatory, scandal")

    st.markdown("##### 🎛️ Data Depth & Priority")
    depth = st.radio("Depth", ["Light Scan (fast)", "Standard Scan (balanced)", "Deep Scan (slower)"], index=1)
    st.text_area(
        "Source Priority (1 = highest)",
        value="1. PitchBook\n2. Crunchbase\n3. CapitalIQ\n4. Web Scraper\n5. LinkedIn",
        height=100,
    )

    st.markdown("##### 🚨 Data Quality Rules")
    st.checkbox("Cross-check metrics between databases", value=True)
    st.checkbox("Flag inconsistent ARR / funding values", value=True)
    st.checkbox("Discard unverified sources", value=True)
    st.checkbox("Auto-note discrepancies in memo output")

    st.markdown("---")
    col_save, col_test = st.columns(2)
    with col_save:
        if st.button("💾 Save Data Source Settings"):
            st.success("Data source settings saved (in memory).")
    with col_test:
        if st.button("🧪 Run Test Scan on Sample Company"):
            st.info("Test scan simulation will be implemented later with live data integrations.")


# -------------------------
# Card 6 – Output Settings
# -------------------------

def render_output_settings_card() -> None:
    st.subheader("6. Output Settings – What Should the Agent Produce?")

    st.markdown("##### 📄 Core Outputs (Inbound Only)")
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("1-page inbound summary", value=True)
        st.checkbox("Investment thesis fit score (with explanation)", value=True)
        st.checkbox("KPI extraction (Excel, PDF tables, screenshots, PPT text)", value=True)
        st.checkbox("Red / yellow flags", value=True)
    with col2:
        st.checkbox("Suggested questions for next call", value=True)
        st.checkbox("Management profile summary", value=True)
        st.checkbox("Draft email to partner")
        st.checkbox("Auto-create CRM note")

    st.markdown("##### 🧠 Claim vs Reality Validation")
    st.checkbox("Market claims vs. real market data", value=True)
    st.checkbox("Growth claims vs. financials + benchmarks", value=True)
    st.checkbox("Competition slide vs. actual competitors", value=True)
    st.checkbox("Tech claims vs. stack, repos, team profiles", value=True)
    st.checkbox("Traction claims vs. LinkedIn hiring, web traffic, funding databases", value=True)

    st.markdown("Validation Output Format")
    st.radio(
        "Format",
        [
            "Show “Pitch says → Data says → Conclusion”",
            "Only show mismatches",
            "Only show validated claims",
        ],
        index=0,
    )

    st.markdown("Validation Labels (auto-generated)")
    st.checkbox("Good — pitch matches reality + thesis", value=True)
    st.checkbox("Possible — plausible but unverified", value=True)
    st.checkbox("Question — unclear or contradictory", value=True)
    st.checkbox("Bad — contradicts data or violates thesis", value=True)

    st.markdown("##### 🗂 Supported Input Types")
    col3, col4 = st.columns(2)
    with col3:
        st.checkbox("PDF (pitch decks, IMs)", value=True)
        st.checkbox("PPT / PPTX (native slide parsing)", value=True)
        st.checkbox("Excel (financial models, KPI tables)", value=True)
    with col4:
        st.checkbox("Images of slides (OCR)", value=True)
        st.checkbox("Transcripts (calls, Zoom, emails)", value=True)
        st.checkbox("Video pitch parsing (coming soon)")

    st.markdown("##### 📑 Output Depth")
    st.radio(
        "Output depth",
        ["Light – fit score + 3 bullets", "Standard – full inbound summary", "Deep – extended inbound memo (2–3 pages)"],
        index=1,
    )

    st.markdown("##### 🔁 After Output Is Generated – Automations")
    st.checkbox("Suggest scheduling a call", value=True)
    st.checkbox("Notify partner automatically")
    st.checkbox("Push summary to CRM draft")
    st.checkbox("Auto-run Market Intelligence Agent")
    st.checkbox("Auto-generate “Missing Information” list for founder")

    st.markdown("---")
    if st.button("💾 Save Output Settings"):
        st.success("Output settings saved (in memory).")
