from fastapi import APIRouter, Depends

from app.auth import verify_api_key
from app.services.model_registry import get_model_definition, get_model_health, get_registered_models


router = APIRouter(prefix="/models", tags=["models"], dependencies=[Depends(verify_api_key)])


@router.get("")
async def list_models() -> dict[str, list[dict]]:
    return {"models": [model.model_dump() for model in get_registered_models()]}


@router.get("/{model_id}/health")
async def model_health(model_id: str) -> dict:
    health = get_model_health(model_id)
    model = get_model_definition(model_id)
    return {
        "model_id": model.id,
        "label": model.label,
        "health": health.status,
        "detail": health.detail,
        "last_success_at": health.last_success_at,
        "suggestion": health.suggestion,
    }
