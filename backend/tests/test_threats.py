"""Tests for threats API endpoints."""

import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_active_threats_empty():
    """Should return empty threats list."""
    with patch("app.api.threats.get_active_threats", new_callable=AsyncMock) as mock_threats:
        mock_threats.return_value = []

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/threats/active")

        assert response.status_code == 200
        assert response.json()["threats"] == []


@pytest.mark.asyncio
async def test_active_threats_with_data():
    """Should return threats when they exist."""
    mock_threats_data = [
        {
            "id": "threat-1",
            "title": "Spike: COVID vaccine claim",
            "status": "active",
            "investigation_count": 5,
            "avg_impact": 75.0,
        }
    ]

    with patch("app.api.threats.get_active_threats", new_callable=AsyncMock) as mock_threats:
        mock_threats.return_value = mock_threats_data

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/threats/active")

        assert response.status_code == 200
        data = response.json()
        assert len(data["threats"]) == 1
        assert data["threats"][0]["title"] == "Spike: COVID vaccine claim"


@pytest.mark.asyncio
async def test_threat_stream_endpoint_exists():
    """SSE stream endpoint should be accessible (verify route exists)."""
    # We only verify the route is registered, not the full SSE stream
    # because SSE streams are long-lived and will block tests.
    from starlette.routing import Route
    routes = [r for r in app.routes if hasattr(r, "path")]
    stream_routes = [r for r in routes if r.path == "/threats/stream"]
    assert len(stream_routes) == 1
