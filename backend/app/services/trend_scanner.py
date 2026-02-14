"""Trend Scanner — proactive trending-topic ingestion.

Periodically fetches trending claims from 3 free sources:
  1. Google Trends  (pytrends — no API key)
  2. Reddit RSS     (r/news, r/worldnews — no API key)
  3. Google Fact Check API (key already in .env)

An LLM filters the best candidates and they are auto-investigated
through the existing pipeline, populating the investigations table
so the Early Warning Engine can detect spikes.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime

import httpx

from app.core.config import get_settings
from app.core.llm import get_llm
from app.agents.pipeline import run_investigation_simple
from app.core.database import save_investigation, get_recent_investigations

from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


# ── Source 1: Google Trends ────────────────────────────────────────────────

async def fetch_google_trends(limit: int = 10) -> list[str]:
    """Fetch today's trending searches from Google Trends via pytrends."""
    try:
        from pytrends.request import TrendReq

        # Run in executor because pytrends is synchronous
        loop = asyncio.get_event_loop()
        def _fetch():
            pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
            trending = pytrends.trending_searches(pn="united_states")
            return trending[0].tolist()[:limit]

        results = await loop.run_in_executor(None, _fetch)
        logger.info(f"Trend Scanner: fetched {len(results)} Google Trends")
        return results
    except Exception as e:
        logger.warning(f"Trend Scanner: Google Trends failed — {e}")
        return []


# ── Source 2: Reddit Hot Posts ─────────────────────────────────────────────

REDDIT_SUBS = ["news", "worldnews", "health", "technology", "science"]

async def fetch_reddit_trending(limit: int = 10) -> list[str]:
    """Fetch hot post titles from news-related subreddits via Reddit JSON API."""
    claims: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            for sub in REDDIT_SUBS:
                try:
                    url = f"https://www.reddit.com/r/{sub}/hot.json?limit=5"
                    resp = await client.get(
                        url,
                        headers={"User-Agent": "Veritas/1.0 (misinformation-detector)"},
                    )
                    if resp.status_code != 200:
                        continue
                    data = resp.json()
                    for post in data.get("data", {}).get("children", []):
                        title = post.get("data", {}).get("title", "")
                        if title and len(title) > 15:
                            claims.append(title)
                except Exception:
                    continue

        logger.info(f"Trend Scanner: fetched {len(claims)} Reddit headlines")
        return claims[:limit]
    except Exception as e:
        logger.warning(f"Trend Scanner: Reddit fetch failed — {e}")
        return []


# ── Source 3: Google Fact Check API ────────────────────────────────────────

async def fetch_recent_factchecks(limit: int = 10) -> list[str]:
    """Fetch recently fact-checked claims from Google Fact Check Tools API."""
    settings = get_settings()
    if not settings.google_factcheck_api_key:
        logger.warning("Trend Scanner: no Google Fact Check API key")
        return []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://factchecktools.googleapis.com/v1alpha1/claims:search",
                params={
                    "query": "trending news",
                    "key": settings.google_factcheck_api_key,
                    "pageSize": limit,
                    "languageCode": "en",
                },
            )
            if resp.status_code != 200:
                return []

            data = resp.json()
            claims = []
            for claim in data.get("claims", []):
                text = claim.get("text", "")
                if text:
                    claims.append(text)

            logger.info(f"Trend Scanner: fetched {len(claims)} fact-checked claims")
            return claims[:limit]
    except Exception as e:
        logger.warning(f"Trend Scanner: Fact Check API failed — {e}")
        return []


# ── LLM Filter ────────────────────────────────────────────────────────────

FILTER_PROMPT = """You are a claim selector for Veritas, a misinformation detection system.

Given a list of trending topics and headlines from Google Trends, Reddit, and fact-checkers,
select the top 5 that are most likely to be:
- Factual claims (not opinions or questions)
- Related to potential misinformation (health, politics, science, technology)
- Worth fact-checking (controversial, widely shared, or potentially harmful)

IMPORTANT: Rephrase each selection as a clear, investigable factual claim.

Respond in JSON:
{
    "claims": [
        "Claim 1 rephrased as an investigable statement",
        "Claim 2...",
        ...
    ]
}

Return at most 5 claims. If fewer than 5 are worth investigating, return fewer.
If none are worth investigating, return an empty list.
"""


async def filter_claims_with_llm(raw_claims: list[str]) -> list[str]:
    """Use the LLM to pick the top 5 investigation-worthy claims."""
    if not raw_claims:
        return []

    try:
        llm = get_llm(temperature=0.1)
        claims_text = "\n".join(f"- {c}" for c in raw_claims)

        messages = [
            SystemMessage(content=FILTER_PROMPT),
            HumanMessage(content=f"Here are the trending topics:\n{claims_text}"),
        ]

        response = await llm.ainvoke(messages)
        content = response.content.strip()

        # Parse JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        parsed = json.loads(content)
        claims = parsed.get("claims", [])

        logger.info(f"Trend Scanner: LLM selected {len(claims)} claims for investigation")
        return claims[:5]

    except Exception as e:
        logger.warning(f"Trend Scanner: LLM filter failed — {e}")
        # Fallback: return first 3 raw claims
        return raw_claims[:3]


# ── Deduplication ─────────────────────────────────────────────────────────

async def deduplicate_claims(claims: list[str]) -> list[str]:
    """Remove claims that are too similar to recent investigations."""
    try:
        recent = await get_recent_investigations(hours=24)
        recent_queries = {inv.get("query", "").lower() for inv in recent}

        deduped = []
        for claim in claims:
            claim_lower = claim.lower()
            # Simple overlap check
            is_duplicate = False
            for existing in recent_queries:
                words_new = set(claim_lower.split())
                words_existing = set(existing.split())
                if not words_new or not words_existing:
                    continue
                overlap = len(words_new & words_existing) / max(len(words_new | words_existing), 1)
                if overlap > 0.6:
                    is_duplicate = True
                    break

            if not is_duplicate:
                deduped.append(claim)

        logger.info(f"Trend Scanner: {len(deduped)}/{len(claims)} claims after dedup")
        return deduped
    except Exception:
        return claims


# ── Auto-Investigate ──────────────────────────────────────────────────────

async def auto_investigate(claims: list[str]):
    """Run each claim through the investigation pipeline."""
    for i, claim in enumerate(claims, 1):
        try:
            logger.info(f"Trend Scanner: auto-investigating ({i}/{len(claims)}): '{claim[:80]}'")
            report = await run_investigation_simple(query=claim, user_id=None)

            # Save to DB
            try:
                await save_investigation(report)
                logger.info(
                    f"Trend Scanner: saved investigation {report.id} — "
                    f"verdict={report.verdict.value}, confidence={report.confidence:.0%}"
                )
            except Exception as e:
                logger.error(f"Trend Scanner: failed to save investigation — {e}")

        except Exception as e:
            logger.error(f"Trend Scanner: investigation failed for '{claim[:50]}' — {e}")

        # Small delay between investigations to avoid rate limits
        if i < len(claims):
            await asyncio.sleep(5)


# ── Main Loop ─────────────────────────────────────────────────────────────

async def trend_scanner_loop(interval_seconds: int = 14400, initial_delay: int = 30):
    """Background loop that periodically scans trends and auto-investigates.

    Default: runs every 4 hours (14400s), first run after 30s delay.
    """
    logger.info(f"Trend Scanner: starting (interval={interval_seconds}s, initial_delay={initial_delay}s)")

    # Wait for server to fully start
    await asyncio.sleep(initial_delay)

    while True:
        try:
            await run_trend_scan()
        except asyncio.CancelledError:
            logger.info("Trend Scanner: stopped")
            break
        except Exception as e:
            logger.error(f"Trend Scanner: cycle error — {e}")

        await asyncio.sleep(interval_seconds)


async def run_trend_scan():
    """Execute one scan cycle: fetch → filter → deduplicate → investigate."""
    logger.info("Trend Scanner: starting scan cycle...")

    # 1. Fetch from all sources in parallel
    google_trends, reddit_trends, factcheck_claims = await asyncio.gather(
        fetch_google_trends(limit=10),
        fetch_reddit_trending(limit=10),
        fetch_recent_factchecks(limit=10),
        return_exceptions=True,
    )

    # Handle exceptions from gather
    if isinstance(google_trends, Exception):
        logger.warning(f"Google Trends error: {google_trends}")
        google_trends = []
    if isinstance(reddit_trends, Exception):
        logger.warning(f"Reddit error: {reddit_trends}")
        reddit_trends = []
    if isinstance(factcheck_claims, Exception):
        logger.warning(f"Fact Check error: {factcheck_claims}")
        factcheck_claims = []

    # 2. Combine all raw claims
    all_claims = []
    all_claims.extend(f"[Google Trends] {c}" for c in google_trends)
    all_claims.extend(f"[Reddit] {c}" for c in reddit_trends)
    all_claims.extend(f"[Fact Check] {c}" for c in factcheck_claims)

    if not all_claims:
        logger.warning("Trend Scanner: no claims fetched from any source")
        return

    logger.info(f"Trend Scanner: {len(all_claims)} raw claims from all sources")

    # 3. LLM filters top 5
    filtered = await filter_claims_with_llm(all_claims)

    if not filtered:
        logger.info("Trend Scanner: LLM found no claims worth investigating")
        return

    # 4. Deduplicate against recent investigations
    unique_claims = await deduplicate_claims(filtered)

    if not unique_claims:
        logger.info("Trend Scanner: all claims already investigated recently")
        return

    # 5. Auto-investigate
    logger.info(f"Trend Scanner: investigating {len(unique_claims)} claims")
    await auto_investigate(unique_claims)

    logger.info(f"Trend Scanner: cycle complete — investigated {len(unique_claims)} claims")
