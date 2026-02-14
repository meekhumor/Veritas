import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api import health, investigate, feed, threats
from app.services.early_warning import early_warning_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Background task handle
_early_warning_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle — launches the Early Warning Engine."""
    global _early_warning_task
    logger.info("Veritas API starting up...")

    # Start early warning background loop (check every 2 minutes)
    _early_warning_task = asyncio.create_task(early_warning_loop(interval_seconds=120))
    logger.info("Early Warning Engine launched")

    yield

    # Shutdown
    if _early_warning_task:
        _early_warning_task.cancel()
        try:
            await _early_warning_task
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


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
    }
