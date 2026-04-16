from app.schemas.errors import ModelErrorCode, model_http_exception
from app.services.model_registry import (
    LEGACY_INSIGHTFACE_COLAB_MODEL_ID,
    get_model_definition,
    get_registered_models,
    get_runner,
)
from app.services.model_runners.base import ResolvedEmbedding


def get_supported_model_ids() -> list[str]:
    return [model.id for model in get_registered_models()]


async def resolve_embedding(*, model_id: str, embedding: list[float] | None, image_data_url: str | None) -> ResolvedEmbedding:
    model_def = get_model_definition(model_id)
    runner = get_runner(model_def.id)
    resolved = await runner.resolve_embedding(
        image_data_url=image_data_url,
        browser_embedding=embedding,
        model_id=model_def.id,
        embedding_dimension=model_def.embedding_dimension,
    )
    if len(resolved.embedding) != model_def.embedding_dimension:
        raise model_http_exception(
            status_code=500,
            error=ModelErrorCode.embedding_dimension_mismatch,
            model_id=model_def.id,
            detail=f"Expected embedding dimension {model_def.embedding_dimension}, received {len(resolved.embedding)}.",
        )
    if model_id == LEGACY_INSIGHTFACE_COLAB_MODEL_ID:
        return ResolvedEmbedding(model_id=model_def.id, embedding=resolved.embedding)
    return resolved
