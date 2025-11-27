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
    st.subheader("1. Define Investment Thesis")
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
            "tactical_focus": "",
            "notes": "We prefer founder-led companies, avoid government-heavy sectors.",
            "financial_metrics": {
                "revenue_metrics": "N/A",
                "ebitda": "N/A",
                "arr": 0,
                "growth": 0,
                "ltv_cac_ratio": 0.0,
                "gross_margin": 0,
                "profitable": False,
                "retention": 0,
            },
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
            st.info("Template suggestions not implemented yet. Use Convert.")
    with c2:
        if st.button("Convert"):
            if not thesis_text.strip():
                st.error("Please enter a thesis description before parsing.")
            else:
                with st.spinner("Parsing thesis with AI..."):
                    data = parse_investment_thesis(thesis_text, client)
                    st.session_state.thesis_struct = data
                    thesis = data
                st.success("Thesis parsed and populated.")

    st.markdown("---")
    st.subheader("🧠 AI-Extracted Thesis Components (Editable)")

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
        new_sector = st.text_input("Add custom sector", key="add_sector_input", placeholder="Add custom sector", label_visibility="collapsed")
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
        new_geo = st.text_input("Add custom region", key="add_geo_input", placeholder="Add custom region", label_visibility="collapsed")
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
        add_stage = st.text_input("Add custom stage", key="add_stage_input", placeholder="Add custom stage", label_visibility="collapsed")
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
    t_min, t_max = st.slider("Ticket Size (€)", 0, slider_max, (current_min, current_max), step=50_000, format="%d", key="thesis_ticket_size")
    thesis["ticket_min"], thesis["ticket_max"] = int(t_min), int(t_max)

    st.markdown("---")
    # 5) Traction & Metrics (range sliders with adjustable endpoints)
    st.markdown("##### 📊 Traction & Metrics")

    # Initialize unified metrics structure with defaults and include Ticket Size
    if "metrics" not in thesis:
        tmin = int(thesis.get("ticket_min", 300_000))
        tmax = int(thesis.get("ticket_max", 2_000_000))
        ticket_domain = max(2_000_000, int(tmax * 2.0))
        thesis["metrics"] = {
            "Revenue (€)": {"domain_max": 5_000_000, "range": (0, 1_000_000), "step": 50_000, "type": "int"},
            "EBITDA (€)": {"domain_max": 2_000_000, "range": (0, 500_000), "step": 50_000, "type": "int"},
            "ARR (€)": {"domain_max": 5_000_000, "range": (0, 1_000_000), "step": 100_000, "type": "int"},
            "Growth (%)": {"domain_max": 300, "range": (0, 100), "step": 1, "type": "int"},
            "LTV : CAC (x)": {"domain_max": 10.0, "range": (0.0, 3.0), "step": 0.1, "type": "float"},
            "Gross Margin (%)": {"domain_max": 100, "range": (0, 60), "step": 1, "type": "int"},
        }

    metrics = thesis.get("metrics", {})

    # Keep Ticket Size metric synced with top-level ticket_min/ticket_max each render
    if "Ticket Size (€)" in metrics:
        cur_tmin = int(thesis.get("ticket_min", 300_000))
        cur_tmax = int(thesis.get("ticket_max", 2_000_000))
        metrics["Ticket Size (€)"]["domain_max"] = max(2_000_000, int(cur_tmax * 2.0))
        metrics["Ticket Size (€)"]["range"] = (cur_tmin, cur_tmax)

    # Suggested defaults not yet present
    metric_suggestions = [
        "Revenue (€)", "EBITDA (€)", "ARR (€)", "Growth (%)",
        "LTV : CAC (x)", "Gross Margin (%)", "Retention (%)", "MRR (%)", "Churn (%)"
    ]


    # Helper to create safe Streamlit keys
    def _keyify(label: str) -> str:
        return "".join(ch if ch.isalnum() else "_" for ch in label).lower()

    # Render metric controls in three columns
    names = list(metrics.keys())
    cols = st.columns(3)
    for idx, name in enumerate(names):
        cfg = metrics[name]
        is_float = cfg.get("type") == "float"
        col = cols[idx % 3]
        with col:
            if is_float:
                dom_max = float(cfg.get("domain_max", 100.0))
                cur_min, cur_max = cfg.get("range", (0.0, float(dom_max)))
                cur_min = float(cur_min)
                cur_max = min(float(cur_max), float(dom_max))
                new_min, new_max = st.slider(
                    name,
                    min_value=0.0,
                    max_value=float(dom_max),
                    value=(float(cur_min), float(cur_max)),
                    step=float(cfg.get("step", 0.1)),
                    key=f"{_keyify(name)}_slider_float",
                )
                # Auto-expand max if user reaches the cap; keeps UI as slider-only
                if float(new_max) >= float(dom_max):
                    metrics[name]["domain_max"] = float(dom_max * 2.0)
                else:
                    metrics[name]["domain_max"] = float(dom_max)
                metrics[name]["range"] = (float(new_min), float(new_max))
            else:
                dom_max = int(cfg.get("domain_max", 100))
                cur_min, cur_max = cfg.get("range", (0, int(dom_max)))
                cur_min = int(cur_min)
                cur_max = min(int(cur_max), int(dom_max))
                new_min, new_max = st.slider(
                    name,
                    min_value=0,
                    max_value=int(dom_max),
                    value=(int(cur_min), int(cur_max)),
                    step=int(cfg.get("step", 1)),
                    key=f"{_keyify(name)}_slider_int",
                    format="%d" if "€" in name else None,
                )
                # Auto-expand max if user reaches the cap; keeps UI as slider-only
                if int(new_max) >= int(dom_max):
                    metrics[name]["domain_max"] = int(dom_max * 2)
                else:
                    metrics[name]["domain_max"] = int(dom_max)
                metrics[name]["range"] = (int(new_min), int(new_max))

            # Keep Ticket Size in sync with top-level ticket_min/ticket_max
            if name == "Ticket Size (€)":
                thesis["ticket_min"], thesis["ticket_max"] = int(metrics[name]["range"][0]), int(metrics[name]["range"][1])

    # Add a custom metric
    st.markdown("---")
    st.markdown("##### Add Custom Metric")

    missing_suggestions = [m for m in metric_suggestions if m not in metrics]
    if missing_suggestions:
        st.caption("Suggested: " + ", ".join(missing_suggestions))

    col_add_input, col_add_btn = st.columns([4, 1])
    with col_add_input:
        new_metric_input = st.text_input(
            "",
            key="add_metric_input",
            placeholder="Add new metric (Name;Max Value;Sign, e.g., 'Retention;100;%')",
            label_visibility="collapsed" # Added to prevent double label, aligning better with the button
        )
    with col_add_btn:
        # Custom CSS to align the button vertically with the text input
        
        if st.button("Add Metric", key="add_metric_btn"):
            parts = [p.strip() for p in new_metric_input.split(';')]
            if len(parts) == 3:
                name, max_val_str, sign = parts
                try:
                    max_val = float(max_val_str)
                    if name and f"{name} ({sign})" not in metrics:
                        metric_type = "float" if "." in max_val_str else "int"
                        metrics[f"{name} ({sign})"] = {
                            "domain_max": max_val,
                            "range": (0.0 if metric_type == "float" else 0, max_val),
                            "step": 0.1 if metric_type == "float" else 1,
                            "type": metric_type,
                        }
                        st.success(f"Metric '{name} ({sign})' added.")
                    else:
                        st.warning("Metric already exists or name is empty.")
                except ValueError:
                    st.error("Max Value must be a number.")
            else:
                st.error("Please use format: Name;Max Value;Sign (e.g., 'Retention;100;%')")

    # Remove custom metrics
    st.markdown("---")
    st.markdown("##### Remove Metrics")
    default_metrics = [
        
    ]
    custom_metrics = [name for name in metrics.keys() if name not in default_metrics]

    if custom_metrics:
        col_select, col_button = st.columns([4, 1])
        with col_select:
            metric_to_remove = st.selectbox(
                "Select metric to remove",
                [""] + custom_metrics,
                key="remove_metric_selectbox",
                label_visibility="collapsed" # Hide label to save space
            )
        with col_button:
            if st.button("Remove Metric", key="remove_metric_btn") and metric_to_remove:
                del metrics[metric_to_remove]
                st.success(f"Metric '{metric_to_remove}' removed.")
                # Force a rerun to update the display immediately
                st.experimental_rerun()
    else:
        st.info("No custom metrics to remove.")

    # Persist metrics back onto thesis
    thesis["metrics"] = metrics

    st.markdown("---")
    # 6) Scoring Weights
    st.markdown("##### ⚖️ Scoring Weights (How much each dimension matters?)")
    s = thesis.get("scoring", {})
    cs1, cs2, cs3 = st.columns(3)
    with cs1:
        s["team_quality"] = st.slider("Team Quality", 0, 10, int(s.get("team_quality", 9)))
        s["tech_readiness"] = st.slider("Tech Readiness", 0, 10, int(s.get("tech_readiness", 8)))
    with cs2:
        s["market_size"] = st.slider("Market", 0, 10, int(s.get("market_size", 9)))
        s["geography_fit"] = st.slider("Geography Fit", 0, 10, int(s.get("geography_fit", 10)))
    with cs3:
        s["traction"] = st.slider("Traction", 0, 10, int(s.get("traction", 5)))
        s["ticket_fit"] = st.slider("Ticket Size Fit", 0, 10, int(s.get("ticket_fit", 5)))
    thesis["scoring"] = s

    st.markdown("---")
    # 6) Auto-Flag / Auto-Reject Rules
    st.markdown("##### 🚨 Auto-Flag Rules (AI suggested from your text)")
    flags = thesis.get("flags", [])

    flag_suggestions = ["Flag if MRR < €20k", "Flag if hardware-intensive", "Flag if founder not technical"]
    cur = set(flags)
    flag_options = sorted(cur.union(flag_suggestions))
    updated_flags = []
    for opt in flag_options:
        checked = st.checkbox(opt, value=(opt in cur), key=f"flag_chk_{opt}")
        if checked:
            updated_flags.append(opt)
    row_flag_input = st.columns([4, 1])
    with row_flag_input[0]:
        new_flag = st.text_input("Add custom flag rule", key="add_flag_input", label_visibility="collapsed")
    with row_flag_input[1]:
        if st.button("Add Flag", key="add_flag_btn"):
            val = new_flag.strip()
            if val and val not in updated_flags:
                updated_flags.append(val)
    thesis["flags"] = updated_flags

    st.markdown("##### 🚫 Auto-Reject Rules (AI suggested from your text)")
    rejects = thesis.get("rejects", [])

    reject_suggestions = ["Reject if outside CEE", "Reject if no revenue (for Seed+)"]
    cur_r = set(rejects)
    reject_options = sorted(cur_r.union(reject_suggestions))
    updated_rejects = []
    for opt in reject_options:
        checked = st.checkbox(opt, value=(opt in cur_r), key=f"reject_chk_{opt}")
        if checked:
            updated_rejects.append(opt)
    
    row_reject_input = st.columns([4, 1])
    with row_reject_input[0]:
        new_reject = st.text_input("Add custom reject rule", key="add_reject_input", label_visibility="collapsed")
    with row_reject_input[1]:
        if st.button("Add Reject", key="add_reject_btn"):
            val = new_reject.strip()
            if val and val not in updated_rejects:
                updated_rejects.append(val)
    thesis["rejects"] = updated_rejects


    st.markdown("---")
    # 7) Tactical Focus
    st.markdown("##### 🎯 Tactical Focus (Optional)")
    thesis["tactical_focus"] = st.text_area(
        "Short-term priorities driven by macro trends, market cycles, or the fund’s deployment phase.",
        value=thesis.get("tactical_focus", ""),
        height=80,
        key="thesis_tactical_focus",
    )

    st.markdown("---")
    # 8) Additional Notes
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
            st.info("Sample deal testing will be implemented later in AgentWorkspace / simulation view.")


# -------------------------
# Card 2 – Triggers
# -------------------------

def render_triggers_card() -> None:
    st.subheader("2. Triggers – When Should the Agent Run?")
    trigger_type = st.selectbox(
        "Choose Trigger Type",
        ["Manual running – when files uploaded", "Automatic running"],
        index=0, # Default to Manual
        key="trigger_type_select"
    )

    if trigger_type == "Automatic running":
        st.markdown("##### Auto-run Settings")
        auto_new_file = st.checkbox("Run analysis when new file detected", value=True)
        auto_tag_company = st.checkbox("Auto-tag company name from email/filename", value=True)
        monitor_shared_inbox = st.checkbox("Monitor shared inbox (e.g. deals@fund.com)", value=True)
        monitor_dealroom = st.checkbox("Monitor Dealroom / Advisor feeds", value=True)
        monitor_founder = st.checkbox("Monitor founder webform submissions", value=True)
        only_business_hours = st.checkbox("Only analyze during business hours")
        notify_partners = st.checkbox("Send notifications to Partners on new intake")

    st.markdown("##### Deal Routing")
    partner = st.selectbox("Assign to Partner", ["– None –", "Partner A", "Partner B", "Partner C"])
    analyst = st.selectbox("Assign to Analyst", ["– None –", "Analyst 1", "Analyst 2"])

    st.markdown("---")
    if st.button("💾 Save Trigger Settings"):
        st.success("Trigger settings saved (in memory).")



# -------------------------
# Card 3 – Output Settings
# -------------------------

def render_output_settings_card() -> None:
    st.subheader("3. Output Settings – What Should the Agent Produce?")

    st.markdown("##### Extract From Pitch Deck")
    col1, col2, col3_pitch = st.columns(3)
    with col1:
        st.checkbox("Product Description", value=True)
        st.checkbox("Problem / Solution", value=True)
        st.checkbox("Team Slide", value=True)
    with col2:
        st.checkbox("KPIs", value=True)
        st.checkbox("Go-to-Market", value=True)
        st.checkbox("Tech Stack")
    with col3_pitch:
        st.checkbox("Market Overview", value=True)
        st.checkbox("Competitive Landscape", value=True)
        st.checkbox("Customer Segments", value=True)

    st.divider()
    st.markdown("##### Extract From Transcript")
    col4, col5, col6_transcript = st.columns(3)
    with col4:
        st.checkbox("Team Answers", value=True)
        st.checkbox("Technical explanation depth")
    with col5:
        st.checkbox("Revenue KPIs", value=True)
        st.checkbox("Red Flags", value=True)
    with col6_transcript:
        st.checkbox("Founder Signals (confidence, clarity, risk language)", value=True)


    st.divider()

    # Ensure settings exist (init_session_state sets this)
    settings = st.session_state.get("output_settings", None)
    if settings is None:
        st.warning("Output Settings not initialized. Please reload the page.")
        return

    modules = settings.get("modules", {})
    # Fallback to a sensible current module if needed
    enabled_names = [n for n, m in modules.items() if m.get("enabled")]
    if "current_output_module" not in st.session_state:
        st.session_state.current_output_module = enabled_names[0] if enabled_names else (list(modules.keys())[0] if modules else None)

    # Left: module checklist. Right: prompt editor that pops when a module is enabled.
    col_left, col_right = st.columns([3, 5], gap="large")

    with col_left:
        st.markdown("##### 📄 Core Output Modules")
        # Render checkboxes in a compact layout
        for name, mod in modules.items():
            prev = bool(mod.get("enabled", False))
            cur = st.checkbox(name, value=prev, key=f"outmod_{name}")
            if cur != prev:
                modules[name]["enabled"] = cur
                # If just enabled, make it the active module for editing
                if cur:
                    st.session_state.current_output_module = name



    with col_right:
        enabled_names = [n for n, m in modules.items() if m.get("enabled")]
        if enabled_names:
            current = st.session_state.get("current_output_module", enabled_names[0])
            if current not in enabled_names:
                current = enabled_names[0]
            sel = st.selectbox("Editing module", enabled_names, index=enabled_names.index(current))
            st.session_state.current_output_module = sel
            st.caption("Tip: tick a module or select it here to edit its prompt on the right.")
        else:
            st.info("Enable at least one module to edit its prompt.")
            
        edit_name = st.session_state.get("current_output_module", None)
        if edit_name and modules.get(edit_name, {}).get("enabled"):
            st.markdown(f"##### ✏️ Prompt – {edit_name}")
            prompt_key = f"prompt_editor_{edit_name}"
            current_prompt = modules[edit_name].get("prompt", "")
            # Editor
            st.text_area(
                "Edit the generation prompt for this module",
                value=current_prompt,
                height=280,
                key=prompt_key,
            )
            # Buttons stacked to avoid multi-level nested columns
            if st.button("Save Prompt", key=f"save_prompt_{edit_name}"):
                modules[edit_name]["prompt"] = st.session_state.get(prompt_key, current_prompt)
                st.success("Prompt saved.")
            if st.button("Reset to Default", key=f"reset_prompt_{edit_name}"):
                defaults = st.session_state.get("output_default_prompts", {})
                default_text = defaults.get(edit_name, current_prompt)
                modules[edit_name]["prompt"] = default_text
                st.session_state[prompt_key] = default_text
                st.info("Reset to default prompt.")
        else:
            st.info("Select a module on the left to edit its prompt.")

    st.markdown("---")
    st.markdown("##### 🧠 Claim vs Reality Validation")
   
    checks = settings["validation"].get("checks", {})
    c1, c2 = st.columns(2)
    items = list(checks.items())
    for i, (label, val) in enumerate(items):
        col = c1 if i % 2 == 0 else c2
        with col:
            checks[label] = st.checkbox(label, value=bool(val), key=f"validation_check_{label}")
    settings["validation"]["checks"] = checks

    st.markdown("##### 🏷️ Validation Labels")
    labels = settings.get("labels", {})
    descriptions = {
        "Good": "Good – pith matches reality and thesis",
        "Possible": "Possible – plausible but unverified",
        "Question": "Question – unclear or contradictory",
        "Bad": "Bad – contradicts data or violates thesis"
    }
    for i, lbl in enumerate(["Good", "Possible", "Question", "Bad"]):
        labels[lbl] = st.checkbox(descriptions[lbl], value=bool(labels.get(lbl, True)), key=f"validation_label_{lbl}")
    settings["labels"] = labels

    st.markdown("##### 🔁 After Output Is Generated")
    post = settings.get("post", {})
    post["flags_red_yellow"] = st.checkbox("Flags (Red/Yellow)", value=bool(post.get("flags_red_yellow", False)))
    settings["post"] = post

    st.markdown("---")
    if st.button("💾 Save Output Settings"):
        # Persist back
        st.session_state.output_settings = settings
        st.success("Output settings saved (in memory).")


# -------------------------
# Card 4 – Data Sources
# -------------------------

def render_datasources_card() -> None:
    st.subheader("4. Data Sources Configuration")
    st.write(
        "Connect and configure external data providers the agent will use for market data, comps, competitors, team insights, news sentiment, and web intelligence."
    )

    st.markdown("##### 📊 Deal & Company Databases")
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("Company Database", value=True)
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
        st.checkbox("Company Database Market Data", value=True)
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

    st.markdown("---")
    col_save, col_test = st.columns(2)
    with col_save:
        if st.button("💾 Save Data Source Settings"):
            st.success("Data source settings saved (in memory).")
    with col_test:
        if st.button("🧪 Run Test Scan on Sample Company"):
            st.info("Test scan simulation will be implemented later with live data integrations.")
