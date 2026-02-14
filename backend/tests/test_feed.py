"""Tests for feed API endpoints."""

import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_feed_empty():
    """Feed should return empty list when no investigations exist."""
    with patch("app.api.feed.get_feed", new_callable=AsyncMock) as mock_feed:
        mock_feed.return_value = {"items": [], "total": 0, "page": 1, "limit": 20}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/feed")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0


@pytest.mark.asyncio
async def test_feed_with_category_filter():
    """Feed should accept category filter parameter."""
    with patch("app.api.feed.get_feed", new_callable=AsyncMock) as mock_feed:
        mock_feed.return_value = {"items": [], "total": 0, "page": 1, "limit": 20}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/feed?category=Health")

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_feed_sorting():
    """Feed should accept sort parameter."""
    with patch("app.api.feed.get_feed", new_callable=AsyncMock) as mock_feed:
        mock_feed.return_value = {"items": [], "total": 0, "page": 1, "limit": 20}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for sort in ["recent", "impact", "trending"]:
                response = await client.get(f"/feed?sort={sort}")
                assert response.status_code == 200


@pytest.mark.asyncio
async def test_feed_pagination():
    """Feed should accept page and limit parameters."""
    with patch("app.api.feed.get_feed", new_callable=AsyncMock) as mock_feed:
        mock_feed.return_value = {"items": [], "total": 0, "page": 2, "limit": 10}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/feed?page=2&limit=10")

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_trending_empty():
    """Trending should return empty when no data."""
    with patch("app.api.feed.get_trending_claims", new_callable=AsyncMock) as mock_trending:
        mock_trending.return_value = []

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/feed/trending")

        assert response.status_code == 200
        assert "clusters" in response.json()


@pytest.mark.asyncio
async def test_get_investigation_not_found():
    """Should return 404 for non-existent investigation."""
    with patch("app.api.feed.get_investigation", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/feed/nonexistent-id")

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_investigation_found():
    """Should return investigation data when found."""
    mock_data = {"id": "test-id", "query": "test", "verdict": "TRUE"}

    with patch("app.api.feed.get_investigation", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_data

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/feed/test-id")

        assert response.status_code == 200
        assert response.json()["id"] == "test-id"


@pytest.mark.asyncio
async def test_vote():
    """Should record a vote."""
    with patch("app.api.feed.add_vote", new_callable=AsyncMock) as mock_vote:
        mock_vote.return_value = {"status": "ok", "vote_type": "upvote"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/feed/test-id/vote",
                json={"vote_type": "upvote", "user_id": "user-123"},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
