"""Investigation API — SSE streaming endpoint for the LangGraph pipeline."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.models.schemas import InvestigateRequest, InvestigationReport
from app.agents.pipeline import run_investigation, run_investigation_simple
from app.services.spam_filter import check_spam
from app.core.database import save_investigation, save_evidence, find_duplicate_investigation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/investigate", tags=["investigate"])


@router.post("", response_class=EventSourceResponse)
async def investigate(request: InvestigateRequest):
    """Run the LangGraph investigation pipeline, streaming each agent step via SSE."""

    # Spam check
    is_spam, spam_reason = await check_spam(request.query)
    if is_spam:
        raise HTTPException(status_code=400, detail=f"Query rejected: {spam_reason}")

    # Duplicate check — return existing report if recently investigated
    existing = await find_duplicate_investigation(request.query)
    if existing:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "This claim was already investigated recently.",
                "investigation_id": existing["id"],
            },
        )

    async def event_generator():
        report: InvestigationReport | None = None

        async for step_event in run_investigation(query=request.query):
            event_data = step_event.model_dump()

            # Capture the final report
            if step_event.agent == "pipeline" and step_event.status == "completed" and step_event.data:
                try:
                    report = InvestigationReport(**step_event.data)
                except Exception:
                    pass

            yield {
                "event": step_event.status,
                "data": json.dumps(event_data),
            }

        # Persist to database after streaming completes
        if report:
            try:
                await save_investigation(report)
                if report.evidence:
                    await save_evidence(report.evidence)
                logger.info(f"Saved investigation {report.id}")
            except Exception as e:
                logger.error(f"Failed to save investigation: {e}")

    return EventSourceResponse(event_generator())


@router.post("/sync")
async def investigate_sync(request: InvestigateRequest) -> dict:
    """Run the investigation pipeline synchronously (non-streaming). Returns full report."""

    is_spam, spam_reason = await check_spam(request.query)
    if is_spam:
        raise HTTPException(status_code=400, detail=f"Query rejected: {spam_reason}")

    try:
        report = await run_investigation_simple(query=request.query)
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="LLM rate limit exceeded. Please wait a moment and try again.",
            )
        if "404" in error_msg or "NOT_FOUND" in error_msg:
            raise HTTPException(
                status_code=503,
                detail=f"LLM model not available: {error_msg[:200]}",
            )
        logger.error(f"Investigation pipeline failed: {e}")
        raise HTTPException(status_code=500, detail="Investigation failed. Please try again.")

    # Persist
    try:
        await save_investigation(report)
        if report.evidence:
            await save_evidence(report.evidence)
    except Exception as e:
        logger.error(f"Failed to save investigation: {e}")

    return report.model_dump()
