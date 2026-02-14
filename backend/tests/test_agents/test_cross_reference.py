"""Tests for the Cross-Reference Analyzer agent."""

import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock

from app.agents.cross_reference import cross_reference_analyzer
from app.agents.state import InvestigationState
from app.models.schemas import EvidenceItem, EvidenceType


@pytest.mark.asyncio
async def test_cross_reference_no_evidence():
    """Should handle empty evidence gracefully."""
    state = InvestigationState(
        query="Does 5G cause cancer?",
        evidence=[],
    )
    result = await cross_reference_analyzer(state)

    assert result["cross_reference"] is not None
    assert result["cross_reference"].source_agreement_score == 0.0
    assert "no evidence" in result["investigation_trail"][0].lower()


@pytest.mark.asyncio
async def test_cross_reference_analyzes_evidence(sample_state_with_evidence):
    """Should analyze evidence and find consensus/contradictions."""
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "consensus_points": [
            "No scientific evidence links 5G to cancer",
            "WHO has not found adverse effects",
        ],
        "contradictions": [
            "Some alternative sources claim otherwise",
        ],
        "unique_findings": [
            "RF classification as Group 2B is broader than 5G",
        ],
        "source_agreement_score": 0.85,
        "summary": "Strong consensus that 5G does not cause cancer.",
    })

    with patch("app.agents.cross_reference.get_llm") as mock_llm_factory:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_llm_factory.return_value = mock_llm

        result = await cross_reference_analyzer(sample_state_with_evidence)

    cr = result["cross_reference"]
    assert len(cr.consensus_points) == 2
    assert len(cr.contradictions) == 1
    assert cr.source_agreement_score == 0.85
    assert result["current_agent"] == "cross_reference_analyzer"


@pytest.mark.asyncio
async def test_cross_reference_bad_json_fallback(sample_state_with_evidence):
    """Should handle malformed JSON gracefully."""
    mock_response = MagicMock()
    mock_response.content = "Not valid JSON but some analysis text here."

    with patch("app.agents.cross_reference.get_llm") as mock_llm_factory:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_llm_factory.return_value = mock_llm

        result = await cross_reference_analyzer(sample_state_with_evidence)

    cr = result["cross_reference"]
    assert cr.source_agreement_score == 0.5  # default
    assert cr.summary != ""
