"""Agent 6 — Verdict Synthesizer.

Combines all evidence, cross-reference analysis, and impact assessment
into a final verdict with confidence score.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm import get_llm, rate_limited_invoke
from app.agents.state import InvestigationState
from app.models.schemas import Verdict

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the final verdict synthesizer for Veritas, a misinformation detection system.

You have access to:
- The original claim and refined query
- All gathered evidence from web, news, authorities, and fact-checkers
- Cross-reference analysis showing consensus and contradictions
- Impact assessment scores

Your job is to produce a final verdict.

Respond in JSON:
{
    "verdict": "TRUE|FALSE|UNVERIFIED|PARTIALLY_TRUE|MISLEADING",
    "confidence": 0.0-1.0,
    "summary": "2-3 sentence summary of the verdict for the public",
    "detailed_analysis": "Thorough paragraph explaining the reasoning, citing specific evidence"
}

Verdict guidelines:
- TRUE: Strong evidence from multiple credible sources supporting the claim
- FALSE: Strong evidence from multiple credible sources contradicting the claim
- PARTIALLY_TRUE: The claim has elements of truth but is incomplete or misleading
- MISLEADING: The claim is technically true but presented in a misleading way
- UNVERIFIED: Insufficient evidence to make a determination

Confidence guidelines:
- 0.9-1.0: Multiple authoritative sources agree, fact-checkers confirm
- 0.7-0.9: Good evidence from credible sources, some agreement
- 0.5-0.7: Mixed evidence, some contradictions
- 0.3-0.5: Limited evidence, significant uncertainty
- 0.0-0.3: Very little evidence, mostly speculation

Be objective, fair, and evidence-based. Never let personal bias influence the verdict.
"""


async def verdict_synthesizer(state: InvestigationState) -> dict:
    """Synthesize all evidence into a final verdict."""
    logger.info(f"Verdict Synthesizer: synthesizing for '{state.refined_query or state.query}'")

    llm = get_llm(temperature=0.1)

    # Build comprehensive context
    context = f"CLAIM: {state.refined_query or state.query}\n"
    context += f"CATEGORY: {state.category.value}\n\n"

    # Evidence summary
    context += f"EVIDENCE ({len(state.evidence)} items):\n"
    for i, item in enumerate(state.evidence, 1):
        context += (
            f"\n{i}. [{item.source_type.value}] {item.source_name}\n"
            f"   Title: {item.title}\n"
            f"   Content: {item.content[:300]}\n"
            f"   Credibility: {item.credibility_score}\n"
        )

    # Cross-reference
    if state.cross_reference:
        context += f"\nCROSS-REFERENCE ANALYSIS:\n"
        context += f"Source Agreement Score: {state.cross_reference.source_agreement_score}\n"
        context += f"Summary: {state.cross_reference.summary}\n"
        if state.cross_reference.consensus_points:
            context += f"Consensus: {'; '.join(state.cross_reference.consensus_points)}\n"
        if state.cross_reference.contradictions:
            context += f"Contradictions: {'; '.join(state.cross_reference.contradictions)}\n"

    # Impact
    if state.impact:
        context += f"\nIMPACT ASSESSMENT:\n"
        context += f"Overall Impact Score: {state.impact.overall}/100\n"

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
        verdict_str = parsed.get("verdict", "UNVERIFIED").upper()
        verdict_map = {v.value: v for v in Verdict}
        verdict = verdict_map.get(verdict_str, Verdict.UNVERIFIED)
        confidence = min(1.0, max(0.0, parsed.get("confidence", 0.5)))
        summary = parsed.get("summary", "Unable to determine verdict.")
        detailed_analysis = parsed.get("detailed_analysis", "")
    except json.JSONDecodeError:
        logger.warning("Verdict Synthesizer: failed to parse JSON")
        verdict = Verdict.UNVERIFIED
        confidence = 0.3
        summary = "Investigation completed but verdict synthesis encountered an error."
        detailed_analysis = content[:500]

    trail_entry = (
        f"[{datetime.utcnow().isoformat()}] Verdict Synthesizer: "
        f"{verdict.value} (confidence: {confidence:.0%})"
    )

    return {
        "verdict": verdict,
        "confidence": confidence,
        "summary": summary,
        "detailed_analysis": detailed_analysis,
        "current_agent": "verdict_synthesizer",
        "investigation_trail": [trail_entry],
    }
