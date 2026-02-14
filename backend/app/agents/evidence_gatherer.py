"""Agent 3 — Evidence Gatherer.

4 parallel sub-agents:
  - Web Search (Tavily API)
  - News Scanner (Media Cloud API)
  - Authority Checker (targeted Tavily search for WHO/CDC/govt)
  - Fact-Check Lookup (Google Fact Check API)
"""

from __future__ import annotations

import logging
import httpx
from datetime import datetime
from typing import Optional

from app.core.config import get_settings
from app.core.llm import get_llm
from app.agents.state import InvestigationState
from app.models.schemas import EvidenceItem, EvidenceType

logger = logging.getLogger(__name__)


# ── Sub-agent: Web Search (Tavily) ─────────────────────────────────────────

async def web_search(state: InvestigationState) -> dict:
    """Search the web using Tavily API."""
    settings = get_settings()
    query = state.refined_query or state.query
    evidence: list[EvidenceItem] = []

    logger.info(f"Web Search: searching for '{query}'")

    if not settings.tavily_api_key:
        logger.warning("Web Search: no Tavily API key configured")
        return {
            "web_search_done": True,
            "current_agent": "web_search",
            "investigation_trail": [
                f"[{datetime.utcnow().isoformat()}] Web Search: Skipped (no API key)"
            ],
        }

    try:
        from tavily import AsyncTavilyClient

        client = AsyncTavilyClient(api_key=settings.tavily_api_key)
        results = await client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True,
        )

        for result in results.get("results", []):
            evidence.append(
                EvidenceItem(
                    investigation_id=state.investigation_id,
                    source_type=EvidenceType.WEB_SEARCH,
                    source_name=result.get("url", "").split("/")[2] if result.get("url") else "web",
                    source_url=result.get("url"),
                    title=result.get("title", ""),
                    content=result.get("content", ""),
                    credibility_score=result.get("score", 0.5),
                    published_date=result.get("published_date"),
                    raw_data=result,
                )
            )

        trail = f"[{datetime.utcnow().isoformat()}] Web Search: Found {len(evidence)} results via Tavily"
    except Exception as e:
        logger.error(f"Web Search error: {e}")
        trail = f"[{datetime.utcnow().isoformat()}] Web Search: Error — {str(e)[:100]}"

    return {
        "evidence": evidence,
        "web_search_done": True,
        "current_agent": "web_search",
        "investigation_trail": [trail],
    }


# ── Sub-agent: News Scanner (Media Cloud) ──────────────────────────────────

async def news_scanner(state: InvestigationState) -> dict:
    """Scan news sources using Media Cloud API."""
    settings = get_settings()
    query = state.refined_query or state.query
    evidence: list[EvidenceItem] = []

    logger.info(f"News Scanner: searching for '{query}'")

    if not settings.mediacloud_api_key:
        logger.warning("News Scanner: no Media Cloud API key configured")
        return {
            "news_scan_done": True,
            "current_agent": "news_scanner",
            "investigation_trail": [
                f"[{datetime.utcnow().isoformat()}] News Scanner: Skipped (no API key)"
            ],
        }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://api.mediacloud.org/api/v2/stories_public/list",
                params={
                    "q": query,
                    "rows": 5,
                    "sort": "publish_date",
                    "key": settings.mediacloud_api_key,
                },
            )
            response.raise_for_status()
            stories = response.json()

            for story in stories:
                evidence.append(
                    EvidenceItem(
                        investigation_id=state.investigation_id,
                        source_type=EvidenceType.NEWS,
                        source_name=story.get("media_name", "news"),
                        source_url=story.get("url"),
                        title=story.get("title", ""),
                        content=story.get("title", ""),  # Media Cloud doesn't return full text
                        credibility_score=0.6,
                        published_date=story.get("publish_date"),
                        raw_data=story,
                    )
                )

        trail = f"[{datetime.utcnow().isoformat()}] News Scanner: Found {len(evidence)} articles via Media Cloud"
    except Exception as e:
        logger.error(f"News Scanner error: {e}")
        trail = f"[{datetime.utcnow().isoformat()}] News Scanner: Error — {str(e)[:100]}"

    return {
        "evidence": evidence,
        "news_scan_done": True,
        "current_agent": "news_scanner",
        "investigation_trail": [trail],
    }


# ── Sub-agent: Authority Checker (Tavily targeted) ─────────────────────────

async def authority_checker(state: InvestigationState) -> dict:
    """Search authoritative sources (WHO, CDC, govt sites) via Tavily."""
    settings = get_settings()
    query = state.refined_query or state.query
    evidence: list[EvidenceItem] = []

    logger.info(f"Authority Checker: searching for '{query}'")

    if not settings.tavily_api_key:
        logger.warning("Authority Checker: no Tavily API key configured")
        return {
            "authority_check_done": True,
            "current_agent": "authority_checker",
            "investigation_trail": [
                f"[{datetime.utcnow().isoformat()}] Authority Checker: Skipped (no API key)"
            ],
        }

    try:
        from tavily import AsyncTavilyClient

        client = AsyncTavilyClient(api_key=settings.tavily_api_key)

        authority_domains = [
            "who.int", "cdc.gov", "nih.gov", "fda.gov", "europa.eu",
            "gov.uk", "un.org", "reuters.com", "apnews.com",
        ]
        domain_filter = " OR ".join(f"site:{d}" for d in authority_domains)
        authority_query = f"{query} ({domain_filter})"

        results = await client.search(
            query=authority_query,
            search_depth="advanced",
            max_results=5,
            include_answer=True,
        )

        for result in results.get("results", []):
            url = result.get("url", "")
            is_authority = any(d in url for d in authority_domains)
            evidence.append(
                EvidenceItem(
                    investigation_id=state.investigation_id,
                    source_type=EvidenceType.AUTHORITY,
                    source_name=url.split("/")[2] if url else "authority",
                    source_url=url,
                    title=result.get("title", ""),
                    content=result.get("content", ""),
                    credibility_score=0.9 if is_authority else 0.6,
                    published_date=result.get("published_date"),
                    raw_data=result,
                )
            )

        trail = f"[{datetime.utcnow().isoformat()}] Authority Checker: Found {len(evidence)} authoritative sources"
    except Exception as e:
        logger.error(f"Authority Checker error: {e}")
        trail = f"[{datetime.utcnow().isoformat()}] Authority Checker: Error — {str(e)[:100]}"

    return {
        "evidence": evidence,
        "authority_check_done": True,
        "current_agent": "authority_checker",
        "investigation_trail": [trail],
    }


# ── Sub-agent: Fact-Check Lookup (Google Fact Check API) ───────────────────

async def fact_check_lookup(state: InvestigationState) -> dict:
    """Look up existing fact-checks via Google Fact Check Tools API."""
    settings = get_settings()
    query = state.refined_query or state.query
    evidence: list[EvidenceItem] = []

    logger.info(f"Fact-Check Lookup: searching for '{query}'")

    if not settings.google_factcheck_api_key:
        logger.warning("Fact-Check Lookup: no Google Fact Check API key configured")
        return {
            "fact_check_done": True,
            "current_agent": "fact_check_lookup",
            "investigation_trail": [
                f"[{datetime.utcnow().isoformat()}] Fact-Check Lookup: Skipped (no API key)"
            ],
        }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://factchecktools.googleapis.com/v1alpha1/claims:search",
                params={
                    "query": query,
                    "key": settings.google_factcheck_api_key,
                    "pageSize": 5,
                    "languageCode": "en",
                },
            )
            response.raise_for_status()
            data = response.json()

            for claim in data.get("claims", []):
                for review in claim.get("claimReview", []):
                    evidence.append(
                        EvidenceItem(
                            investigation_id=state.investigation_id,
                            source_type=EvidenceType.FACT_CHECK,
                            source_name=review.get("publisher", {}).get("name", "fact-checker"),
                            source_url=review.get("url"),
                            title=review.get("title", claim.get("text", "")),
                            content=(
                                f"Claim: {claim.get('text', '')}\n"
                                f"Rating: {review.get('textualRating', 'N/A')}\n"
                                f"Review: {review.get('title', '')}"
                            ),
                            credibility_score=0.85,
                            published_date=review.get("reviewDate"),
                            raw_data={"claim": claim, "review": review},
                        )
                    )

        trail = f"[{datetime.utcnow().isoformat()}] Fact-Check Lookup: Found {len(evidence)} fact-checks"
    except Exception as e:
        logger.error(f"Fact-Check Lookup error: {e}")
        trail = f"[{datetime.utcnow().isoformat()}] Fact-Check Lookup: Error — {str(e)[:100]}"

    return {
        "evidence": evidence,
        "fact_check_done": True,
        "current_agent": "fact_check_lookup",
        "investigation_trail": [trail],
    }
