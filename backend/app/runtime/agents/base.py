"""
LLM factory — centralizes model initialization so every agent
gets the right model without duplicating config.
"""

from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings


def get_orchestrator_llm() -> ChatGoogleGenerativeAI:
    """Gemini 2.5 Flash — query generation is structured output, not deep reasoning."""
    return ChatGoogleGenerativeAI(
        model=settings.worker_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.3,  # Lower = more deterministic planning
    )


def get_worker_llm() -> ChatGoogleGenerativeAI:
    """Gemini 2.0 Flash — fast and cheap for the worker agents."""
    return ChatGoogleGenerativeAI(
        model=settings.worker_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.7,
    )
