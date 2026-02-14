"""Feed API — paginated, filterable public feed of past investigations."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import Category, VoteRequest
from app.core.database import (
    get_feed,
    get_investigation,
    get_trending_claims,
    add_vote,
    get_dashboard_stats,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("")
async def list_feed(
    category: Optional[Category] = None,
    sort: str = Query(default="recent", pattern="^(recent|impact|trending)$"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Get paginated public feed of past investigations."""
    try:
        result = await get_feed(category=category, sort=sort, page=page, limit=limit)
        return result
    except Exception as e:
        logger.error(f"Feed error: {e}")
        return {"items": [], "total": 0, "page": page, "limit": limit}


@router.get("/trending")
async def trending():
    """Get trending claim clusters."""
    try:
        claims = await get_trending_claims()
        return {"clusters": claims}
    except Exception as e:
        logger.error(f"Trending error: {e}")
        return {"clusters": []}


@router.get("/stats")
async def stats():
    """Get aggregate dashboard stats."""
    try:
        return await get_dashboard_stats()
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {
            "total_investigations": 0,
            "avg_confidence": 0,
            "active_threats": 0,
            "verdicts": {},
        }


@router.get("/recent")
async def recent_activity():
    """Get 5 most recent investigations (compact)."""
    try:
        result = await get_feed(sort="recent", page=1, limit=5)
        items = [
            {
                "id": inv.get("id"),
                "query": inv.get("query", "")[:100],
                "verdict": inv.get("verdict"),
                "confidence": inv.get("confidence"),
                "category": inv.get("category"),
                "created_at": inv.get("created_at"),
            }
            for inv in result.get("items", [])
        ]
        return {"items": items}
    except Exception as e:
        logger.error(f"Recent activity error: {e}")
        return {"items": []}


@router.get("/{investigation_id}")
async def get_report(investigation_id: str):
    """Get full investigation report by ID."""
    try:
        report = await get_investigation(investigation_id)
        if not report:
            raise HTTPException(status_code=404, detail="Investigation not found")
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get report error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch investigation")


@router.post("/{investigation_id}/vote")
async def vote(investigation_id: str, request: VoteRequest):
    """Upvote or flag an investigation."""
    try:
        result = await add_vote(investigation_id, request.user_id, request.vote_type)
        return result
    except Exception as e:
        logger.error(f"Vote error: {e}")
        raise HTTPException(status_code=500, detail="Failed to record vote")
