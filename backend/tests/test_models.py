"""Tests for Pydantic models and schemas."""

import pytest
from app.models.schemas import (
    InvestigateRequest,
    InvestigationReport,
    EvidenceItem,
    EvidenceType,
    ImpactScore,
    ImpactDimension,
    CrossReferenceResult,
    Threat,
    VoteRequest,
    FeedQuery,
    Verdict,
    Category,
    ThreatStatus,
    VoteType,
    SSEEvent,
    AgentStepEvent,
)


class TestInvestigateRequest:
    def test_valid_request(self):
        req = InvestigateRequest(query="Does 5G cause cancer?")
        assert req.query == "Does 5G cause cancer?"
        assert req.category is None

    def test_with_category(self):
        req = InvestigateRequest(query="Test claim", category=Category.HEALTH)
        assert req.category == Category.HEALTH

    def test_min_length_validation(self):
        with pytest.raises(Exception):
            InvestigateRequest(query="ab")

    def test_max_length_validation(self):
        with pytest.raises(Exception):
            InvestigateRequest(query="x" * 1001)


class TestEvidenceItem:
    def test_defaults(self):
        item = EvidenceItem(
            source_type=EvidenceType.WEB_SEARCH,
            source_name="test",
            title="Test",
            content="Content",
        )
        assert item.credibility_score == 0.5
        assert item.id is not None
        assert item.source_url is None

    def test_all_evidence_types(self):
        for et in EvidenceType:
            item = EvidenceItem(
                source_type=et, source_name="test", title="T", content="C"
            )
            assert item.source_type == et


class TestImpactScore:
    def test_valid_score(self):
        dim = ImpactDimension(score=75, explanation="Test")
        score = ImpactScore(
            overall=70,
            topic_sensitivity=dim,
            geographic_reach=dim,
            emotional_charge=dim,
            actionability=dim,
            vulnerable_populations=dim,
        )
        assert score.overall == 70

    def test_score_bounds(self):
        with pytest.raises(Exception):
            ImpactDimension(score=101, explanation="Too high")
        with pytest.raises(Exception):
            ImpactDimension(score=-1, explanation="Too low")


class TestInvestigationReport:
    def test_defaults(self):
        report = InvestigationReport(query="Test")
        assert report.verdict == Verdict.UNVERIFIED
        assert report.confidence == 0.0
        assert report.evidence == []
        assert report.is_published is False
        assert report.upvotes == 0

    def test_serialization(self):
        report = InvestigationReport(
            query="Test",
            verdict=Verdict.TRUE,
            confidence=0.95,
            summary="Verified",
        )
        data = report.model_dump()
        assert data["verdict"] == "TRUE"
        assert data["confidence"] == 0.95


class TestThreat:
    def test_defaults(self):
        threat = Threat(title="Test threat", description="Desc")
        assert threat.status == ThreatStatus.ACTIVE
        assert threat.investigation_count == 0

    def test_all_statuses(self):
        for status in ThreatStatus:
            threat = Threat(title="T", description="D", status=status)
            assert threat.status == status


class TestVoteRequest:
    def test_upvote(self):
        vote = VoteRequest(vote_type=VoteType.UPVOTE, user_id="user-1")
        assert vote.vote_type == VoteType.UPVOTE

    def test_flag(self):
        vote = VoteRequest(vote_type=VoteType.FLAG, user_id="user-1")
        assert vote.vote_type == VoteType.FLAG


class TestFeedQuery:
    def test_defaults(self):
        q = FeedQuery()
        assert q.sort == "recent"
        assert q.page == 1
        assert q.limit == 20

    def test_custom_values(self):
        q = FeedQuery(category=Category.POLITICS, sort="impact", page=3, limit=50)
        assert q.category == Category.POLITICS
        assert q.sort == "impact"


class TestSSEEvent:
    def test_creation(self):
        event = SSEEvent(event="test", data={"key": "value"})
        assert event.event == "test"


class TestAgentStepEvent:
    def test_creation(self):
        event = AgentStepEvent(
            agent="query_analyzer",
            status="completed",
            message="Done",
        )
        assert event.agent == "query_analyzer"
        assert event.timestamp is not None
