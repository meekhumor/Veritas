"""LangGraph shared state for the investigation pipeline."""

from __future__ import annotations

from typing import Annotated, Optional
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages

from app.models.schemas import (
    Category,
    EvidenceItem,
    CrossReferenceResult,
    ImpactScore,
    Verdict,
)


def merge_evidence(existing: list[EvidenceItem], new: list[EvidenceItem]) -> list[EvidenceItem]:
    """Merge evidence lists, deduplicating by id."""
    seen = {e.id for e in existing}
    merged = list(existing)
    for item in new:
        if item.id not in seen:
            merged.append(item)
            seen.add(item.id)
    return merged


def merge_trail(existing: list[str], new: list[str]) -> list[str]:
    """Append new trail entries."""
    return existing + new


class InvestigationState(BaseModel):
    """Shared state passed through the LangGraph investigation pipeline."""

    # Input
    query: str = ""
    user_id: Optional[str] = None

    # Query Analyzer output
    refined_query: str = ""
    category: Category = Category.GENERAL
    needs_clarification: bool = False
    clarification_questions: list[str] = Field(default_factory=list)
    clarification_answers: list[str] = Field(default_factory=list)

    # Evidence (accumulated from 4 parallel sub-agents)
    evidence: Annotated[list[EvidenceItem], merge_evidence] = Field(default_factory=list)
    web_search_done: bool = False
    news_scan_done: bool = False
    authority_check_done: bool = False
    fact_check_done: bool = False

    # Cross-Reference output
    cross_reference: Optional[CrossReferenceResult] = None

    # Impact Assessment output
    impact: Optional[ImpactScore] = None

    # Verdict output
    verdict: Verdict = Verdict.UNVERIFIED
    confidence: float = 0.0
    summary: str = ""
    detailed_analysis: str = ""

    # Pipeline tracking
    investigation_id: str = ""
    investigation_trail: Annotated[list[str], merge_trail] = Field(default_factory=list)
    current_agent: str = ""
    error: Optional[str] = None
