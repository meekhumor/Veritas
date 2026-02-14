"""Tests for the Impact Assessor agent."""

import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock

from app.agents.impact_assessor import impact_assessor
from app.agents.state import InvestigationState
from app.models.schemas import Category, CrossReferenceResult


@pytest.mark.asyncio
async def test_impact_assessor_scores():
    """Should return impact scores across all 5 dimensions."""
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "topic_sensitivity": {"score": 85, "explanation": "Health/safety topic"},
        "geographic_reach": {"score": 80, "explanation": "Global concern"},
        "emotional_charge": {"score": 70, "explanation": "Fear-inducing"},
        "actionability": {"score": 60, "explanation": "Could affect tech adoption"},
        "vulnerable_populations": {"score": 65, "explanation": "Health-anxious"},
        "overall": 72,
    })

    with patch("app.agents.impact_assessor.get_llm") as mock_llm_factory:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_llm_factory.return_value = mock_llm

        state = InvestigationState(
            query="Does 5G cause cancer?",
            refined_query="Does 5G radiation cause cancer?",
            category=Category.HEALTH,
        )
        result = await impact_assessor(state)

    impact = result["impact"]
    assert impact.overall == 72
    assert impact.topic_sensitivity.score == 85
    assert impact.geographic_reach.score == 80
    assert impact.emotional_charge.score == 70
    assert impact.actionability.score == 60
    assert impact.vulnerable_populations.score == 65
    assert result["current_agent"] == "impact_assessor"


@pytest.mark.asyncio
async def test_impact_assessor_clamping():
    """Scores should be clamped to 0-100 range."""
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "topic_sensitivity": {"score": 150, "explanation": "Way too high"},
        "geographic_reach": {"score": -10, "explanation": "Negative"},
        "emotional_charge": {"score": 50, "explanation": "Normal"},
        "actionability": {"score": 50, "explanation": "Normal"},
        "vulnerable_populations": {"score": 50, "explanation": "Normal"},
        "overall": 200,
    })

    with patch("app.agents.impact_assessor.get_llm") as mock_llm_factory:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_llm_factory.return_value = mock_llm

        state = InvestigationState(query="Test claim")
        result = await impact_assessor(state)

    impact = result["impact"]
    assert impact.overall == 100  # clamped
    assert impact.topic_sensitivity.score == 100  # clamped
    assert impact.geographic_reach.score == 0  # clamped


@pytest.mark.asyncio
async def test_impact_assessor_fallback():
    """Should return defaults on LLM failure."""
    mock_response = MagicMock()
    mock_response.content = "invalid json garbage"

    with patch("app.agents.impact_assessor.get_llm") as mock_llm_factory:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_llm_factory.return_value = mock_llm

        state = InvestigationState(query="Test claim")
        result = await impact_assessor(state)

    impact = result["impact"]
    assert impact.overall == 50  # default
