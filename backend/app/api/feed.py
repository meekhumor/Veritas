from fastapi import APIRouter

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("")
async def get_feed():
    """Get paginated public feed of past investigations. (TODO)"""
    return {"items": [], "total": 0}


@router.get("/trending")
async def get_trending():
    """Get trending claim clusters. (TODO)"""
    return {"clusters": []}


@router.get("/{investigation_id}")
async def get_investigation(investigation_id: str):
    """Get full investigation report by ID. (TODO)"""
    return {"id": investigation_id, "message": "Coming soon"}


@router.post("/{investigation_id}/vote")
async def vote(investigation_id: str):
    """Upvote or flag an investigation. (TODO)"""
    return {"id": investigation_id, "message": "Vote recorded"}
