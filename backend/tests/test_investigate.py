"""Tests for investigation API endpoints."""

import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.schemas import InvestigateRequest


@pytest.mark.asyncio
async def test_investigate_rejects_spam():
    """Spam queries should be rejected with 400."""
    with patch("app.api.investigate.check_spam", new_callable=AsyncMock) as mock_spam:
        mock_spam.return_value = (True, "Detected as spam")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/investigate",
                json={"query": "buy cheap viagra now!!!"},
            )
        assert response.status_code == 400
        assert "rejected" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_investigate_sync_rejects_spam():
    """Sync endpoint also rejects spam."""
    with patch("app.api.investigate.check_spam", new_callable=AsyncMock) as mock_spam:
        mock_spam.return_value = (True, "Detected as spam")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/investigate/sync",
                json={"query": "spam spam spam"},
            )
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_investigate_request_validation():
    """Query must be at least 3 characters."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/investigate", json={"query": "ab"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_investigate_request_model():
    """Test InvestigateRequest model validation."""
    req = InvestigateRequest(query="Is the earth flat?")
    assert req.query == "Is the earth flat?"
    assert req.category is None

    with pytest.raises(Exception):
        InvestigateRequest(query="ab")  # too short
