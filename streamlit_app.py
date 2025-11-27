"""
Streamlit entrypoint kept minimal by delegating to the app package.

Refactor summary:
- app/config.py: page setup, navigation, OpenAI client
- app/state.py: session_state initialization
- app/services.py: AI/service helpers (e.g., parse_investment_thesis)
- app/views/cards.py: reusable UI cards
- app/views/agentlab.py: AgentLab page
- app/views/agentops.py: AgentWorkspace page
"""

from app.config import setup_page, get_section, get_client
from app.state import init_session_state
from app.views.agentlab import render_agentlab
from app.views.agentops import render_agentops


def main() -> None:
    # Page config and title
    setup_page()

    # Initialize session state keys
    init_session_state()

    # Sidebar navigation and OpenAI client
    section = get_section()
    client = get_client(timeout=600)

    # Route to selected section
    if section == "AgentWorkspace":
        render_agentops()
    else:
        render_agentlab(client)


if __name__ == "__main__":
    main()
