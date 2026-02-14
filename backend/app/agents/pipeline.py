"""LangGraph investigation pipeline.

Orchestrates the 6-agent pipeline:
  1. Query Analyzer → 2. Clarifier → 3. Evidence Gatherer (4 parallel)
  → 4. Cross-Reference Analyzer → 5. Impact Assessor → 6. Verdict Synthesizer
"""

from __future__ import annotations

import logging
import uuid
from typing import AsyncGenerator

from langgraph.graph import StateGraph, END

from app.agents.state import InvestigationState
from app.agents.query_analyzer import query_analyzer
from app.agents.clarifier import clarifier
from app.agents.evidence_gatherer import (
    web_search,
    news_scanner,
    authority_checker,
    fact_check_lookup,
)
from app.agents.cross_reference import cross_reference_analyzer
from app.agents.impact_assessor import impact_assessor
from app.agents.verdict_synthesizer import verdict_synthesizer
from app.models.schemas import AgentStepEvent, InvestigationReport

logger = logging.getLogger(__name__)


# ── Routing functions ──────────────────────────────────────────────────────

def should_clarify(state: InvestigationState) -> str:
    """Route to clarifier or skip to evidence gathering."""
    if state.needs_clarification and not state.clarification_answers:
        return "clarifier"
    return "evidence_gathering"


# ── Build the graph ───────────────────────────────────────────────────────

def build_investigation_graph() -> StateGraph:
    """Build and compile the LangGraph investigation pipeline."""
    graph = StateGraph(InvestigationState)

    # Add nodes
    graph.add_node("query_analyzer", query_analyzer)
    graph.add_node("clarifier", clarifier)
    graph.add_node("web_search", web_search)
    graph.add_node("news_scanner", news_scanner)
    graph.add_node("authority_checker", authority_checker)
    graph.add_node("fact_check_lookup", fact_check_lookup)
    graph.add_node("cross_reference_analyzer", cross_reference_analyzer)
    graph.add_node("impact_assessor", impact_assessor)
    graph.add_node("verdict_synthesizer", verdict_synthesizer)

    # Set entry point
    graph.set_entry_point("query_analyzer")

    # Query Analyzer → conditional routing
    graph.add_conditional_edges(
        "query_analyzer",
        should_clarify,
        {
            "clarifier": "clarifier",
            "evidence_gathering": "web_search",
        },
    )

    # Clarifier → evidence gathering (all 4 in parallel via fan-out)
    graph.add_edge("clarifier", "web_search")

    # Fan-out: all 4 evidence sub-agents run from the same trigger
    # We use edges from web_search entry point and parallel nodes
    graph.add_edge("web_search", "news_scanner")
    graph.add_edge("news_scanner", "authority_checker")
    graph.add_edge("authority_checker", "fact_check_lookup")

    # After all evidence is gathered → cross-reference
    graph.add_edge("fact_check_lookup", "cross_reference_analyzer")

    # Cross-reference → Impact Assessment → Verdict
    graph.add_edge("cross_reference_analyzer", "impact_assessor")
    graph.add_edge("impact_assessor", "verdict_synthesizer")
    graph.add_edge("verdict_synthesizer", END)

    return graph.compile()


# Pre-compiled graph
investigation_graph = build_investigation_graph()


async def run_investigation(
    query: str,
    user_id: str | None = None,
) -> AsyncGenerator[AgentStepEvent, None]:
    """Run the investigation pipeline, yielding SSE events for each step.

    Yields AgentStepEvent for each agent transition.
    The final event contains the complete investigation report in data.
    """
    investigation_id = str(uuid.uuid4())

    initial_state = InvestigationState(
        query=query,
        user_id=user_id,
        investigation_id=investigation_id,
    )

    logger.info(f"Starting investigation {investigation_id}: '{query}'")

    yield AgentStepEvent(
        agent="pipeline",
        status="started",
        message=f"Investigation started: {query}",
        data={"investigation_id": investigation_id},
    )

    # Track which agents have fired
    seen_agents: set[str] = set()

    try:
        async for event in investigation_graph.astream(initial_state, stream_mode="values"):
            current = event.get("current_agent", "") if isinstance(event, dict) else getattr(event, "current_agent", "")
            if current and current not in seen_agents:
                seen_agents.add(current)

                # Map internal names to user-friendly names
                agent_names = {
                    "query_analyzer": "Query Analyzer",
                    "clarifier": "Clarifier",
                    "web_search": "Web Search",
                    "news_scanner": "News Scanner",
                    "authority_checker": "Authority Checker",
                    "fact_check_lookup": "Fact-Check Lookup",
                    "cross_reference_analyzer": "Cross-Reference Analyzer",
                    "impact_assessor": "Impact Assessor",
                    "verdict_synthesizer": "Verdict Synthesizer",
                }

                friendly_name = agent_names.get(current, current)
                yield AgentStepEvent(
                    agent=current,
                    status="completed",
                    message=f"{friendly_name} completed",
                )

        # Get final state
        final_state = await investigation_graph.ainvoke(initial_state)
        if isinstance(final_state, dict):
            fs = InvestigationState(**final_state)
        else:
            fs = final_state

        # Build report
        report = InvestigationReport(
            id=investigation_id,
            query=fs.query,
            refined_query=fs.refined_query,
            category=fs.category,
            verdict=fs.verdict,
            confidence=fs.confidence,
            summary=fs.summary,
            detailed_analysis=fs.detailed_analysis,
            evidence=fs.evidence,
            cross_reference=fs.cross_reference,
            impact=fs.impact,
            investigation_trail=fs.investigation_trail,
            user_id=fs.user_id,
            is_published=True,
        )

        yield AgentStepEvent(
            agent="pipeline",
            status="completed",
            message="Investigation complete",
            data=report.model_dump(),
        )

    except Exception as e:
        logger.error(f"Investigation {investigation_id} failed: {e}")
        yield AgentStepEvent(
            agent="pipeline",
            status="error",
            message=f"Investigation failed: {str(e)}",
            data={"investigation_id": investigation_id, "error": str(e)},
        )


async def run_investigation_simple(
    query: str,
    user_id: str | None = None,
) -> InvestigationReport:
    """Run the investigation pipeline and return the final report (non-streaming)."""
    investigation_id = str(uuid.uuid4())

    initial_state = InvestigationState(
        query=query,
        user_id=user_id,
        investigation_id=investigation_id,
    )

    result = await investigation_graph.ainvoke(initial_state)
    if isinstance(result, dict):
        fs = InvestigationState(**result)
    else:
        fs = result

    return InvestigationReport(
        id=investigation_id,
        query=fs.query,
        refined_query=fs.refined_query,
        category=fs.category,
        verdict=fs.verdict,
        confidence=fs.confidence,
        summary=fs.summary,
        detailed_analysis=fs.detailed_analysis,
        evidence=fs.evidence,
        cross_reference=fs.cross_reference,
        impact=fs.impact,
        investigation_trail=fs.investigation_trail,
        user_id=fs.user_id,
        is_published=True,
    )
