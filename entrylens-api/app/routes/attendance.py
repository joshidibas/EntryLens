from fastapi import APIRouter, Depends

from app.auth import verify_api_key


router = APIRouter(prefix="/api/v1", tags=["attendance"])


@router.get("/attendance", dependencies=[Depends(verify_api_key)])
async def list_attendance() -> dict[str, list[dict[str, str]]]:
    return {"items": []}
