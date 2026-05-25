"""
Tavily web search tool — built specifically for LLM agents.
Returns clean, structured results without HTML noise.
"""

import os

from langchain_community.tools.tavily_search import TavilySearchResults

from app.config import settings

# Tavily reads from env var, so we set it explicitly from our settings
os.environ["TAVILY_API_KEY"] = settings.tavily_api_key

web_search = TavilySearchResults(
    max_results=5,
    search_depth="advanced",
    include_answer=True,
    include_raw_content=False,
    include_images=False,
)
