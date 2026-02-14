from fastapi import APIRouter

router = APIRouter(prefix="/threats", tags=["threats"])


@router.get("/active")
async def get_active_threats():
    """Get currently active early warning threats. (TODO)"""
    return {"threats": []}


@router.get("/stream")
async def stream_threats():
    """SSE stream for real-time threat alerts. (TODO)"""
    return {"message": "Threat stream — coming soon"}
