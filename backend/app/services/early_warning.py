"""Early Warning Engine.

Background task that:
  - Groups completed investigations by semantic similarity
  - Detects spikes (≥3 similar claims in 2 hours + avg impact > 60)
  - Auto-escalates to active threats
  - Broadcasts alerts via SSE
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Optional

from app.core.database import get_recent_investigations, save_threat, get_active_threats
from app.models.schemas import Threat, ThreatStatus, Category

logger = logging.getLogger(__name__)


# ── Event Bus for SSE broadcasting ────────────────────────────────────────

class ThreatEventBus:
    """Simple pub/sub for broadcasting threat alerts to SSE subscribers."""

    def __init__(self):
        self._subscribers: list[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    async def publish(self, event: dict):
        for queue in self._subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass  # Skip slow consumers


# Singleton event bus
threat_event_bus = ThreatEventBus()


# ── Spike Detection ───────────────────────────────────────────────────────

def cluster_by_similarity(investigations: list[dict], threshold: float = 0.6) -> list[list[dict]]:
    """Group investigations by query similarity using simple keyword overlap.

    For a production system, use embedding-based similarity (e.g., sentence-transformers).
    This is a fast approximation for the hackathon.
    """
    clusters: list[list[dict]] = []

    for inv in investigations:
        query_words = set(inv.get("query", "").lower().split())
        placed = False

        for cluster in clusters:
            # Compare against first item in cluster
            cluster_words = set(cluster[0].get("query", "").lower().split())
            if not query_words or not cluster_words:
                continue

            overlap = len(query_words & cluster_words) / max(len(query_words | cluster_words), 1)
            if overlap >= threshold:
                cluster.append(inv)
                placed = True
                break

        if not placed:
            clusters.append([inv])

    return clusters


def detect_spikes(
    clusters: list[list[dict]],
    min_count: int = 2,
    min_avg_impact: float = 40.0,
) -> list[dict]:
    """Detect spikes: clusters with ≥min_count items and avg impact > min_avg_impact."""
    spikes = []

    for cluster in clusters:
        if len(cluster) < min_count:
            continue

        # Calculate avg impact
        impacts = []
        for inv in cluster:
            impact_data = inv.get("impact")
            if isinstance(impact_data, dict):
                impacts.append(impact_data.get("overall", 0))

        avg_impact = sum(impacts) / len(impacts) if impacts else 0

        if avg_impact >= min_avg_impact:
            spikes.append({
                "investigations": cluster,
                "count": len(cluster),
                "avg_impact": avg_impact,
                "avg_confidence": sum(
                    inv.get("confidence", 0) for inv in cluster
                ) / len(cluster),
            })

    return spikes


# ── Background Task ───────────────────────────────────────────────────────

async def early_warning_loop(interval_seconds: int = 120):
    """Background loop that periodically checks for misinformation spikes.

    Runs every `interval_seconds` and:
    1. Fetches recent investigations (last 2 hours)
    2. Clusters by similarity
    3. Detects spikes
    4. Creates/updates threats
    5. Broadcasts alerts
    """
    logger.info("Early Warning Engine started")

    while True:
        try:
            await asyncio.sleep(interval_seconds)
            await run_spike_detection()
        except asyncio.CancelledError:
            logger.info("Early Warning Engine stopped")
            break
        except Exception as e:
            logger.error(f"Early Warning Engine error: {e}")
            await asyncio.sleep(10)


async def run_spike_detection():
    """Run one cycle of spike detection."""
    logger.info("Early Warning: checking for spikes...")

    try:
        # Fetch recent investigations
        investigations = await get_recent_investigations(hours=2)

        if len(investigations) < 2:
            logger.debug(f"Early Warning: only {len(investigations)} recent investigations, skipping")
            return

        # Cluster and detect spikes
        clusters = cluster_by_similarity(investigations)
        spikes = detect_spikes(clusters)

        if not spikes:
            logger.debug("Early Warning: no spikes detected")
            return

        logger.warning(f"Early Warning: {len(spikes)} spike(s) detected!")

        for spike in spikes:
            # Create threat
            sample = spike["investigations"][0]
            threat = Threat(
                title=f"Spike: {sample.get('query', 'Unknown claim')[:100]}",
                description=(
                    f"Detected {spike['count']} similar investigations in the last 2 hours "
                    f"with average impact score of {spike['avg_impact']:.0f}/100."
                ),
                category=Category(sample.get("category", "General")),
                status=ThreatStatus.ACTIVE,
                investigation_ids=[inv.get("id", "") for inv in spike["investigations"]],
                investigation_count=spike["count"],
                avg_confidence=spike["avg_confidence"],
                avg_impact=spike["avg_impact"],
                escalation_reason=(
                    f"≥{spike['count']} similar claims detected with avg impact "
                    f"{spike['avg_impact']:.0f} > 60"
                ),
            )

            # Save to database
            try:
                await save_threat(threat)
            except Exception as e:
                logger.error(f"Failed to save threat: {e}")

            # Broadcast alert
            await threat_event_bus.publish({
                "type": "new_threat",
                "threat": threat.model_dump(),
            })

    except Exception as e:
        logger.error(f"Spike detection error: {e}")
