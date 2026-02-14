"""Spam filter — LLM-based check before publishing to feed."""

from __future__ import annotations

import json
import logging

from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm import get_llm, rate_limited_invoke

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a spam and abuse filter for Veritas, a misinformation detection system.

Users submit claims/queries to investigate. Your job is to determine if a query is:
1. Genuine — a real claim or question about possible misinformation
2. Spam — nonsensical, advertising, self-promotion, or gibberish
3. Abusive — hate speech, threats, harassment, or deliberately harmful content
4. Off-topic — clearly not about a factual claim (e.g., "write me a poem")

Respond in JSON:
{
    "is_spam": true/false,
    "reason": "brief explanation",
    "category": "genuine|spam|abusive|off_topic"
}

Be lenient — if in doubt, allow it. Only reject clear spam or abuse.
"""


async def check_spam(query: str) -> tuple[bool, str]:
    """Check if a query is spam/abuse. Returns (is_spam, reason)."""
    if not query or len(query.strip()) < 3:
        return True, "Query too short"

    # Quick heuristic checks
    if len(query) > 1000:
        return True, "Query too long"

    # LLM-based check
    try:
        llm = get_llm(temperature=0.0)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Check this query: {query}"),
        ]
        response = await rate_limited_invoke(llm, messages)
        content = response.content.strip()

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        parsed = json.loads(content)
        is_spam = parsed.get("is_spam", False)
        reason = parsed.get("reason", "")

        if is_spam:
            logger.info(f"Spam filter rejected: '{query[:50]}...' — {reason}")

        return is_spam, reason

    except Exception as e:
        # On error, allow the query through (fail open)
        logger.warning(f"Spam filter error: {e}")
        return False, ""
