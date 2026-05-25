"""
Template 1: Competitor Deep Dive

Use case: Deep analysis of a specific company or product in a market.
Example trigger: "Deep dive on Stripe's expansion into LATAM"
"""

TEMPLATE = {
    "id": "competitive_intel",
    "name": "Competitor Deep Dive",
    "description": "In-depth analysis of a specific company, product, or competitor in a target market.",
    "example_prompt": "Analyze Stripe's strategy and competitive positioning in Latin America",
    "graph": {
        "nodes": [
            {"id": "orchestrator", "label": "Orchestrator", "role": "Breaks down the request into search queries"},
            {"id": "researcher", "label": "Researcher", "role": "Runs web searches and collects data"},
            {"id": "analyst", "label": "Analyst", "role": "Synthesizes data into structured intelligence"},
            {"id": "critic", "label": "Critic", "role": "Reviews quality and approves or rejects"},
            {"id": "reporter", "label": "Reporter", "role": "Generates the final report and Telegram summary"},
        ],
        "edges": [
            {"source": "orchestrator", "target": "researcher", "label": ""},
            {"source": "researcher", "target": "analyst", "label": ""},
            {"source": "analyst", "target": "critic", "label": ""},
            {"source": "critic", "target": "researcher", "label": "if rejected"},
            {"source": "critic", "target": "reporter", "label": "if approved"},
            {"source": "reporter", "target": "__end__", "label": ""},
        ],
    },
}
