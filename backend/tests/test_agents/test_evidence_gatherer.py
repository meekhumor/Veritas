"""Tests for the Evidence Gatherer sub-agents."""

import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock

from app.agents.evidence_gatherer import (
    web_search,
    news_scanner,
    authority_checker,
    fact_check_lookup,
)
from app.agents.state import InvestigationState
from app.models.schemas import EvidenceType


@pytest.fixture
def evidence_state():
    return InvestigationState(
        query="Does 5G cause cancer?",
        refined_query="Does 5G radiation cause cancer?",
        investigation_id="test-ev-001",
    )


# ── Web Search ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_web_search_no_api_key(evidence_state):
    """Should skip gracefully when no Tavily key is configured."""
    with patch("app.agents.evidence_gatherer.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(tavily_api_key="")
        result = await web_search(evidence_state)

    assert result["web_search_done"] is True
    assert "Skipped" in result["investigation_trail"][0]


@pytest.mark.asyncio
async def test_web_search_with_results(evidence_state):
    """Should parse Tavily results into evidence items."""
    mock_tavily = AsyncMock()
    mock_tavily.search.return_value = {
        "results": [
            {
                "url": "https://example.com/article",
                "title": "5G Health Facts",
                "content": "No evidence linking 5G to cancer",
                "score": 0.8,
            },
        ]
    }

    with patch("app.agents.evidence_gatherer.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(tavily_api_key="test-key")
        with patch("tavily.AsyncTavilyClient", return_value=mock_tavily):
            result = await web_search(evidence_state)

    assert result["web_search_done"] is True
    assert len(result["evidence"]) == 1
    assert result["evidence"][0].source_type == EvidenceType.WEB_SEARCH


# ── News Scanner ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_news_scanner_no_api_key(evidence_state):
    """Should skip gracefully when no Media Cloud key."""
    with patch("app.agents.evidence_gatherer.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(mediacloud_api_key="")
        result = await news_scanner(evidence_state)

    assert result["news_scan_done"] is True
    assert "Skipped" in result["investigation_trail"][0]


# ── Authority Checker ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_authority_checker_no_api_key(evidence_state):
    """Should skip gracefully when no Tavily key."""
    with patch("app.agents.evidence_gatherer.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(tavily_api_key="")
        result = await authority_checker(evidence_state)

    assert result["authority_check_done"] is True
    assert "Skipped" in result["investigation_trail"][0]


@pytest.mark.asyncio
async def test_authority_checker_scores_authority_sites(evidence_state):
    """Authority sites should get higher credibility scores."""
    mock_tavily = AsyncMock()
    mock_tavily.search.return_value = {
        "results": [
            {
                "url": "https://www.who.int/5g",
                "title": "WHO on 5G",
                "content": "No adverse effects found",
                "score": 0.9,
            },
            {
                "url": "https://random-blog.com/5g",
                "title": "My 5G opinion",
                "content": "I think 5G is bad",
                "score": 0.3,
            },
        ]
    }

    with patch("app.agents.evidence_gatherer.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(tavily_api_key="test-key")
        with patch("tavily.AsyncTavilyClient", return_value=mock_tavily):
            result = await authority_checker(evidence_state)

    assert result["authority_check_done"] is True
    evidence = result["evidence"]
    assert len(evidence) == 2

    # WHO should have higher credibility
    who_item = [e for e in evidence if "who.int" in (e.source_url or "")][0]
    blog_item = [e for e in evidence if "random-blog" in (e.source_url or "")][0]
    assert who_item.credibility_score > blog_item.credibility_score


# ── Fact-Check Lookup ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fact_check_no_api_key(evidence_state):
    """Should skip gracefully when no Google key."""
    with patch("app.agents.evidence_gatherer.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(google_factcheck_api_key="")
        result = await fact_check_lookup(evidence_state)

    assert result["fact_check_done"] is True
    assert "Skipped" in result["investigation_trail"][0]


@pytest.mark.asyncio
async def test_fact_check_with_results(evidence_state):
    """Should parse Google Fact Check API results."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "claims": [
            {
                "text": "5G causes cancer",
                "claimReview": [
                    {
                        "publisher": {"name": "Snopes"},
                        "url": "https://snopes.com/5g",
                        "title": "5G Cancer Claim",
                        "textualRating": "False",
                        "reviewDate": "2024-01-01",
                    }
                ],
            }
        ]
    }

    with patch("app.agents.evidence_gatherer.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(google_factcheck_api_key="test-key")
        with patch("app.agents.evidence_gatherer.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = await fact_check_lookup(evidence_state)

    assert result["fact_check_done"] is True
    assert len(result["evidence"]) == 1
    assert result["evidence"][0].source_type == EvidenceType.FACT_CHECK
    assert "Snopes" in result["evidence"][0].source_name
