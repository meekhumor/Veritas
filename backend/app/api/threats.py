"""Threats API — active threats, SSE stream, clusters, and seed endpoint."""

from __future__ import annotations

import json
import logging
import asyncio

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.core.database import get_active_threats, get_recent_investigations, save_threat
from app.services.early_warning import (
    threat_event_bus,
    cluster_by_similarity,
)
from app.models.schemas import Threat, ThreatStatus, Category

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/threats", tags=["threats"])


@router.get("/active")
async def active_threats():
    """Get currently active early warning threats."""
    try:
        threats = await get_active_threats()
        return {"threats": threats}
    except Exception as e:
        logger.error(f"Active threats error: {e}")
        return {"threats": []}


@router.get("/stream")
async def stream_threats():
    """SSE stream for real-time threat alerts.

    Clients connect and receive threat events as they are detected
    by the Early Warning Engine.
    """
    async def event_generator():
        queue = threat_event_bus.subscribe()
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": "threat",
                        "data": json.dumps(event),
                    }
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield {"event": "ping", "data": ""}
        except asyncio.CancelledError:
            pass
        finally:
            threat_event_bus.unsubscribe(queue)

    return EventSourceResponse(event_generator())


@router.get("/clusters")
async def get_clusters():
    """Get current investigation clusters (trending topic groups).

    Returns groups of similar investigations from the last 6 hours,
    even before they become full threats.
    """
    try:
        investigations = await get_recent_investigations(hours=6)

        if len(investigations) < 2:
            return {"clusters": [], "total_investigations": len(investigations)}

        raw_clusters = cluster_by_similarity(investigations, threshold=0.4)

        # Format for frontend — only include clusters with 2+ items
        clusters = []
        for cluster in raw_clusters:
            if len(cluster) < 2:
                continue

            # Calculate cluster stats
            impacts = []
            for inv in cluster:
                impact_data = inv.get("impact")
                if isinstance(impact_data, dict):
                    impacts.append(impact_data.get("overall", 0))

            avg_impact = sum(impacts) / len(impacts) if impacts else 0

            clusters.append({
                "topic": cluster[0].get("query", "Unknown"),
                "count": len(cluster),
                "avg_impact": round(avg_impact, 1),
                "avg_confidence": round(
                    sum(inv.get("confidence", 0) for inv in cluster) / len(cluster),
                    2,
                ),
                "category": cluster[0].get("category", "General"),
                "latest": cluster[0].get("created_at", ""),
                "verdicts": list({inv.get("verdict", "UNVERIFIED") for inv in cluster}),
                "investigation_ids": [inv.get("id", "") for inv in cluster],
            })

        # Sort by count (most investigated first)
        clusters.sort(key=lambda c: c["count"], reverse=True)

        return {
            "clusters": clusters[:20],
            "total_investigations": len(investigations),
        }

    except Exception as e:
        logger.error(f"Clusters error: {e}")
        return {"clusters": [], "total_investigations": 0}


@router.post("/seed")
async def seed_threats():
    """Seed sample threats for demo/testing. Creates one of each status."""
    try:
        sample_threats = [
            Threat(
                title="Spike: Viral health misinformation about new vaccine side effects",
                description=(
                    "Detected 5 similar investigations in the last 2 hours "
                    "with average impact score of 78/100. Multiple sources reporting "
                    "unverified claims about severe reactions."
                ),
                category=Category.HEALTH,
                status=ThreatStatus.ACTIVE,
                investigation_count=5,
                avg_confidence=0.72,
                avg_impact=78,
                escalation_reason="≥5 similar claims detected with avg impact 78 > 40",
            ),
            Threat(
                title="Monitoring: Financial market manipulation claims spreading",
                description=(
                    "Detected 3 similar investigations about stock market manipulation "
                    "with average impact score of 55/100. Monitoring for escalation."
                ),
                category=Category.FINANCE,
                status=ThreatStatus.MONITORING,
                investigation_count=3,
                avg_confidence=0.58,
                avg_impact=55,
                escalation_reason="3 similar claims with moderate impact, monitoring",
            ),
            Threat(
                title="Resolved: Election interference conspiracy debunked",
                description=(
                    "Previously active threat about election fraud claims has been "
                    "resolved. 4 investigations confirmed the claims were false."
                ),
                category=Category.POLITICS,
                status=ThreatStatus.RESOLVED,
                investigation_count=4,
                avg_confidence=0.85,
                avg_impact=90,
                escalation_reason="Resolved: claims debunked by multiple fact-checkers",
            ),
        ]

        saved = []
        for threat in sample_threats:
            try:
                result = await save_threat(threat)
                saved.append(result)
            except Exception as e:
                logger.error(f"Failed to save seed threat: {e}")

        # Broadcast the active one via SSE
        active_threat = sample_threats[0]
        await threat_event_bus.publish({
            "type": "new_threat",
            "threat": active_threat.model_dump(),
        })

        return {
            "status": "ok",
            "seeded": len(saved),
            "message": f"Created {len(saved)} sample threats",
        }

    except Exception as e:
        logger.error(f"Seed threats error: {e}")
        return {"status": "error", "message": str(e)}
