"""Tests for the Early Warning Engine."""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.early_warning import (
    ThreatEventBus,
    cluster_by_similarity,
    detect_spikes,
    run_spike_detection,
)


# ── ThreatEventBus ────────────────────────────────────────────────────────

def test_event_bus_subscribe():
    bus = ThreatEventBus()
    q = bus.subscribe()
    assert isinstance(q, asyncio.Queue)
    assert len(bus._subscribers) == 1


def test_event_bus_unsubscribe():
    bus = ThreatEventBus()
    q = bus.subscribe()
    bus.unsubscribe(q)
    assert len(bus._subscribers) == 0


@pytest.mark.asyncio
async def test_event_bus_publish():
    bus = ThreatEventBus()
    q = bus.subscribe()
    await bus.publish({"type": "test", "data": "hello"})
    event = q.get_nowait()
    assert event["type"] == "test"


@pytest.mark.asyncio
async def test_event_bus_multiple_subscribers():
    bus = ThreatEventBus()
    q1 = bus.subscribe()
    q2 = bus.subscribe()
    await bus.publish({"type": "broadcast"})
    assert q1.get_nowait()["type"] == "broadcast"
    assert q2.get_nowait()["type"] == "broadcast"


# ── Clustering ────────────────────────────────────────────────────────────

def test_cluster_empty():
    clusters = cluster_by_similarity([])
    assert clusters == []


def test_cluster_single_item():
    investigations = [{"query": "Does 5G cause cancer?"}]
    clusters = cluster_by_similarity(investigations)
    assert len(clusters) == 1
    assert len(clusters[0]) == 1


def test_cluster_similar_items():
    investigations = [
        {"query": "Does 5G cause cancer"},
        {"query": "5G cancer risk in humans"},
        {"query": "Does 5G radiation cause cancer"},
    ]
    clusters = cluster_by_similarity(investigations, threshold=0.3)
    # With simple keyword overlap, these should cluster together
    assert len(clusters) <= 2  # Should find some overlap


def test_cluster_different_items():
    investigations = [
        {"query": "Does 5G cause cancer"},
        {"query": "Bitcoin price prediction for tomorrow"},
        {"query": "Is the moon landing fake"},
    ]
    clusters = cluster_by_similarity(investigations, threshold=0.5)
    assert len(clusters) == 3  # All different


# ── Spike Detection ──────────────────────────────────────────────────────

def test_detect_spikes_no_clusters():
    spikes = detect_spikes([])
    assert spikes == []


def test_detect_spikes_below_threshold():
    clusters = [
        [{"query": "test", "impact": {"overall": 80}}],  # only 1 item
        [{"query": "test"}, {"query": "test"}],  # only 2 items
    ]
    spikes = detect_spikes(clusters, min_count=3)
    assert len(spikes) == 0


def test_detect_spikes_above_threshold():
    cluster = [
        {"query": "vaccine causes autism", "impact": {"overall": 85}, "confidence": 0.7},
        {"query": "vaccines cause autism in kids", "impact": {"overall": 75}, "confidence": 0.8},
        {"query": "vaccine autism link", "impact": {"overall": 70}, "confidence": 0.6},
    ]
    spikes = detect_spikes([cluster], min_count=3, min_avg_impact=60)
    assert len(spikes) == 1
    assert spikes[0]["count"] == 3
    assert spikes[0]["avg_impact"] > 60


def test_detect_spikes_low_impact():
    cluster = [
        {"query": "harmless claim", "impact": {"overall": 20}, "confidence": 0.5},
        {"query": "harmless claim 2", "impact": {"overall": 30}, "confidence": 0.5},
        {"query": "harmless claim 3", "impact": {"overall": 25}, "confidence": 0.5},
    ]
    spikes = detect_spikes([cluster], min_count=3, min_avg_impact=60)
    assert len(spikes) == 0  # Impact too low


# ── Spike Detection Integration ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_spike_detection_few_investigations():
    """Should skip when fewer than 3 recent investigations."""
    with patch("app.services.early_warning.get_recent_investigations", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [{"query": "test"}]
        await run_spike_detection()  # Should not raise


@pytest.mark.asyncio
async def test_run_spike_detection_no_spikes():
    """Should run cleanly when no spikes detected."""
    investigations = [
        {"query": "claim A", "impact": {"overall": 30}, "confidence": 0.5},
        {"query": "claim B different", "impact": {"overall": 20}, "confidence": 0.5},
        {"query": "claim C unrelated", "impact": {"overall": 25}, "confidence": 0.5},
    ]
    with patch("app.services.early_warning.get_recent_investigations", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = investigations
        await run_spike_detection()  # Should not raise
