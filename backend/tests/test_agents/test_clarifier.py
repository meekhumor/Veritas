"""Tests for the Clarifier agent."""

import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock

from app.agents.clarifier import clarifier
from app.agents.state import InvestigationState


@pytest.mark.asyncio
async def test_clarifier_skips_when_not_needed():
    """Should skip if no clarification is needed."""
    state = InvestigationState(
        query="Does 5G cause cancer?",
        needs_clarification=False,
    )
    result = await clarifier(state)

    assert result["current_agent"] == "clarifier"
    assert "no clarification needed" in result["investigation_trail"][0].lower()


@pytest.mark.asyncio
async def test_clarifier_waits_for_answers():
    """Should wait if clarification needed but no answers provided."""
    state = InvestigationState(
        query="Is the vaccine safe?",
        needs_clarification=True,
        clarification_questions=["Which vaccine?"],
        clarification_answers=[],
    )
    result = await clarifier(state)

    assert "awaiting" in result["investigation_trail"][0].lower()


@pytest.mark.asyncio
async def test_clarifier_refines_with_answers():
    """Should refine query using clarification answers."""
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "refined_query": "Is the Pfizer COVID-19 vaccine safe for children under 12?",
        "reasoning": "Refined based on user specifying Pfizer vaccine and concern about children."
    })

    with patch("app.agents.clarifier.get_llm") as mock_llm_factory:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_llm_factory.return_value = mock_llm

        state = InvestigationState(
            query="Is the vaccine safe?",
            refined_query="Is the vaccine safe?",
            needs_clarification=True,
            clarification_questions=["Which vaccine?", "For which age group?"],
            clarification_answers=["Pfizer COVID vaccine", "Children under 12"],
        )
        result = await clarifier(state)

    assert "Pfizer" in result["refined_query"]
    assert result["needs_clarification"] is False
