"""Tests for the spam filter service."""

import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.spam_filter import check_spam


@pytest.mark.asyncio
async def test_spam_filter_rejects_short_query():
    """Should reject queries shorter than 3 characters."""
    is_spam, reason = await check_spam("ab")
    assert is_spam is True
    assert "short" in reason.lower()


@pytest.mark.asyncio
async def test_spam_filter_rejects_empty_query():
    """Should reject empty queries."""
    is_spam, reason = await check_spam("")
    assert is_spam is True


@pytest.mark.asyncio
async def test_spam_filter_rejects_long_query():
    """Should reject queries over 1000 characters."""
    long_query = "x" * 1001
    is_spam, reason = await check_spam(long_query)
    assert is_spam is True
    assert "long" in reason.lower()


@pytest.mark.asyncio
async def test_spam_filter_allows_genuine_query():
    """Should allow genuine investigation queries."""
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "is_spam": False,
        "reason": "Genuine claim about health misinformation",
        "category": "genuine",
    })

    with patch("app.services.spam_filter.get_llm") as mock_llm_factory:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_llm_factory.return_value = mock_llm

        is_spam, reason = await check_spam("Does drinking bleach cure COVID-19?")

    assert is_spam is False


@pytest.mark.asyncio
async def test_spam_filter_rejects_spam():
    """Should reject spam queries."""
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "is_spam": True,
        "reason": "This is advertising/spam content",
        "category": "spam",
    })

    with patch("app.services.spam_filter.get_llm") as mock_llm_factory:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_llm_factory.return_value = mock_llm

        is_spam, reason = await check_spam("BUY CHEAP PILLS NOW CLICK HERE!!!")

    assert is_spam is True


@pytest.mark.asyncio
async def test_spam_filter_fails_open():
    """Should allow queries when the LLM check fails (fail open)."""
    with patch("app.services.spam_filter.get_llm") as mock_llm_factory:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = Exception("LLM unavailable")
        mock_llm_factory.return_value = mock_llm

        is_spam, reason = await check_spam("Is the earth flat?")

    assert is_spam is False  # Fail open
