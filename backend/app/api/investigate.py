from fastapi import APIRouter

router = APIRouter(prefix="/investigate", tags=["investigate"])


@router.post("")
async def investigate():
    """Run the LangGraph investigation pipeline. (SSE endpoint - TODO)"""
    return {"message": "Investigation endpoint — coming soon"}
