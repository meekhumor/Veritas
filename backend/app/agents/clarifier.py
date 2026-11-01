"""Agent 2 — Clarifier.

Asks 1-2 smart follow-up questions if the query is vague/ambiguous.
Skips if the query is clear enough (as determined by Query Analyzer).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm import get_llm, rate_limited_invoke, extract_text
from app.agents.state import InvestigationState

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a clarification specialist for a misinformation detection system.

The user submitted a vague or ambiguous claim. The Query Analyzer has flagged it for clarification
and suggested some questions. Your job is to refine the query using the user's answers.

Given:
- Original query
- Clarification questions that were asked
- User's answers

Produce a refined, specific, investigable claim statement.

Respond in JSON:
{
    "refined_query": "The refined, specific claim to investigate",
    "reasoning": "Brief explanation of how you refined the query"
}
"""


async def clarifier(state: InvestigationState) -> dict:
    """Refine the query using clarification answers, or pass through if clear."""
    # Skip if no clarification needed
    if not state.needs_clarification:
        logger.info("Clarifier: query is clear, skipping")
        return {
            "current_agent": "clarifier",
            "investigation_trail": [
                f"[{datetime.utcnow().isoformat()}] Clarifier: Query is clear, no clarification needed"
            ],
        }

    # If clarification was needed but no answers provided yet, just pass through
    if not state.clarification_answers:
        logger.info("Clarifier: awaiting clarification answers")
        return {
            "current_agent": "clarifier",
            "investigation_trail": [
                f"[{datetime.utcnow().isoformat()}] Clarifier: Awaiting user clarification"
            ],
        }

    llm = get_llm(temperature=0.1)

    qa_pairs = ""
    for i, (q, a) in enumerate(zip(state.clarification_questions, state.clarification_answers)):
        qa_pairs += f"\nQ{i+1}: {q}\nA{i+1}: {a}"

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"Original query: {state.query}\n\nClarification Q&A:{qa_pairs}"
        ),
    ]

    response = await rate_limited_invoke(llm, messages)
    content = extract_text(response.content).strip()

    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = {"refined_query": state.refined_query, "reasoning": "Used existing refined query"}

    trail_entry = f"[{datetime.utcnow().isoformat()}] Clarifier: {parsed.get('reasoning', 'Refined query')}"

    return {
        "refined_query": parsed.get("refined_query", state.refined_query),
        "needs_clarification": False,
        "current_agent": "clarifier",
        "investigation_trail": [trail_entry],
    }
