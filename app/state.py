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

# -------------------------
# Output Settings defaults and helpers
# -------------------------

# Order of modules as per spec
OUTPUT_MODULE_ORDER = [
    "Executive Summary",
    "Deal Summary",
    "Propose Next Steps",
    "KPI & Financial Summary",
    "Fund Fit",
    "Product/tech differentiation, defensibility",
    "Business model & unit economics",
    "Team",
    "Funding",
    "News",
    "Website visitors",
    "People",
]

# Default prompt for Executive Summary (from attached spec image; normalized to plain quotes)
EXECUTIVE_SUMMARY_DEFAULT_PROMPT = '''Generate a concise Executive Summary of the deal, based solely on the materials provided (pitch deck, IM, transcript, Excel, website data, external sources if enabled).

The Executive Summary must include:
- What the company does
- Why it exists / problem solved
- Product overview
- Target market & ideal customer
- Early traction signals (if any)
- Team snapshot (founders, senior roles)
- High-level financial snapshot (if available)
- Key risks or uncertainties (only the most essential)
- One-sentence investment takeaway (why this matters)

Tone:
- Brief, factual, investment-ready, partner-level.
- Avoid hype, avoid repetition, avoid unverified claims.
- If data is missing, state explicitly: "Data not provided."

If other output modules are also selected in settings (e.g., KPIs, Fund Fit, Business Model, Claim vs Reality), do NOT repeat their content — the Executive Summary should remain a tight 1–3 paragraph overview.'''

def default_prompt_for_module(name: str) -> str:
    """Return default prompt for a given output module."""
    if name == "Executive Summary":
        return EXECUTIVE_SUMMARY_DEFAULT_PROMPT
    if name == "Deal Summary":
        return "Produce a structured deal summary including: company basics, product, market, traction, business model, funding history, ownership (if available), and current ask. Keep it factual and cite missing data explicitly."
    if name == "Propose Next Steps":
        return "Based on the materials and open questions, propose 3–7 concrete next steps for the investment process. Prioritize for Partners vs Analysts and include data requests where appropriate."
    if name == "KPI & Financial Summary":
        return "Summarize the key KPIs and available financials into a compact list/table-oriented narrative. Include ARR/MRR, growth, gross margin, retention/churn, LTV:CAC where present. Note any inconsistencies."
    if name == "Fund Fit":
        return "Assess fund fit against the configured investment thesis (sectors, geography, stage, ticket). Provide a brief explanation and a 0–10 fit score."
    if name == "Product/tech differentiation, defensibility":
        return "Explain the product/technology differentiation and likely defensibility. Reference evidence from docs, stack, repos, patents, team expertise if available."
    if name == "Business model & unit economics":
        return "Describe the business model and unit economics. Outline revenue model, pricing, sales motion, key unit economics (e.g., LTV, CAC) if available."
    if name == "Team":
        return "Summarize the founding and leadership team, roles, and notable experience. Highlight strengths and potential gaps relevant to execution risk."
    if name == "Funding":
        return "Outline funding history, investors, round sizes, dates, and current raise/terms if available. Flag discrepancies across sources."
    if name == "News":
        return "Summarize notable recent news and sentiment relevant to the company. Avoid speculation; cite facts and timing."
    if name == "Website visitors":
        return "Summarize available web traffic signals (e.g., SimilarWeb, Google Trends proxies if enabled). Note limitations and data freshness."
    if name == "People":
        return "Summarize headcount, hiring velocity, and org snapshot from LinkedIn or other sources if enabled."
    # Fallback
    return f"Generate a concise section for: {name}. Keep it factual, brief, and note missing data explicitly."

def build_default_output_settings() -> dict:
    """Construct default Output Settings structure for session state."""
    modules = {name: {"enabled": (name == "Executive Summary"), "prompt": default_prompt_for_module(name)} for name in OUTPUT_MODULE_ORDER}
    validation_checks = {
        "Market claims vs. available market data": False,
        "Growth claims vs. financials + benchmarks": False,
        "Competition slide vs. actual competitors": False,
        "Tech claims vs. stack, reports, team profiles": False,
        "Traction claims vs. LinkedIn hiring, web traffic, funding databases": False,
    }
    return {
        "modules": modules,
        "validation": {
            "enabled": False,
            "checks": validation_checks,
        },
        "labels": {
            "Good": True,
            "Possible": True,
            "Question": True,
            "Bad": True,
        },
        "post": {
            "flags_red_yellow": False,  # Placeholder for after-output flags
        },
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

    # Output Settings: modules + prompts + validation/labels + post placeholders
    if "output_settings" not in st.session_state:
        st.session_state.output_settings = build_default_output_settings()

    # For prompt reset convenience
    if "output_default_prompts" not in st.session_state:
        st.session_state.output_default_prompts = {name: default_prompt_for_module(name) for name in OUTPUT_MODULE_ORDER}

    # Editor selection for prompt side-panel
    if "current_output_module" not in st.session_state:
        st.session_state.current_output_module = "Executive Summary"
