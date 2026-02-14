"""Tests for the Verdict Synthesizer agent."""

import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock

from app.agents.verdict_synthesizer import verdict_synthesizer
from app.agents.state import InvestigationState
from app.models.schemas import (
    Verdict,
    Category,
    CrossReferenceResult,
    ImpactScore,
    ImpactDimension,
    EvidenceItem,
    EvidenceType,
)


@pytest.mark.asyncio
async def test_verdict_true():
    """Should return TRUE verdict with high confidence for strong evidence."""
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "verdict": "FALSE",
        "confidence": 0.92,
        "summary": "The claim that 5G causes cancer is false based on scientific consensus.",
        "detailed_analysis": "Multiple authoritative sources including WHO confirm no link.",
    })

    with patch("app.agents.verdict_synthesizer.get_llm") as mock_llm_factory:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_llm_factory.return_value = mock_llm

        state = InvestigationState(
            query="Does 5G cause cancer?",
            refined_query="Does 5G radiation cause cancer?",
            category=Category.HEALTH,
            evidence=[
                EvidenceItem(
                    source_type=EvidenceType.AUTHORITY,
                    source_name="who.int",
                    title="WHO on 5G",
                    content="No adverse effects found",
                    credibility_score=0.95,
                ),
            ],
            cross_reference=CrossReferenceResult(
                consensus_points=["No link found"],
                source_agreement_score=0.9,
                summary="Strong consensus",
            ),
            impact=ImpactScore(
                overall=72,
                topic_sensitivity=ImpactDimension(score=85, explanation="Health"),
                geographic_reach=ImpactDimension(score=80, explanation="Global"),
                emotional_charge=ImpactDimension(score=70, explanation="Fear"),
                actionability=ImpactDimension(score=60, explanation="Tech"),
                vulnerable_populations=ImpactDimension(score=65, explanation="Elderly"),
            ),
        )
        result = await verdict_synthesizer(state)

    assert result["verdict"] == Verdict.FALSE
    assert result["confidence"] == 0.92
    assert "false" in result["summary"].lower()
    assert result["current_agent"] == "verdict_synthesizer"


@pytest.mark.asyncio
async def test_verdict_unverified():
    """Should return UNVERIFIED when evidence is insufficient."""
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "verdict": "UNVERIFIED",
        "confidence": 0.3,
        "summary": "Insufficient evidence to verify this claim.",
        "detailed_analysis": "Limited data available.",
    })

    with patch("app.agents.verdict_synthesizer.get_llm") as mock_llm_factory:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_llm_factory.return_value = mock_llm

        state = InvestigationState(query="Some obscure claim", evidence=[])
        result = await verdict_synthesizer(state)

    assert result["verdict"] == Verdict.UNVERIFIED
    assert result["confidence"] == 0.3


@pytest.mark.asyncio
async def test_verdict_confidence_clamping():
    """Confidence should be clamped to 0.0-1.0."""
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "verdict": "TRUE",
        "confidence": 1.5,
        "summary": "Definitely true.",
        "detailed_analysis": "Very sure.",
    })

    with patch("app.agents.verdict_synthesizer.get_llm") as mock_llm_factory:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_llm_factory.return_value = mock_llm

        state = InvestigationState(query="Test")
        result = await verdict_synthesizer(state)

    assert result["confidence"] == 1.0


@pytest.mark.asyncio
async def test_verdict_bad_json_fallback():
    """Should return UNVERIFIED on parse failure."""
    mock_response = MagicMock()
    mock_response.content = "Not JSON at all"

    with patch("app.agents.verdict_synthesizer.get_llm") as mock_llm_factory:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_llm_factory.return_value = mock_llm

        state = InvestigationState(query="Test")
        result = await verdict_synthesizer(state)

    assert result["verdict"] == Verdict.UNVERIFIED
    assert result["confidence"] == 0.3


@pytest.mark.asyncio
async def test_verdict_all_verdicts_valid():
    """All verdict enum values should be handled."""
    for v in Verdict:
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "verdict": v.value,
            "confidence": 0.5,
            "summary": f"Verdict is {v.value}",
            "detailed_analysis": "Analysis.",
        })

        with patch("app.agents.verdict_synthesizer.get_llm") as mock_llm_factory:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = mock_response
            mock_llm_factory.return_value = mock_llm

            state = InvestigationState(query="Test")
            result = await verdict_synthesizer(state)

        assert result["verdict"] == v
