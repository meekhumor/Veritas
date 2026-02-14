"""Tests for the Query Analyzer agent."""

import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock

from app.agents.query_analyzer import query_analyzer
from app.agents.state import InvestigationState
from app.models.schemas import Category


@pytest.mark.asyncio
async def test_query_analyzer_clear_query():
    """Should analyze a clear query without requesting clarification."""
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "refined_query": "Does 5G radiation cause cancer in humans?",
        "category": "Health",
        "needs_clarification": False,
        "clarification_questions": [],
        "reasoning": "Query is specific and investigable."
    })

    with patch("app.agents.query_analyzer.get_llm") as mock_llm_factory:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_llm_factory.return_value = mock_llm

        state = InvestigationState(query="Does 5G cause cancer?")
        result = await query_analyzer(state)

    assert result["refined_query"] == "Does 5G radiation cause cancer in humans?"
    assert result["category"] == Category.HEALTH
    assert result["needs_clarification"] is False
    assert result["current_agent"] == "query_analyzer"
    assert len(result["investigation_trail"]) == 1


@pytest.mark.asyncio
async def test_query_analyzer_vague_query():
    """Should request clarification for vague queries."""
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "refined_query": "Is the vaccine safe?",
        "category": "Health",
        "needs_clarification": True,
        "clarification_questions": [
            "Which vaccine are you asking about?",
            "Are you concerned about a specific side effect?"
        ],
        "reasoning": "Query is too vague — 'vaccine' could refer to many vaccines."
    })

    with patch("app.agents.query_analyzer.get_llm") as mock_llm_factory:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_llm_factory.return_value = mock_llm

        state = InvestigationState(query="Is the vaccine safe?")
        result = await query_analyzer(state)

    assert result["needs_clarification"] is True
    assert len(result["clarification_questions"]) == 2


@pytest.mark.asyncio
async def test_query_analyzer_bad_json_fallback():
    """Should handle malformed LLM responses gracefully."""
    mock_response = MagicMock()
    mock_response.content = "This is not valid JSON at all"

    with patch("app.agents.query_analyzer.get_llm") as mock_llm_factory:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_llm_factory.return_value = mock_llm

        state = InvestigationState(query="Does 5G cause cancer?")
        result = await query_analyzer(state)

    # Should fall back to original query
    assert result["refined_query"] == "Does 5G cause cancer?"
    assert result["category"] == Category.GENERAL
    assert result["needs_clarification"] is False


@pytest.mark.asyncio
async def test_query_analyzer_json_in_code_block():
    """Should extract JSON from markdown code blocks."""
    mock_response = MagicMock()
    mock_response.content = """Here's my analysis:

```json
{
    "refined_query": "Bitcoin price prediction claim",
    "category": "Finance",
    "needs_clarification": false,
    "clarification_questions": [],
    "reasoning": "Clear financial claim"
}
```
"""

    with patch("app.agents.query_analyzer.get_llm") as mock_llm_factory:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_llm_factory.return_value = mock_llm

        state = InvestigationState(query="Will Bitcoin hit 100k?")
        result = await query_analyzer(state)

    assert result["category"] == Category.FINANCE
    assert result["needs_clarification"] is False
