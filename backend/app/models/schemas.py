"""Pydantic models for the Veritas investigation system."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid


# ── Enums ──────────────────────────────────────────────────────────────────

class Verdict(str, Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNVERIFIED = "UNVERIFIED"
    PARTIALLY_TRUE = "PARTIALLY_TRUE"
    MISLEADING = "MISLEADING"


class Category(str, Enum):
    HEALTH = "Health"
    FINANCE = "Finance"
    POLITICS = "Politics"
    TECH = "Tech"
    GENERAL = "General"


class ThreatStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    MONITORING = "monitoring"


class VoteType(str, Enum):
    UPVOTE = "upvote"
    FLAG = "flag"


class EvidenceType(str, Enum):
    WEB_SEARCH = "web_search"
    NEWS = "news"
    AUTHORITY = "authority"
    FACT_CHECK = "fact_check"


# ── Request Models ─────────────────────────────────────────────────────────

class InvestigateRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000, description="The claim or question to investigate")
    category: Optional[Category] = None


class ClarificationResponse(BaseModel):
    investigation_id: str
    answers: list[str]


class VoteRequest(BaseModel):
    vote_type: VoteType
    user_id: str


class FeedQuery(BaseModel):
    category: Optional[Category] = None
    sort: str = Field(default="recent", pattern="^(recent|impact|trending)$")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


# ── Evidence ───────────────────────────────────────────────────────────────

class EvidenceItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    investigation_id: str = ""
    source_type: EvidenceType
    source_name: str
    source_url: Optional[str] = None
    title: str
    content: str
    credibility_score: float = Field(default=0.5, ge=0.0, le=1.0)
    published_date: Optional[str] = None
    raw_data: Optional[dict] = None


# ── Impact Score ───────────────────────────────────────────────────────────

class ImpactDimension(BaseModel):
    score: float = Field(ge=0.0, le=100.0)
    explanation: str


class ImpactScore(BaseModel):
    overall: float = Field(ge=0.0, le=100.0)
    topic_sensitivity: ImpactDimension
    geographic_reach: ImpactDimension
    emotional_charge: ImpactDimension
    actionability: ImpactDimension
    vulnerable_populations: ImpactDimension


# ── Cross-Reference Result ─────────────────────────────────────────────────

class CrossReferenceResult(BaseModel):
    consensus_points: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    unique_findings: list[str] = Field(default_factory=list)
    source_agreement_score: float = Field(default=0.5, ge=0.0, le=1.0)
    summary: str = ""


# ── Investigation Report ──────────────────────────────────────────────────

class InvestigationReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    refined_query: Optional[str] = None
    category: Category = Category.GENERAL
    verdict: Verdict = Verdict.UNVERIFIED
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    summary: str = ""
    detailed_analysis: str = ""
    evidence: list[EvidenceItem] = Field(default_factory=list)
    cross_reference: Optional[CrossReferenceResult] = None
    impact: Optional[ImpactScore] = None
    investigation_trail: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    user_id: Optional[str] = None
    is_published: bool = False
    upvotes: int = 0
    flags: int = 0


# ── Threat ─────────────────────────────────────────────────────────────────

class Threat(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    category: Category = Category.GENERAL
    status: ThreatStatus = ThreatStatus.ACTIVE
    investigation_ids: list[str] = Field(default_factory=list)
    investigation_count: int = 0
    avg_confidence: float = 0.0
    avg_impact: float = 0.0
    first_seen: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    escalation_reason: str = ""


# ── SSE Event Models ──────────────────────────────────────────────────────

class SSEEvent(BaseModel):
    event: str
    data: dict


class AgentStepEvent(BaseModel):
    agent: str
    status: str  # "started" | "completed" | "error"
    message: str
    data: Optional[dict] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
