"""Comprehensive tests for the health API endpoints.

Covers:
  - GET /         (root)
  - GET /health   (health check)
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


# ── Helpers ─────────────────────────────────────────────────────────────────

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── GET / ───────────────────────────────────────────────────────────────────

class TestRootEndpoint:
    """Tests for the root '/' endpoint."""

    @pytest.mark.asyncio
    async def test_root_returns_200(self, client):
        response = await client.get("/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_root_returns_app_name(self, client):
        data = (await client.get("/")).json()
        assert "name" in data
        assert data["name"] == "Veritas API"

    @pytest.mark.asyncio
    async def test_root_returns_version(self, client):
        data = (await client.get("/")).json()
        assert "version" in data
        assert data["version"] == "0.1.0"

    @pytest.mark.asyncio
    async def test_root_returns_docs_url(self, client):
        data = (await client.get("/")).json()
        assert data["docs"] == "/docs"

    @pytest.mark.asyncio
    async def test_root_response_keys(self, client):
        """Root should return exactly: name, version, docs."""
        data = (await client.get("/")).json()
        assert set(data.keys()) == {"name", "version", "docs"}


# ── GET /health ─────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, client):
        response = await client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_status_ok(self, client):
        data = (await client.get("/health")).json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_service_name(self, client):
        data = (await client.get("/health")).json()
        assert data["service"] == "veritas-api"

    @pytest.mark.asyncio
    async def test_health_response_keys(self, client):
        data = (await client.get("/health")).json()
        assert set(data.keys()) == {"status", "service"}

    @pytest.mark.asyncio
    async def test_health_is_json(self, client):
        response = await client.get("/health")
        assert response.headers["content-type"] == "application/json"
