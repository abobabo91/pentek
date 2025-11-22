
import os
import streamlit as st
from openai import OpenAI

# =========================
# ---- Basic Setup --------
# =========================

st.set_page_config(page_title="AgentLab & AgentOps", layout="wide")
st.title("🤖 AI Agent Workspace")

# Sidebar navigation
SECTION = st.sidebar.radio("Navigation", ["AgentLab", "AgentOps"])

# =========================
# ---- OpenAI Client ------#
# =========================

def get_api_key() -> str:
    try:
        return st.secrets["openai"]["OPENAI_API_KEY"]
    except Exception:
        return os.environ.get("OPENAI_API_KEY", "")

api_key = get_api_key()
if not api_key:
    st.error("Missing OpenAI API key. Please set OPENAI_API_KEY in env or Streamlit secrets.")
    st.stop()

client = OpenAI(api_key=api_key, timeout=600)

# =========================
# ---- Session State ------#
# =========================

if "inbound_workstreams" not in st.session_state:
    # Example default workstreams for Inbound Sourcing Agent
    st.session_state.inbound_workstreams = {
        "Inbound Email Screening": {"status": "Active"},
        "Manual Upload Screening": {"status": "Active"},
        "Advisor/Dealroom Sync": {"status": "Paused"},
        "Founder Webform Intake": {"status": "Active"},
    }

if "current_workstream" not in st.session_state:
    st.session_state.current_workstream = None

if "creating_workstream" not in st.session_state:
    st.session_state.creating_workstream = False

if "parsed_thesis_markdown" not in st.session_state:
    st.session_state.parsed_thesis_markdown = ""

# =========================
# ---- Helper: AI Call ----#
# =========================

def parse_investment_thesis(thesis_text: str) -> str:
    """
    Uses OpenAI to parse a free-text investment thesis into structured,
    human-readable components (Markdown).
    """
    system_msg = (
        "You are an assistant helping a VC/PE fund configure an inbound sourcing agent. "
        "The user provides a free-text investment thesis. "
        "You MUST extract and structure it into components:\n"
        "- Sector focus\n"
        "- Geography fit\n"
        "- Stage\n"
        "- Ticket size (min / max)\n"
        "- Scoring weights (0–10) for: Team Quality, Tech Readiness, Market Size, Geography Fit, Traction, Ticket Size Fit\n"
        "- Auto-flag / Auto-reject rules\n"
        "- Additional notes\n\n"
        "Output STRICTLY in Markdown with clear headings and bullet lists. "
        "Do NOT include any JSON. Be concise but concrete."
    )
    user_msg = f"Free-text investment thesis:\n\n{thesis_text}"

    try:
        resp = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
        )
        # SDK convenience: output_text contains concatenated text
        parsed = getattr(resp, "output_text", None)
        if not parsed:
            # Fallback: best-effort extraction from response object
            try:
                first = resp.output[0].content[0].text.value
                parsed = first
            except Exception:
                parsed = "Could not parse response from model."
        return parsed
    except Exception as e:
        return f"⚠️ Error while calling AI: {e}"

# =========================
# ---- UI: AgentLab -------#
# =========================

def render_agentlab():
    st.header("🧪 AgentLab – Agent Setup")

    col_left, col_right = st.columns([1, 3], gap="large")

    with col_left:
        st.markdown("### Agent Navigation")
        category = st.selectbox(
            "Category",
            ["Sourcing", "Research (coming soon)", "Portfolio (coming soon)", "Deal Desk (coming soon)"],
            index=0,
        )

        if category == "Sourcing":
            agent_type = st.selectbox(
                "Agent",
                ["Inbound Sourcing Agent", "Outbound Sourcing Agent (coming soon)"],
                index=0,
            )
        else:
            agent_type = "Placeholder"

        if category == "Sourcing" and agent_type.startswith("Inbound"):
            st.markdown("#### Workstreams")
            st.caption("AgentLab > Sourcing > Inbound Agent > Workstreams")

            # Create New Workstream button
            if st.button("➕ Create New Workstream", use_container_width=True):
                st.session_state.creating_workstream = True
                st.session_state.current_workstream = None

            st.markdown("**Existing Workstreams**")
            st.divider()

            # List existing workstreams
            to_delete = None
            for name, cfg in list(st.session_state.inbound_workstreams.items()):
                status = cfg.get("status", "Active")
                row_cols = st.columns([3, 1, 1, 1])
                with row_cols[0]:
                    st.markdown(f"**• {name}**")
                    st.caption(f"Status: {status}")
                with row_cols[1]:
                    if st.button("Configure", key=f"cfg_{name}"):
                        st.session_state.current_workstream = name
                        st.session_state.creating_workstream = False
                with row_cols[2]:
                    toggle_label = "Pause" if status == "Active" else "Activate"
                    if st.button(toggle_label, key=f"toggle_{name}"):
                        st.session_state.inbound_workstreams[name]["status"] = (
                            "Paused" if status == "Active" else "Active"
                        )
                with row_cols[3]:
                    if st.button("Delete", key=f"del_{name}"):
                        to_delete = name
                st.markdown("---")

            if to_delete:
                st.session_state.inbound_workstreams.pop(to_delete, None)
                if st.session_state.current_workstream == to_delete:
                    st.session_state.current_workstream = None

        else:
            st.info("Select **Sourcing → Inbound Sourcing Agent** to configure inbound workstreams.")

    # Right side: Workstream configuration area
    with col_right:
        if st.session_state.creating_workstream:
            render_new_workstream_form()
        elif st.session_state.current_workstream:
            render_workstream_detail(st.session_state.current_workstream)
        else:
            st.markdown("### No Workstream Selected")
            st.caption("Choose an existing workstream or create a new one from the left panel.")

# -------------------------
# New Workstream Form
# -------------------------

def render_new_workstream_form():
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

def render_workstream_detail(name: str):
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
        render_thesis_card()

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

# -------------------------
# Card 1 – Investment Thesis
# -------------------------

def render_thesis_card():
    st.subheader("DEFINE INVESTMENT THESIS")
    st.write(
        "Describe your fund’s investment logic. AI will extract and structure it into thesis components automatically."
    )

    example_text = (
        "We invest in CEE-based SaaS, AI and HRtech companies at Seed/Series A stage, ideally with €20–100k MRR, "
        "strong technical founders, and early signs of scalability. We avoid deep hardware, crypto, and biotech. "
        "Geography: CEE + DACH optional. Ticket size €300k–€2M."
    )

    thesis_text = st.text_area(
        "✍️ Free-Text Thesis Description",
        value=example_text,
        height=200,
        help="Write in your own language; AI will interpret.",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Suggest Thesis Elements"):
            st.info("In a later step, this can generate suggestions based on templates. For now, use 'Parse Automatically'.")
    with col2:
        if st.button("Parse Automatically"):
            if not thesis_text.strip():
                st.error("Please enter a thesis description before parsing.")
            else:
                with st.spinner("Parsing thesis with AI..."):
                    parsed = parse_investment_thesis(thesis_text)
                    st.session_state.parsed_thesis_markdown = parsed

    st.markdown("---")
    st.subheader("🧠 AI-EXTRACTED THESIS COMPONENTS (Editable)")

    if st.session_state.parsed_thesis_markdown:
        st.markdown(st.session_state.parsed_thesis_markdown)
    else:
        st.caption("Run **Parse Automatically** to see AI-extracted components here.")

    st.markdown("##### Scoring Weights (How much each dimension matters?)")
    cols = st.columns(3)
    with cols[0]:
        team_quality = st.slider("Team Quality", 0, 10, 9)
        tech_readiness = st.slider("Tech Readiness", 0, 10, 8)
    with cols[1]:
        market_size = st.slider("Market Size", 0, 10, 9)
        geography_fit = st.slider("Geography Fit", 0, 10, 10)
    with cols[2]:
        traction = st.slider("Traction", 0, 10, 5)
        ticket_fit = st.slider("Ticket Size Fit", 0, 10, 5)

    st.markdown("##### 🚨 Auto-Flag / Auto-Reject Rules")
    col_a, col_b = st.columns(2)
    with col_a:
        flag_low_mrr = st.checkbox("Flag if MRR < €20k", value=True)
        flag_hardware = st.checkbox("Flag if hardware-intensive", value=True)
        flag_non_technical = st.checkbox("Flag if founder not technical", value=True)
    with col_b:
        reject_outside_geo = st.checkbox("Reject if outside CEE")
        reject_no_revenue = st.checkbox("Reject if no revenue (for Seed+)")

    st.markdown("Auto-Reject Logic Examples:")
    st.code(
        "IF geography not in allowed list → [auto-pass] [auto-reject] [flag only]\n"
        "IF stage mismatch by 2+ levels  → [auto-pass] [auto-reject] [flag only]",
        language="text",
    )

    st.markdown("##### 🧠 Additional Notes (Optional)")
    notes = st.text_area(
        "Additional notes",
        value="We prefer founder-led companies, avoid government-heavy sectors.",
        height=80,
    )

    st.markdown("---")
    col_save, col_test = st.columns(2)
    with col_save:
        if st.button("💾 Save Investment Thesis"):
            st.success("Investment thesis settings saved for this workstream (in memory for now).")
    with col_test:
        if st.button("🧪 Test Thesis on a Sample Deal"):
            st.info("Sample deal testing will be implemented later in AgentOps / simulation view.")

# -------------------------
# Card 2 – Triggers
# -------------------------

def render_triggers_card():
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

def render_source_card():
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

def render_extraction_card():
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

def render_datasources_card():
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

def render_output_settings_card():
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

# =========================
# ---- UI: AgentOps -------#
# =========================


def render_agentops():
    st.header("⚙️ AgentOps – Inbound Operations")

    st.markdown("## 📥 Automatic Inbox")
    st.caption("New deals processed automatically based on your AgentLab rules.")

    st.table([
        {"Company": "AtWork", "Source": "Gmail", "Summary": "Ready", "Fit": "82%", "Action": "Open"},
        {"Company": "NovaCRM", "Source": "Drive", "Summary": "Ready", "Fit": "41%", "Action": "Open"},
        {"Company": "FlowOps", "Source": "Email", "Summary": "Ready", "Fit": "67%", "Action": "Open"},
        {"Company": "EdgeAI", "Source": "Webform", "Summary": "Ready", "Fit": "74%", "Action": "Open"},
    ])

    st.markdown("### Filters")
    st.multiselect("Filter results", ["Hot (80%+)", "Needs Info", "Low Fit", "New"])

    st.markdown("---")
    st.markdown("## 🧳 Manual Upload")
    uploaded_files = st.file_uploader(
        "Upload decks, IMs, transcripts for instant manual analysis.",
        accept_multiple_files=True
    )

    if uploaded_files:
        st.write("Uploaded Files:")
        for f in uploaded_files:
            st.write("•", f.name)

    if st.button("Run Analysis"):
        st.success("Manual analysis started (stub).")

    st.markdown("---")
    st.markdown("## 📤 Download & Export")

    export_format = st.radio(
        "Export Format",
        ["Web View", "PDF", "Word (.docx)", "PowerPoint (.pptx)", "Notion Page", "Slack Share"],
        index=0,
    )

    included = st.multiselect(
        "Included in Export",
        [
            "1-page summary",
            "KPI extraction table",
            "Fit score + explanation",
            "Red / yellow flags",
            "Claim vs Reality section",
            "Suggested questions",
            "Management profiles",
            "Attach original files",
        ],
        default=[
            "1-page summary",
            "KPI extraction table",
            "Fit score + explanation",
            "Red / yellow flags",
            "Claim vs Reality section",
            "Suggested questions",
        ],
    )

    st.checkbox("Remove internal notes", value=True)
    st.checkbox("Show scoring model")
    st.checkbox("Include timestamp & analyst initials")

    st.markdown("---")
    st.button("Export Summary")
    st.button("Open Web Version")


if SECTION == "AgentOps":
    render_agentops()
