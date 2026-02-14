"""LLM initialization and helpers."""

from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import get_settings


def get_llm(temperature: float = 0.1, model: str | None = None) -> ChatGoogleGenerativeAI:
    """Return a configured Gemini LLM instance."""
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=model or settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=temperature,
        convert_system_message_to_human=True,
    )
