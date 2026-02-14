"""Agent 5 — Impact Assessor.

Scores societal risk across 5 dimensions:
  - Topic Sensitivity
  - Geographic Reach
  - Emotional Charge
  - Actionability
  - Vulnerable Populations
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm import get_llm, rate_limited_invoke
from app.agents.state import InvestigationState
from app.models.schemas import ImpactScore, ImpactDimension

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a societal impact assessment specialist for a misinformation detection system.

Given a claim and the evidence gathered about it, assess the potential societal impact across 5 dimensions.
Score each dimension from 0 to 100.

Dimensions:
1. **Topic Sensitivity** — How sensitive is the topic? (health/safety = high, trivia = low)
2. **Geographic Reach** — How widespread could this misinformation spread? (global = high, local = low)
3. **Emotional Charge** — How emotionally provocative is the claim? (fear/outrage = high, neutral = low)
4. **Actionability** — Could people take harmful action based on this? (medical advice = high, opinion = low)
5. **Vulnerable Populations** — Does this target vulnerable groups? (children/elderly/sick = high)

Respond in JSON:
{
    "topic_sensitivity": {"score": 0-100, "explanation": "brief reason"},
    "geographic_reach": {"score": 0-100, "explanation": "brief reason"},
    "emotional_charge": {"score": 0-100, "explanation": "brief reason"},
    "actionability": {"score": 0-100, "explanation": "brief reason"},
    "vulnerable_populations": {"score": 0-100, "explanation": "brief reason"},
    "overall": 0-100
}

The overall score should be a weighted average emphasizing actionability and vulnerable populations.
"""


async def impact_assessor(state: InvestigationState) -> dict:
    """Assess societal impact of the claim."""
    logger.info(f"Impact Assessor: assessing '{state.refined_query or state.query}'")

    llm = get_llm(temperature=0.2)

    # Build context from evidence and cross-reference
    context = f"Claim: {state.refined_query or state.query}\nCategory: {state.category.value}\n"
    if state.cross_reference:
        context += f"\nCross-reference summary: {state.cross_reference.summary}\n"
    context += f"\nNumber of evidence items: {len(state.evidence)}\n"

    # Include brief evidence summary
    for i, item in enumerate(state.evidence[:5], 1):
        context += f"\nEvidence {i} ({item.source_type.value}): {item.title} — {item.content[:200]}\n"

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=context),
    ]

    response = await rate_limited_invoke(llm, messages)
    content = response.content.strip()

    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    try:
        parsed = json.loads(content)

        def _parse_dim(key: str) -> ImpactDimension:
            dim = parsed.get(key, {})
            return ImpactDimension(
                score=min(100, max(0, dim.get("score", 50))),
                explanation=dim.get("explanation", "No explanation provided"),
            )

        impact = ImpactScore(
            overall=min(100, max(0, parsed.get("overall", 50))),
            topic_sensitivity=_parse_dim("topic_sensitivity"),
            geographic_reach=_parse_dim("geographic_reach"),
            emotional_charge=_parse_dim("emotional_charge"),
            actionability=_parse_dim("actionability"),
            vulnerable_populations=_parse_dim("vulnerable_populations"),
        )
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Impact Assessor: failed to parse response — {e}")
        default_dim = ImpactDimension(score=50, explanation="Could not assess")
        impact = ImpactScore(
            overall=50,
            topic_sensitivity=default_dim,
            geographic_reach=default_dim,
            emotional_charge=default_dim,
            actionability=default_dim,
            vulnerable_populations=default_dim,
        )

    trail_entry = f"[{datetime.utcnow().isoformat()}] Impact Assessor: Overall impact score = {impact.overall}"

    return {
        "impact": impact,
        "current_agent": "impact_assessor",
        "investigation_trail": [trail_entry],
    }
