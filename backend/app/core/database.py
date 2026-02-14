"""Database helpers for Supabase operations."""

from __future__ import annotations

import logging
from typing import Optional

from app.core.supabase import get_supabase_client
from app.models.schemas import (
    InvestigationReport,
    EvidenceItem,
    Threat,
    VoteType,
    ThreatStatus,
    Category,
)

logger = logging.getLogger(__name__)


# ── Investigations ─────────────────────────────────────────────────────────

async def save_investigation(report: InvestigationReport) -> dict:
    """Save a completed investigation to Supabase."""
    client = get_supabase_client()
    data = report.model_dump()
    # Serialize nested models
    if data.get("cross_reference"):
        data["cross_reference"] = report.cross_reference.model_dump()
    if data.get("impact"):
        data["impact"] = report.impact.model_dump()
    data["evidence"] = [e.model_dump() for e in report.evidence]

    result = client.table("investigations").insert(data).execute()
    return result.data[0] if result.data else {}


async def get_investigation(investigation_id: str) -> Optional[dict]:
    """Fetch a single investigation by ID."""
    client = get_supabase_client()
    result = (
        client.table("investigations")
        .select("*")
        .eq("id", investigation_id)
        .single()
        .execute()
    )
    return result.data


async def get_feed(
    category: Optional[Category] = None,
    sort: str = "recent",
    page: int = 1,
    limit: int = 20,
) -> dict:
    """Fetch paginated feed of published investigations."""
    client = get_supabase_client()
    query = client.table("investigations").select("*", count="exact").eq("is_published", True)

    if category:
        query = query.eq("category", category.value)

    if sort == "recent":
        query = query.order("created_at", desc=True)
    elif sort == "impact":
        query = query.order("impact->overall", desc=True)
    elif sort == "trending":
        query = query.order("upvotes", desc=True)

    offset = (page - 1) * limit
    query = query.range(offset, offset + limit - 1)
    result = query.execute()

    return {"items": result.data or [], "total": result.count or 0, "page": page, "limit": limit}


async def get_trending_claims(limit: int = 10) -> list[dict]:
    """Fetch trending claim clusters (most investigated recently)."""
    client = get_supabase_client()
    result = (
        client.table("investigations")
        .select("id, query, category, verdict, confidence, upvotes, created_at")
        .eq("is_published", True)
        .order("upvotes", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


# ── Evidence ───────────────────────────────────────────────────────────────

async def find_duplicate_investigation(query: str, hours: int = 24) -> Optional[dict]:
    """Check if a near-identical investigation was published recently."""
    client = get_supabase_client()
    normalised = query.strip().lower()
    # Exact-match on lower-cased query within the last N hours
    from datetime import datetime, timedelta, timezone
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    result = (
        client.table("investigations")
        .select("id, query, verdict, confidence, created_at")
        .ilike("query", normalised)
        .gte("created_at", cutoff)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


async def save_evidence(items: list[EvidenceItem]) -> list[dict]:
    """Save evidence items to Supabase."""
    if not items:
        return []
    client = get_supabase_client()
    data = [item.model_dump() for item in items]
    result = client.table("evidence").insert(data).execute()
    return result.data or []


# ── Votes ──────────────────────────────────────────────────────────────────

async def add_vote(investigation_id: str, user_id: str, vote_type: VoteType) -> dict:
    """Add a vote (upvote/flag) to an investigation. Prevents duplicate votes."""
    client = get_supabase_client()

    # Check for existing vote by this user
    existing = (
        client.table("votes")
        .select("vote_type")
        .eq("investigation_id", investigation_id)
        .eq("user_id", user_id)
        .execute()
    )
    old_vote = existing.data[0] if existing.data else None

    # Already voted with the same type → no-op
    if old_vote and old_vote["vote_type"] == vote_type.value:
        return {"status": "already_voted", "vote_type": vote_type.value}

    # Upsert vote
    vote_data = {
        "investigation_id": investigation_id,
        "user_id": user_id,
        "vote_type": vote_type.value,
    }
    client.table("votes").upsert(vote_data, on_conflict="investigation_id,user_id").execute()

    # Update counts on investigation
    inv = await get_investigation(investigation_id)
    if inv:
        updates = {}
        if old_vote:
            # Switching vote type: decrement old, increment new
            old_field = "upvotes" if old_vote["vote_type"] == "upvote" else "flags"
            new_field = "upvotes" if vote_type == VoteType.UPVOTE else "flags"
            updates[old_field] = max(0, inv.get(old_field, 0) - 1)
            updates[new_field] = inv.get(new_field, 0) + 1
        else:
            # New vote
            field = "upvotes" if vote_type == VoteType.UPVOTE else "flags"
            updates[field] = inv.get(field, 0) + 1
        client.table("investigations").update(updates).eq("id", investigation_id).execute()

    return {"status": "ok", "vote_type": vote_type.value}


# ── Threats ────────────────────────────────────────────────────────────────


async def get_dashboard_stats() -> dict:
    """Fetch aggregate stats for the dashboard."""
    client = get_supabase_client()

    # Total investigations
    all_inv = (
        client.table("investigations")
        .select("verdict, confidence", count="exact")
        .eq("is_published", True)
        .execute()
    )
    total = all_inv.count or 0
    items = all_inv.data or []

    # Verdict breakdown
    verdicts = {}
    confidence_sum = 0
    for inv in items:
        v = (inv.get("verdict") or "unverified").lower()
        verdicts[v] = verdicts.get(v, 0) + 1
        confidence_sum += inv.get("confidence", 0) or 0

    avg_confidence = round(confidence_sum / total, 2) if total else 0

    # Active threats count
    threats_res = (
        client.table("threats")
        .select("id", count="exact")
        .eq("status", ThreatStatus.ACTIVE.value)
        .execute()
    )
    active_threats = threats_res.count or 0

    return {
        "total_investigations": total,
        "avg_confidence": avg_confidence,
        "active_threats": active_threats,
        "verdicts": verdicts,
    }

async def save_threat(threat: Threat) -> dict:
    """Save or update a threat."""
    client = get_supabase_client()
    data = threat.model_dump()
    result = client.table("threats").upsert(data).execute()
    return result.data[0] if result.data else {}


async def get_active_threats() -> list[dict]:
    """Fetch active threats."""
    client = get_supabase_client()
    result = (
        client.table("threats")
        .select("*")
        .eq("status", ThreatStatus.ACTIVE.value)
        .order("last_updated", desc=True)
        .execute()
    )
    return result.data or []


async def update_threat_status(threat_id: str, status: ThreatStatus) -> dict:
    """Update threat status."""
    client = get_supabase_client()
    result = (
        client.table("threats")
        .update({"status": status.value})
        .eq("id", threat_id)
        .execute()
    )
    return result.data[0] if result.data else {}


async def get_recent_investigations(hours: int = 2) -> list[dict]:
    """Fetch investigations from the last N hours for spike detection."""
    from datetime import datetime, timedelta

    client = get_supabase_client()
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    result = (
        client.table("investigations")
        .select("*")
        .gte("created_at", cutoff)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []
