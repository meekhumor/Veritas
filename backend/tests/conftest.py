"""Shared test fixtures for the Veritas backend test suite."""

import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# Set test env vars before importing app modules
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("GOOGLE_API_KEY", "test-google-key")
os.environ.setdefault("TAVILY_API_KEY", "test-tavily-key")
os.environ.setdefault("MEDIACLOUD_API_KEY", "test-mediacloud-key")
os.environ.setdefault("GOOGLE_FACTCHECK_API_KEY", "test-factcheck-key")
os.environ.setdefault("FRONTEND_URL", "http://localhost:5173")
os.environ.setdefault("DEBUG", "true")

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.agents.state import InvestigationState
from app.models.schemas import (
    EvidenceItem,
    EvidenceType,
    CrossReferenceResult,
    ImpactScore,
    ImpactDimension,
    Category,
    Verdict,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Async HTTP test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_state() -> InvestigationState:
    """A pre-populated investigation state for testing agents."""
    return InvestigationState(
        query="Does 5G cause cancer?",
        investigation_id="test-inv-001",
        refined_query="Does 5G radiation cause cancer in humans?",
        category=Category.HEALTH,
    )


@pytest.fixture
def sample_state_with_evidence(sample_state) -> InvestigationState:
    """State with evidence already gathered."""
    evidence = [
        EvidenceItem(
            investigation_id="test-inv-001",
            source_type=EvidenceType.WEB_SEARCH,
            source_name="example.com",
            source_url="https://example.com/5g-study",
            title="5G and Health: What Science Says",
            content="Multiple studies have shown no link between 5G frequencies and cancer. The WHO classifies RF radiation as a Group 2B carcinogen, but this applies to all RF not specifically 5G.",
            credibility_score=0.7,
        ),
        EvidenceItem(
            investigation_id="test-inv-001",
            source_type=EvidenceType.AUTHORITY,
            source_name="who.int",
            source_url="https://www.who.int/5g",
            title="WHO Statement on 5G and Health",
            content="To date, and after much research, no adverse health effect has been causally linked with exposure to wireless technologies including 5G.",
            credibility_score=0.95,
        ),
        EvidenceItem(
            investigation_id="test-inv-001",
            source_type=EvidenceType.FACT_CHECK,
            source_name="Snopes",
            source_url="https://www.snopes.com/5g-cancer",
            title="Does 5G Cause Cancer?",
            content="Claim: 5G causes cancer.\nRating: False\nReview: No scientific evidence supports the claim that 5G causes cancer.",
            credibility_score=0.85,
        ),
    ]
    sample_state.evidence = evidence
    return sample_state


@pytest.fixture
def sample_cross_reference() -> CrossReferenceResult:
    return CrossReferenceResult(
        consensus_points=[
            "No scientific evidence links 5G to cancer",
            "WHO has not found adverse health effects from 5G",
        ],
        contradictions=[
            "Some alternative health sources claim RF is harmful",
        ],
        unique_findings=[
            "WHO classification of RF as Group 2B applies broadly, not specifically to 5G",
        ],
        source_agreement_score=0.85,
        summary="Strong consensus across scientific and authoritative sources that 5G does not cause cancer.",
    )


@pytest.fixture
def sample_impact() -> ImpactScore:
    return ImpactScore(
        overall=72,
        topic_sensitivity=ImpactDimension(score=85, explanation="Health/safety topic"),
        geographic_reach=ImpactDimension(score=80, explanation="Global 5G rollout"),
        emotional_charge=ImpactDimension(score=70, explanation="Fear-based claim"),
        actionability=ImpactDimension(score=60, explanation="Could deter 5G adoption"),
        vulnerable_populations=ImpactDimension(score=65, explanation="Concerns elderly/health-anxious"),
    )


@pytest.fixture
def mock_llm_response():
    """Factory fixture to create mock LLM responses."""
    def _create(content: str):
        mock_response = MagicMock()
        mock_response.content = content
        return mock_response
    return _create


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    mock = MagicMock()
    mock.table.return_value = mock
    mock.select.return_value = mock
    mock.insert.return_value = mock
    mock.update.return_value = mock
    mock.upsert.return_value = mock
    mock.eq.return_value = mock
    mock.gte.return_value = mock
    mock.order.return_value = mock
    mock.limit.return_value = mock
    mock.range.return_value = mock
    mock.single.return_value = mock
    mock.execute.return_value = MagicMock(data=[], count=0)
    return mock
