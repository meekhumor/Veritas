import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api import health, investigate, feed, threats, news
from app.services.early_warning import early_warning_loop
from app.services.trend_scanner import trend_scanner_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Background task handle
_early_warning_task: asyncio.Task | None = None
_trend_scanner_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle — launches the Early Warning Engine."""
    global _early_warning_task, _trend_scanner_task
    logger.info("Veritas API starting up...")

    # Start early warning background loop (check every minute)
    _early_warning_task = asyncio.create_task(early_warning_loop(interval_seconds=60))
    logger.info("Early Warning Engine launched")

    # Start trend scanner (runs every 4 hours, first run after 30s)
    _trend_scanner_task = asyncio.create_task(
        trend_scanner_loop(interval_seconds=14400, initial_delay=30)
    )
    logger.info("Trend Scanner launched")

    yield

    # Shutdown
    for task in (_early_warning_task, _trend_scanner_task):
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    logger.info("Veritas API shut down")


app = FastAPI(
    title=settings.app_name,
    description="Multi-Source Misinformation & Social Risk Early Warning System",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(investigate.router)
app.include_router(feed.router)
app.include_router(threats.router)
app.include_router(news.router)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
    }
