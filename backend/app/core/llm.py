"""LLM initialization and helpers with rate-limit-aware throttling."""

import asyncio
import time
import logging

from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# ── Simple token-bucket rate limiter ───────────────────────────────────────

class _RateLimiter:
    """Async rate limiter that enforces a minimum delay between LLM calls.

    With gemma-3-27b-it at 15k tokens/min and ~2k tokens per call,
    we can safely do ~7 calls/min → ~8.5s between calls.
    Use 10s to leave headroom.
    """

    def __init__(self, min_interval: float = 10.0):
        self.min_interval = min_interval
        self._last_call: float = 0.0
        self._lock = asyncio.Lock()

    async def wait(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call
            if elapsed < self.min_interval:
                delay = self.min_interval - elapsed
                logger.info(f"Rate limiter: waiting {delay:.1f}s before next LLM call")
                await asyncio.sleep(delay)
            self._last_call = time.monotonic()


_rate_limiter = _RateLimiter(min_interval=10.0)


def get_llm(temperature: float = 0.1, model: str | None = None) -> ChatGoogleGenerativeAI:
    """Return a configured Gemini/Gemma LLM instance."""
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=model or settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=temperature,
        convert_system_message_to_human=True,
    )


def extract_text(content) -> str:
    """Extract plain text string from LLM response.content which can be a str or list of parts."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for part in content:
            if isinstance(part, str):
                texts.append(part)
            elif isinstance(part, dict) and "text" in part:
                texts.append(part["text"])
            elif hasattr(part, "text"):
                texts.append(getattr(part, "text"))
            else:
                texts.append(str(part))
        return "".join(texts)
    return str(content)


async def rate_limited_invoke(llm: ChatGoogleGenerativeAI, messages, **kwargs):
    """Invoke the LLM with rate limiting to stay within token quotas."""
    await _rate_limiter.wait()
    return await llm.ainvoke(messages, **kwargs)
