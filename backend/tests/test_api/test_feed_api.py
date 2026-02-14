"""Comprehensive tests for the feed API endpoints.

Covers:
  - GET  /feed                        (paginated feed)
  - GET  /feed/trending               (trending claims)
  - GET  /feed/{investigation_id}     (single report)
  - POST /feed/{investigation_id}/vote (vote on report)
"""

import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app


# ── Helpers ─────────────────────────────────────────────────────────────────

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


MOCK_INVESTIGATION = {
    "id": "inv-001",
    "query": "Does 5G cause cancer?",
    "refined_query": "Does 5G radiation cause cancer in humans?",
    "category": "Health",
    "verdict": "FALSE",
    "confidence": 0.92,
    "summary": "No scientific evidence links 5G to cancer.",
    "detailed_analysis": "Multiple studies...",
    "evidence": [],
    "cross_reference": None,
    "impact": {"overall": 72},
    "investigation_trail": ["query_analyzer", "evidence_gatherer"],
    "created_at": "2026-02-14T08:00:00",
    "user_id": None,
    "is_published": True,
    "upvotes": 12,
    "flags": 0,
}

MOCK_FEED_RESULT = {
    "items": [MOCK_INVESTIGATION],
    "total": 1,
    "page": 1,
    "limit": 20,
}


# ── GET /feed ───────────────────────────────────────────────────────────────

class TestListFeed:
    """Tests for GET /feed."""

    @pytest.mark.asyncio
    async def test_feed_returns_200(self, client):
        with patch("app.api.feed.get_feed", new_callable=AsyncMock) as m:
            m.return_value = {"items": [], "total": 0, "page": 1, "limit": 20}
            response = await client.get("/feed")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_feed_empty(self, client):
        with patch("app.api.feed.get_feed", new_callable=AsyncMock) as m:
            m.return_value = {"items": [], "total": 0, "page": 1, "limit": 20}
            data = (await client.get("/feed")).json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_feed_with_items(self, client):
        with patch("app.api.feed.get_feed", new_callable=AsyncMock) as m:
            m.return_value = MOCK_FEED_RESULT
            data = (await client.get("/feed")).json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == "inv-001"

    @pytest.mark.asyncio
    async def test_feed_default_pagination(self, client):
        """Defaults: page=1, limit=20."""
        with patch("app.api.feed.get_feed", new_callable=AsyncMock) as m:
            m.return_value = {"items": [], "total": 0, "page": 1, "limit": 20}
            await client.get("/feed")
            m.assert_called_once_with(category=None, sort="recent", page=1, limit=20)

    @pytest.mark.asyncio
    async def test_feed_custom_pagination(self, client):
        with patch("app.api.feed.get_feed", new_callable=AsyncMock) as m:
            m.return_value = {"items": [], "total": 0, "page": 3, "limit": 10}
            await client.get("/feed?page=3&limit=10")
            m.assert_called_once_with(category=None, sort="recent", page=3, limit=10)

    @pytest.mark.asyncio
    async def test_feed_category_filter(self, client):
        with patch("app.api.feed.get_feed", new_callable=AsyncMock) as m:
            m.return_value = {"items": [], "total": 0, "page": 1, "limit": 20}
            response = await client.get("/feed?category=Health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_feed_invalid_category_returns_422(self, client):
        response = await client.get("/feed?category=InvalidCategory")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_feed_sort_recent(self, client):
        with patch("app.api.feed.get_feed", new_callable=AsyncMock) as m:
            m.return_value = {"items": [], "total": 0, "page": 1, "limit": 20}
            response = await client.get("/feed?sort=recent")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_feed_sort_impact(self, client):
        with patch("app.api.feed.get_feed", new_callable=AsyncMock) as m:
            m.return_value = {"items": [], "total": 0, "page": 1, "limit": 20}
            response = await client.get("/feed?sort=impact")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_feed_sort_trending(self, client):
        with patch("app.api.feed.get_feed", new_callable=AsyncMock) as m:
            m.return_value = {"items": [], "total": 0, "page": 1, "limit": 20}
            response = await client.get("/feed?sort=trending")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_feed_invalid_sort_returns_422(self, client):
        response = await client.get("/feed?sort=invalid_sort")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_feed_page_zero_returns_422(self, client):
        response = await client.get("/feed?page=0")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_feed_negative_page_returns_422(self, client):
        response = await client.get("/feed?page=-1")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_feed_limit_zero_returns_422(self, client):
        response = await client.get("/feed?limit=0")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_feed_limit_exceeds_max_returns_422(self, client):
        response = await client.get("/feed?limit=101")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_feed_limit_at_max(self, client):
        """limit=100 is the max allowed and should succeed."""
        with patch("app.api.feed.get_feed", new_callable=AsyncMock) as m:
            m.return_value = {"items": [], "total": 0, "page": 1, "limit": 100}
            response = await client.get("/feed?limit=100")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_feed_db_error_returns_empty(self, client):
        """When the DB throws, the endpoint should gracefully return empty."""
        with patch("app.api.feed.get_feed", new_callable=AsyncMock) as m:
            m.side_effect = Exception("DB connection lost")
            data = (await client.get("/feed")).json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_feed_combined_params(self, client):
        """All query params used together."""
        with patch("app.api.feed.get_feed", new_callable=AsyncMock) as m:
            m.return_value = {"items": [], "total": 0, "page": 2, "limit": 5}
            response = await client.get("/feed?category=Politics&sort=impact&page=2&limit=5")
        assert response.status_code == 200


# ── GET /feed/trending ──────────────────────────────────────────────────────

class TestTrending:
    """Tests for GET /feed/trending."""

    @pytest.mark.asyncio
    async def test_trending_returns_200(self, client):
        with patch("app.api.feed.get_trending_claims", new_callable=AsyncMock) as m:
            m.return_value = []
            response = await client.get("/feed/trending")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_trending_empty(self, client):
        with patch("app.api.feed.get_trending_claims", new_callable=AsyncMock) as m:
            m.return_value = []
            data = (await client.get("/feed/trending")).json()
        assert data["clusters"] == []

    @pytest.mark.asyncio
    async def test_trending_with_data(self, client):
        mock_claims = [
            {"id": "inv-1", "query": "5G cancer?", "upvotes": 50},
            {"id": "inv-2", "query": "Flat earth?", "upvotes": 30},
        ]
        with patch("app.api.feed.get_trending_claims", new_callable=AsyncMock) as m:
            m.return_value = mock_claims
            data = (await client.get("/feed/trending")).json()
        assert len(data["clusters"]) == 2

    @pytest.mark.asyncio
    async def test_trending_db_error_returns_empty_clusters(self, client):
        with patch("app.api.feed.get_trending_claims", new_callable=AsyncMock) as m:
            m.side_effect = Exception("DB error")
            data = (await client.get("/feed/trending")).json()
        assert data["clusters"] == []

    @pytest.mark.asyncio
    async def test_trending_response_has_clusters_key(self, client):
        with patch("app.api.feed.get_trending_claims", new_callable=AsyncMock) as m:
            m.return_value = []
            data = (await client.get("/feed/trending")).json()
        assert "clusters" in data


# ── GET /feed/{investigation_id} ────────────────────────────────────────────

class TestGetReport:
    """Tests for GET /feed/{investigation_id}."""

    @pytest.mark.asyncio
    async def test_get_report_found(self, client):
        with patch("app.api.feed.get_investigation", new_callable=AsyncMock) as m:
            m.return_value = MOCK_INVESTIGATION
            response = await client.get("/feed/inv-001")
        assert response.status_code == 200
        assert response.json()["id"] == "inv-001"

    @pytest.mark.asyncio
    async def test_get_report_not_found_returns_404(self, client):
        with patch("app.api.feed.get_investigation", new_callable=AsyncMock) as m:
            m.return_value = None
            response = await client.get("/feed/nonexistent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_report_returns_full_data(self, client):
        with patch("app.api.feed.get_investigation", new_callable=AsyncMock) as m:
            m.return_value = MOCK_INVESTIGATION
            data = (await client.get("/feed/inv-001")).json()
        assert data["query"] == "Does 5G cause cancer?"
        assert data["verdict"] == "FALSE"
        assert data["confidence"] == 0.92

    @pytest.mark.asyncio
    async def test_get_report_db_error_returns_500(self, client):
        with patch("app.api.feed.get_investigation", new_callable=AsyncMock) as m:
            m.side_effect = Exception("DB exploded")
            response = await client.get("/feed/inv-001")
        assert response.status_code == 500
        assert "failed" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_report_calls_get_investigation_with_correct_id(self, client):
        with patch("app.api.feed.get_investigation", new_callable=AsyncMock) as m:
            m.return_value = MOCK_INVESTIGATION
            await client.get("/feed/abc-123-xyz")
            m.assert_called_once_with("abc-123-xyz")


# ── POST /feed/{investigation_id}/vote ──────────────────────────────────────

class TestVote:
    """Tests for POST /feed/{investigation_id}/vote."""

    @pytest.mark.asyncio
    async def test_vote_upvote_returns_200(self, client):
        with patch("app.api.feed.add_vote", new_callable=AsyncMock) as m:
            m.return_value = {"status": "ok", "vote_type": "upvote"}
            response = await client.post(
                "/feed/inv-001/vote",
                json={"vote_type": "upvote", "user_id": "user-1"},
            )
        assert response.status_code == 200
        assert response.json()["vote_type"] == "upvote"

    @pytest.mark.asyncio
    async def test_vote_flag_returns_200(self, client):
        with patch("app.api.feed.add_vote", new_callable=AsyncMock) as m:
            m.return_value = {"status": "ok", "vote_type": "flag"}
            response = await client.post(
                "/feed/inv-001/vote",
                json={"vote_type": "flag", "user_id": "user-2"},
            )
        assert response.status_code == 200
        assert response.json()["vote_type"] == "flag"

    @pytest.mark.asyncio
    async def test_vote_invalid_type_returns_422(self, client):
        response = await client.post(
            "/feed/inv-001/vote",
            json={"vote_type": "downvote", "user_id": "user-1"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_vote_missing_user_id_returns_422(self, client):
        response = await client.post(
            "/feed/inv-001/vote",
            json={"vote_type": "upvote"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_vote_missing_vote_type_returns_422(self, client):
        response = await client.post(
            "/feed/inv-001/vote",
            json={"user_id": "user-1"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_vote_empty_body_returns_422(self, client):
        response = await client.post("/feed/inv-001/vote", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_vote_no_body_returns_422(self, client):
        response = await client.post("/feed/inv-001/vote")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_vote_db_error_returns_500(self, client):
        with patch("app.api.feed.add_vote", new_callable=AsyncMock) as m:
            m.side_effect = Exception("DB write failed")
            response = await client.post(
                "/feed/inv-001/vote",
                json={"vote_type": "upvote", "user_id": "user-1"},
            )
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_vote_calls_add_vote_with_correct_args(self, client):
        with patch("app.api.feed.add_vote", new_callable=AsyncMock) as m:
            m.return_value = {"status": "ok", "vote_type": "upvote"}
            await client.post(
                "/feed/inv-001/vote",
                json={"vote_type": "upvote", "user_id": "user-1"},
            )
            from app.models.schemas import VoteType
            m.assert_called_once_with("inv-001", "user-1", VoteType.UPVOTE)
