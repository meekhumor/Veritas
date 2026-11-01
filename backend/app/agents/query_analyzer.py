"""Agent 1 — Query Analyzer.

Parses the user's query, identifies the category, refines the claim,
and decides if clarification is needed before investigation.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm import get_llm, rate_limited_invoke, extract_text
from app.agents.state import InvestigationState
from app.models.schemas import Category

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a query analysis specialist for a misinformation detection system called Veritas.

Given a user's query about a claim, you must:
1. Determine if the query is clear enough to investigate, or if clarification is needed.
2. Refine the query into a precise, investigable claim statement.
3. Classify the claim into one of these categories: Health, Finance, Politics, Tech, General.

Respond in JSON format:
{
    "refined_query": "A clear, precise version of the claim to investigate",
    "category": "Health|Finance|Politics|Tech|General",
    "needs_clarification": true/false,
    "clarification_questions": ["question1", "question2"] (only if needs_clarification is true, max 2 questions),
    "reasoning": "Brief explanation of your analysis"
}

Rules:
- If the claim is already clear and specific, set needs_clarification to false.
- Only request clarification if the claim is genuinely ambiguous or too vague to investigate meaningfully.
- The refined query should be a neutral, factual statement that can be verified.
- Be concise in your reasoning.
"""


async def query_analyzer(state: InvestigationState) -> dict:
    """Analyze and refine the user's query."""
    logger.info(f"Query Analyzer: processing '{state.query}'")

    llm = get_llm(temperature=0.1)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Analyze this claim/query: {state.query}"),
    ]

    response = await rate_limited_invoke(llm, messages)
    content = extract_text(response.content).strip()

    # Parse JSON from response (handle markdown code blocks)
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        logger.warning(f"Query Analyzer: failed to parse JSON, using raw query")
        parsed = {
            "refined_query": state.query,
            "category": "General",
            "needs_clarification": False,
            "clarification_questions": [],
            "reasoning": "Failed to parse LLM response, proceeding with original query.",
        }

    category_map = {c.value.lower(): c for c in Category}
    raw_category = parsed.get("category", "General").lower()
    category = category_map.get(raw_category, Category.GENERAL)

    trail_entry = f"[{datetime.utcnow().isoformat()}] Query Analyzer: {parsed.get('reasoning', 'Analyzed query')}"

    return {
        "refined_query": parsed.get("refined_query", state.query),
        "category": category,
        "needs_clarification": parsed.get("needs_clarification", False),
        "clarification_questions": parsed.get("clarification_questions", []),
        "current_agent": "query_analyzer",
        "investigation_trail": [trail_entry],
    }
