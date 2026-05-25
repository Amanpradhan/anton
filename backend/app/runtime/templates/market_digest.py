"""
Template 2: Market Trend Weekly Digest

Use case: Broad scan of a market or industry for recent trends and developments.
Example trigger: "What's happening in the LATAM fintech space this week?"
"""

TEMPLATE = {
    "id": "market_digest",
    "name": "Market Trend Weekly Digest",
    "description": "Broad market scan for recent trends, news, funding, and emerging players in a sector.",
    "example_prompt": "Give me a weekly digest of the LATAM fintech market",
    "graph": {
        "nodes": [
            {"id": "orchestrator", "label": "Orchestrator", "role": "Plans broad market scan queries"},
            {"id": "researcher", "label": "Researcher", "role": "Scans news, funding data, and trends"},
            {"id": "analyst", "label": "Analyst", "role": "Identifies key themes and developments"},
            {"id": "critic", "label": "Critic", "role": "Ensures breadth and recency of coverage"},
            {"id": "reporter", "label": "Reporter", "role": "Formats as a weekly digest report"},
        ],
        "edges": [
            {"source": "orchestrator", "target": "researcher", "label": ""},
            {"source": "researcher", "target": "analyst", "label": ""},
            {"source": "analyst", "target": "critic", "label": ""},
            {"source": "critic", "target": "researcher", "label": "if gaps found"},
            {"source": "critic", "target": "reporter", "label": "if approved"},
            {"source": "reporter", "target": "__end__", "label": ""},
        ],
    },
}
