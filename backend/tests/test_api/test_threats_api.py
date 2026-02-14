"""Comprehensive tests for the threats API endpoints.

Covers:
  - GET /threats/active    (list active threats)
  - GET /threats/stream    (SSE stream route registration)
"""

import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app


# ── Helpers ─────────────────────────────────────────────────────────────────

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


MOCK_THREAT = {
    "id": "threat-001",
    "title": "Spike: COVID vaccine causes infertility",
    "description": "Detected 5 similar investigations in 2 hours with avg impact 78.",
    "category": "Health",
    "status": "active",
    "investigation_ids": ["inv-1", "inv-2", "inv-3", "inv-4", "inv-5"],
    "investigation_count": 5,
    "avg_confidence": 0.85,
    "avg_impact": 78.0,
    "first_seen": "2026-02-14T08:00:00",
    "last_updated": "2026-02-14T08:30:00",
    "escalation_reason": "≥5 similar claims with avg impact 78 > 60",
}


# ── GET /threats/active ─────────────────────────────────────────────────────

class TestActiveThreats:
    """Tests for GET /threats/active."""

    @pytest.mark.asyncio
    async def test_active_threats_returns_200(self, client):
        with patch("app.api.threats.get_active_threats", new_callable=AsyncMock) as m:
            m.return_value = []
            response = await client.get("/threats/active")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_active_threats_empty(self, client):
        with patch("app.api.threats.get_active_threats", new_callable=AsyncMock) as m:
            m.return_value = []
            data = (await client.get("/threats/active")).json()
        assert data["threats"] == []

    @pytest.mark.asyncio
    async def test_active_threats_with_data(self, client):
        with patch("app.api.threats.get_active_threats", new_callable=AsyncMock) as m:
            m.return_value = [MOCK_THREAT]
            data = (await client.get("/threats/active")).json()
        assert len(data["threats"]) == 1
        assert data["threats"][0]["id"] == "threat-001"

    @pytest.mark.asyncio
    async def test_active_threats_multiple(self, client):
        threats = [
            {**MOCK_THREAT, "id": "threat-001"},
            {**MOCK_THREAT, "id": "threat-002", "title": "Spike: Election fraud claims"},
            {**MOCK_THREAT, "id": "threat-003", "title": "Spike: Climate hoax"},
        ]
        with patch("app.api.threats.get_active_threats", new_callable=AsyncMock) as m:
            m.return_value = threats
            data = (await client.get("/threats/active")).json()
        assert len(data["threats"]) == 3

    @pytest.mark.asyncio
    async def test_active_threats_response_has_threats_key(self, client):
        with patch("app.api.threats.get_active_threats", new_callable=AsyncMock) as m:
            m.return_value = []
            data = (await client.get("/threats/active")).json()
        assert "threats" in data

    @pytest.mark.asyncio
    async def test_active_threats_returns_full_threat_data(self, client):
        with patch("app.api.threats.get_active_threats", new_callable=AsyncMock) as m:
            m.return_value = [MOCK_THREAT]
            data = (await client.get("/threats/active")).json()
        threat = data["threats"][0]
        assert threat["title"] == "Spike: COVID vaccine causes infertility"
        assert threat["status"] == "active"
        assert threat["investigation_count"] == 5
        assert threat["avg_impact"] == 78.0

    @pytest.mark.asyncio
    async def test_active_threats_db_error_returns_empty(self, client):
        """When DB raises, endpoint should gracefully return empty."""
        with patch("app.api.threats.get_active_threats", new_callable=AsyncMock) as m:
            m.side_effect = Exception("Supabase connection timeout")
            data = (await client.get("/threats/active")).json()
        assert data["threats"] == []

    @pytest.mark.asyncio
    async def test_active_threats_is_json(self, client):
        with patch("app.api.threats.get_active_threats", new_callable=AsyncMock) as m:
            m.return_value = []
            response = await client.get("/threats/active")
        assert response.headers["content-type"] == "application/json"


# ── GET /threats/stream (SSE route) ─────────────────────────────────────────

class TestThreatStream:
    """Tests for GET /threats/stream (SSE endpoint)."""

    @pytest.mark.asyncio
    async def test_stream_route_exists(self, client):
        """Verify the /threats/stream route is registered on the app."""
        routes = [r for r in app.routes if hasattr(r, "path")]
        stream_routes = [r for r in routes if r.path == "/threats/stream"]
        assert len(stream_routes) == 1

    @pytest.mark.asyncio
    async def test_stream_route_is_get(self, client):
        """The stream route should respond to GET."""
        routes = [r for r in app.routes if hasattr(r, "path")]
        stream_routes = [r for r in routes if r.path == "/threats/stream"]
        assert stream_routes, "Route /threats/stream not found"
        route = stream_routes[0]
        assert "GET" in route.methods

    @pytest.mark.asyncio
    async def test_stream_post_not_allowed(self, client):
        """POST to /threats/stream should be 405 Method Not Allowed."""
        response = await client.post("/threats/stream")
        assert response.status_code == 405


# ── Route Registration ──────────────────────────────────────────────────────

class TestThreatRouteRegistration:
    """Verify that all expected threat routes are registered."""

    def test_active_route_registered(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/threats/active" in paths

    def test_stream_route_registered(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/threats/stream" in paths
