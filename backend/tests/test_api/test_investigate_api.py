"""Comprehensive tests for the investigate API endpoints.

Covers:
  - POST /investigate       (SSE streaming investigation)
  - POST /investigate/sync  (synchronous investigation)
  - Request validation      (min_length, max_length, schema)
"""

import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.schemas import (
    InvestigateRequest,
    InvestigationReport,
    AgentStepEvent,
    Category,
    Verdict,
)


# ── Helpers ─────────────────────────────────────────────────────────────────

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _make_report(**overrides) -> InvestigationReport:
    """Build a minimal InvestigationReport with sensible defaults."""
    defaults = dict(
        id="inv-test-001",
        query="Does 5G cause cancer?",
        refined_query="Does 5G radiation cause cancer in humans?",
        category=Category.HEALTH,
        verdict=Verdict.FALSE,
        confidence=0.92,
        summary="No scientific evidence links 5G to cancer.",
        detailed_analysis="Multiple peer-reviewed studies confirm no link.",
        evidence=[],
        cross_reference=None,
        impact=None,
        investigation_trail=["query_analyzer", "verdict_synthesizer"],
        is_published=True,
    )
    defaults.update(overrides)
    return InvestigationReport(**defaults)


# ── Request Model Validation ────────────────────────────────────────────────

class TestInvestigateRequestModel:
    """Direct Pydantic model validation for InvestigateRequest."""

    def test_valid_query(self):
        req = InvestigateRequest(query="Is the earth flat?")
        assert req.query == "Is the earth flat?"
        assert req.category is None

    def test_valid_query_with_category(self):
        req = InvestigateRequest(query="Is the earth flat?", category=Category.GENERAL)
        assert req.category == Category.GENERAL

    def test_query_too_short_raises(self):
        with pytest.raises(Exception):
            InvestigateRequest(query="ab")

    def test_query_exactly_min_length(self):
        req = InvestigateRequest(query="abc")
        assert len(req.query) == 3

    def test_query_too_long_raises(self):
        with pytest.raises(Exception):
            InvestigateRequest(query="x" * 1001)

    def test_query_exactly_max_length(self):
        req = InvestigateRequest(query="x" * 1000)
        assert len(req.query) == 1000

    def test_empty_query_raises(self):
        with pytest.raises(Exception):
            InvestigateRequest(query="")

    def test_missing_query_raises(self):
        with pytest.raises(Exception):
            InvestigateRequest()


# ── POST /investigate  (SSE streaming) ──────────────────────────────────────

class TestInvestigateSSE:
    """Tests for POST /investigate (streaming endpoint)."""

    @pytest.mark.asyncio
    async def test_spam_query_rejected_with_400(self, client):
        with patch("app.api.investigate.check_spam", new_callable=AsyncMock) as m:
            m.return_value = (True, "Detected as spam")
            response = await client.post(
                "/investigate", json={"query": "buy cheap viagra now!!!"}
            )
        assert response.status_code == 400
        assert "rejected" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_spam_check_reason_in_detail(self, client):
        with patch("app.api.investigate.check_spam", new_callable=AsyncMock) as m:
            m.return_value = (True, "Looks like advertising")
            response = await client.post(
                "/investigate", json={"query": "buy now free offer!!!"}
            )
        assert response.status_code == 400
        assert "Looks like advertising" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_query_too_short_returns_422(self, client):
        response = await client.post("/investigate", json={"query": "ab"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_query_returns_422(self, client):
        response = await client.post("/investigate", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_no_body_returns_422(self, client):
        response = await client.post("/investigate")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_valid_query_passes_spam_check(self, client):
        """Non-spam query should NOT be rejected at the spam-check step."""
        async def fake_stream(query, user_id=None):
            yield AgentStepEvent(
                agent="pipeline", status="started", message="Started"
            )
            yield AgentStepEvent(
                agent="pipeline",
                status="completed",
                message="Done",
                data=_make_report().model_dump(),
            )

        with (
            patch("app.api.investigate.check_spam", new_callable=AsyncMock) as spam_mock,
            patch("app.api.investigate.run_investigation", side_effect=fake_stream),
            patch("app.api.investigate.save_investigation", new_callable=AsyncMock),
            patch("app.api.investigate.save_evidence", new_callable=AsyncMock),
        ):
            spam_mock.return_value = (False, "")
            response = await client.post(
                "/investigate", json={"query": "Is the earth flat?"}
            )
        # SSE endpoint returns 200 with text/event-stream
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_sse_content_type(self, client):
        """Streaming endpoint should return text/event-stream."""
        async def fake_stream(query, user_id=None):
            yield AgentStepEvent(
                agent="pipeline", status="completed", message="Done"
            )

        with (
            patch("app.api.investigate.check_spam", new_callable=AsyncMock) as spam_mock,
            patch("app.api.investigate.run_investigation", side_effect=fake_stream),
            patch("app.api.investigate.save_investigation", new_callable=AsyncMock),
            patch("app.api.investigate.save_evidence", new_callable=AsyncMock),
        ):
            spam_mock.return_value = (False, "")
            response = await client.post(
                "/investigate", json={"query": "Is the earth flat?"}
            )
        assert "text/event-stream" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_sse_events_contain_agent_and_status(self, client):
        """Each SSE event data should contain 'agent' and 'status' fields."""
        events_emitted = []

        async def fake_stream(query, user_id=None):
            ev1 = AgentStepEvent(
                agent="query_analyzer", status="completed", message="Analyzed"
            )
            ev2 = AgentStepEvent(
                agent="pipeline", status="completed", message="Done"
            )
            events_emitted.extend([ev1, ev2])
            yield ev1
            yield ev2

        with (
            patch("app.api.investigate.check_spam", new_callable=AsyncMock) as spam_mock,
            patch("app.api.investigate.run_investigation", side_effect=fake_stream),
            patch("app.api.investigate.save_investigation", new_callable=AsyncMock),
            patch("app.api.investigate.save_evidence", new_callable=AsyncMock),
        ):
            spam_mock.return_value = (False, "")
            response = await client.post(
                "/investigate", json={"query": "Is the earth flat?"}
            )

        # Parse SSE events from response body
        body = response.text
        data_lines = [
            line.removeprefix("data: ")
            for line in body.splitlines()
            if line.startswith("data: ")
        ]
        for raw in data_lines:
            parsed = json.loads(raw)
            assert "agent" in parsed
            assert "status" in parsed

    @pytest.mark.asyncio
    async def test_investigation_saved_after_stream(self, client):
        """When the pipeline yields a completed report, it should be persisted."""
        report = _make_report()

        async def fake_stream(query, user_id=None):
            yield AgentStepEvent(
                agent="pipeline",
                status="completed",
                message="Done",
                data=report.model_dump(),
            )

        with (
            patch("app.api.investigate.check_spam", new_callable=AsyncMock) as spam_mock,
            patch("app.api.investigate.run_investigation", side_effect=fake_stream),
            patch("app.api.investigate.save_investigation", new_callable=AsyncMock) as save_mock,
            patch("app.api.investigate.save_evidence", new_callable=AsyncMock),
        ):
            spam_mock.return_value = (False, "")
            await client.post(
                "/investigate", json={"query": "Does 5G cause cancer?"}
            )
            save_mock.assert_called_once()


# ── POST /investigate/sync ──────────────────────────────────────────────────

class TestInvestigateSync:
    """Tests for POST /investigate/sync (non-streaming)."""

    @pytest.mark.asyncio
    async def test_sync_spam_rejected(self, client):
        with patch("app.api.investigate.check_spam", new_callable=AsyncMock) as m:
            m.return_value = (True, "Spam detected")
            response = await client.post(
                "/investigate/sync", json={"query": "spam spam spam"}
            )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_sync_returns_full_report(self, client):
        report = _make_report()

        with (
            patch("app.api.investigate.check_spam", new_callable=AsyncMock) as spam_mock,
            patch("app.api.investigate.run_investigation_simple", new_callable=AsyncMock) as run_mock,
            patch("app.api.investigate.save_investigation", new_callable=AsyncMock),
            patch("app.api.investigate.save_evidence", new_callable=AsyncMock),
        ):
            spam_mock.return_value = (False, "")
            run_mock.return_value = report
            response = await client.post(
                "/investigate/sync", json={"query": "Does 5G cause cancer?"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "inv-test-001"
        assert data["verdict"] == "FALSE"
        assert data["confidence"] == 0.92

    @pytest.mark.asyncio
    async def test_sync_returns_json(self, client):
        report = _make_report()

        with (
            patch("app.api.investigate.check_spam", new_callable=AsyncMock) as spam_mock,
            patch("app.api.investigate.run_investigation_simple", new_callable=AsyncMock) as run_mock,
            patch("app.api.investigate.save_investigation", new_callable=AsyncMock),
            patch("app.api.investigate.save_evidence", new_callable=AsyncMock),
        ):
            spam_mock.return_value = (False, "")
            run_mock.return_value = report
            response = await client.post(
                "/investigate/sync", json={"query": "Does 5G cause cancer?"}
            )

        assert response.headers["content-type"] == "application/json"

    @pytest.mark.asyncio
    async def test_sync_saves_investigation(self, client):
        report = _make_report()

        with (
            patch("app.api.investigate.check_spam", new_callable=AsyncMock) as spam_mock,
            patch("app.api.investigate.run_investigation_simple", new_callable=AsyncMock) as run_mock,
            patch("app.api.investigate.save_investigation", new_callable=AsyncMock) as save_mock,
            patch("app.api.investigate.save_evidence", new_callable=AsyncMock),
        ):
            spam_mock.return_value = (False, "")
            run_mock.return_value = report
            await client.post(
                "/investigate/sync", json={"query": "Does 5G cause cancer?"}
            )
            save_mock.assert_called_once_with(report)

    @pytest.mark.asyncio
    async def test_sync_saves_evidence_when_present(self, client):
        from app.models.schemas import EvidenceItem, EvidenceType

        evidence = [
            EvidenceItem(
                investigation_id="inv-test-001",
                source_type=EvidenceType.WEB_SEARCH,
                source_name="example.com",
                title="Test",
                content="Test content",
            )
        ]
        report = _make_report(evidence=evidence)

        with (
            patch("app.api.investigate.check_spam", new_callable=AsyncMock) as spam_mock,
            patch("app.api.investigate.run_investigation_simple", new_callable=AsyncMock) as run_mock,
            patch("app.api.investigate.save_investigation", new_callable=AsyncMock),
            patch("app.api.investigate.save_evidence", new_callable=AsyncMock) as ev_mock,
        ):
            spam_mock.return_value = (False, "")
            run_mock.return_value = report
            await client.post(
                "/investigate/sync", json={"query": "Does 5G cause cancer?"}
            )
            ev_mock.assert_called_once_with(evidence)

    @pytest.mark.asyncio
    async def test_sync_skips_save_evidence_when_empty(self, client):
        report = _make_report(evidence=[])

        with (
            patch("app.api.investigate.check_spam", new_callable=AsyncMock) as spam_mock,
            patch("app.api.investigate.run_investigation_simple", new_callable=AsyncMock) as run_mock,
            patch("app.api.investigate.save_investigation", new_callable=AsyncMock),
            patch("app.api.investigate.save_evidence", new_callable=AsyncMock) as ev_mock,
        ):
            spam_mock.return_value = (False, "")
            run_mock.return_value = report
            await client.post(
                "/investigate/sync", json={"query": "Does 5G cause cancer?"}
            )
            ev_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_save_failure_does_not_break_response(self, client):
        """If save_investigation raises, the endpoint should still return the report."""
        report = _make_report()

        with (
            patch("app.api.investigate.check_spam", new_callable=AsyncMock) as spam_mock,
            patch("app.api.investigate.run_investigation_simple", new_callable=AsyncMock) as run_mock,
            patch("app.api.investigate.save_investigation", new_callable=AsyncMock) as save_mock,
            patch("app.api.investigate.save_evidence", new_callable=AsyncMock),
        ):
            spam_mock.return_value = (False, "")
            run_mock.return_value = report
            save_mock.side_effect = Exception("DB down")
            response = await client.post(
                "/investigate/sync", json={"query": "Does 5G cause cancer?"}
            )

        # Should still return 200 with report data despite save failure
        assert response.status_code == 200
        assert response.json()["id"] == "inv-test-001"

    @pytest.mark.asyncio
    async def test_sync_query_too_short_returns_422(self, client):
        response = await client.post("/investigate/sync", json={"query": "ab"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_sync_missing_query_returns_422(self, client):
        response = await client.post("/investigate/sync", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_sync_report_contains_expected_fields(self, client):
        report = _make_report()

        with (
            patch("app.api.investigate.check_spam", new_callable=AsyncMock) as spam_mock,
            patch("app.api.investigate.run_investigation_simple", new_callable=AsyncMock) as run_mock,
            patch("app.api.investigate.save_investigation", new_callable=AsyncMock),
            patch("app.api.investigate.save_evidence", new_callable=AsyncMock),
        ):
            spam_mock.return_value = (False, "")
            run_mock.return_value = report
            response = await client.post(
                "/investigate/sync", json={"query": "Does 5G cause cancer?"}
            )

        data = response.json()
        expected_keys = {
            "id", "query", "refined_query", "category", "verdict",
            "confidence", "summary", "detailed_analysis", "evidence",
            "cross_reference", "impact", "investigation_trail",
            "created_at", "user_id", "is_published", "upvotes", "flags",
        }
        assert expected_keys.issubset(set(data.keys()))
