"""Threats API — active threats and SSE stream for real-time alerts."""

from __future__ import annotations

import json
import logging
import asyncio

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.core.database import get_active_threats
from app.services.early_warning import threat_event_bus

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
