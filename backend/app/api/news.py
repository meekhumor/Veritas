"""Trending News API — fetches headlines from Tavily + Google Fact Check for the sidebar."""

from __future__ import annotations

import logging
import time
from typing import Optional

import httpx
from fastapi import APIRouter

from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/news", tags=["news"])

# ── Simple in-memory cache ─────────────────────────────────────────────────

_cache: dict = {"items": [], "ts": 0}
CACHE_TTL = 1800  # 30 minutes


def _is_cache_fresh() -> bool:
    return bool(_cache["items"]) and (time.time() - _cache["ts"]) < CACHE_TTL


# ── Fetchers ───────────────────────────────────────────────────────────────

async def _fetch_tavily_trending() -> list[dict]:
    """Fetch trending / breaking news via Tavily search."""
    settings = get_settings()
    if not settings.tavily_api_key:
        return []

    try:
        from tavily import AsyncTavilyClient

        client = AsyncTavilyClient(api_key=settings.tavily_api_key)
        results = await client.search(
            query="India breaking news today controversial claims viral misinformation",
            search_depth="basic",
            max_results=8,
            topic="news",
        )

        items = []
        for r in results.get("results", []):
            url = r.get("url", "")
            items.append({
                "title": r.get("title", ""),
                "url": url,
                "source": url.split("/")[2] if url else "web",
                "snippet": (r.get("content", "") or "")[:200],
                "published_at": r.get("published_date"),
                "origin": "tavily",
            })
        return items
    except Exception as e:
        logger.error(f"Tavily trending fetch error: {e}")
        return []


async def _fetch_factcheck_claims() -> list[dict]:
    """Fetch recent claims from Google Fact Check Tools API."""
    settings = get_settings()
    if not settings.google_factcheck_api_key:
        return []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://factchecktools.googleapis.com/v1alpha1/claims:search",
                params={
                    "query": "trending",
                    "key": settings.google_factcheck_api_key,
                    "pageSize": 5,
                    "languageCode": "en",
                },
            )
            response.raise_for_status()
            data = response.json()

            items = []
            for claim in data.get("claims", []):
                reviews = claim.get("claimReview", [])
                review = reviews[0] if reviews else {}
                items.append({
                    "title": claim.get("text", ""),
                    "url": review.get("url", ""),
                    "source": review.get("publisher", {}).get("name", "fact-checker"),
                    "snippet": f"Rating: {review.get('textualRating', 'N/A')} — {review.get('title', '')}",
                    "published_at": review.get("reviewDate"),
                    "origin": "factcheck",
                })
            return items
    except Exception as e:
        logger.error(f"Google Fact Check trending fetch error: {e}")
        return []


# ── Merge & deduplicate ───────────────────────────────────────────────────

def _deduplicate(items: list[dict]) -> list[dict]:
    """Remove items with duplicate titles (case-insensitive)."""
    seen: set[str] = set()
    unique = []
    for item in items:
        key = item["title"].strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


# ── Endpoint ──────────────────────────────────────────────────────────────

@router.get("/trending")
async def trending_news():
    """Return up to 10 trending headlines, cached for 30 minutes."""
    if _is_cache_fresh():
        return {"items": _cache["items"]}

    tavily_items = await _fetch_tavily_trending()
    fc_items = await _fetch_factcheck_claims()

    merged = _deduplicate(tavily_items + fc_items)[:10]

    _cache["items"] = merged
    _cache["ts"] = time.time()

    return {"items": merged}
