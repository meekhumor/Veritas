"""Agent 4 — Cross-Reference Analyzer.

Finds consensus and contradictions across all gathered evidence.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm import get_llm, rate_limited_invoke
from app.agents.state import InvestigationState
from app.models.schemas import CrossReferenceResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a cross-reference analysis specialist for a misinformation detection system.

You will receive evidence gathered from multiple sources (web search, news, authoritative sources, fact-checkers).
Your job is to:
1. Identify points where sources agree (consensus).
2. Identify contradictions between sources.
3. Note unique findings that only appear in one source.
4. Calculate a source agreement score (0.0 to 1.0).

Respond in JSON:
{
    "consensus_points": ["point1", "point2", ...],
    "contradictions": ["contradiction1", "contradiction2", ...],
    "unique_findings": ["finding1", "finding2", ...],
    "source_agreement_score": 0.0-1.0,
    "summary": "Brief paragraph summarizing the cross-reference analysis"
}

Be thorough but concise. Focus on factual claims, not opinions.
"""


async def cross_reference_analyzer(state: InvestigationState) -> dict:
    """Analyze evidence for consensus and contradictions."""
    logger.info(f"Cross-Reference Analyzer: analyzing {len(state.evidence)} evidence items")

    if not state.evidence:
        logger.warning("Cross-Reference Analyzer: no evidence to analyze")
        return {
            "cross_reference": CrossReferenceResult(
                summary="No evidence available for cross-reference analysis.",
                source_agreement_score=0.0,
            ),
            "current_agent": "cross_reference_analyzer",
            "investigation_trail": [
                f"[{datetime.utcnow().isoformat()}] Cross-Reference Analyzer: No evidence to analyze"
            ],
        }

    llm = get_llm(temperature=0.1)

    # Format evidence for LLM
    evidence_text = ""
    for i, item in enumerate(state.evidence, 1):
        evidence_text += (
            f"\n--- Source {i} ({item.source_type.value}) ---\n"
            f"Name: {item.source_name}\n"
            f"Title: {item.title}\n"
            f"Content: {item.content[:500]}\n"
            f"Credibility: {item.credibility_score}\n"
        )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"Claim being investigated: {state.refined_query or state.query}\n\nEvidence:{evidence_text}"
        ),
    ]

    response = await rate_limited_invoke(llm, messages)
    content = response.content.strip()

    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    try:
        parsed = json.loads(content)
        cross_ref = CrossReferenceResult(
            consensus_points=parsed.get("consensus_points", []),
            contradictions=parsed.get("contradictions", []),
            unique_findings=parsed.get("unique_findings", []),
            source_agreement_score=min(1.0, max(0.0, parsed.get("source_agreement_score", 0.5))),
            summary=parsed.get("summary", ""),
        )
    except json.JSONDecodeError:
        logger.warning("Cross-Reference Analyzer: failed to parse JSON response")
        cross_ref = CrossReferenceResult(
            summary=content[:500],
            source_agreement_score=0.5,
        )

    trail_entry = (
        f"[{datetime.utcnow().isoformat()}] Cross-Reference Analyzer: "
        f"Found {len(cross_ref.consensus_points)} consensus points, "
        f"{len(cross_ref.contradictions)} contradictions, "
        f"agreement score: {cross_ref.source_agreement_score:.2f}"
    )

    return {
        "cross_reference": cross_ref,
        "current_agent": "cross_reference_analyzer",
        "investigation_trail": [trail_entry],
    }
