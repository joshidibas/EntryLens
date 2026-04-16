from fastapi import status

from app.schemas.errors import ModelErrorCode, model_http_exception
from app.services.model_runners.base import BaseModelRunner, ModelHealth, ResolvedEmbedding


class MediaPipeEmbeddingRunner(BaseModelRunner):
    def is_available(self) -> bool:
        return True

    async def resolve_embedding(
        self,
        *,
        image_data_url: str | None,
        browser_embedding: list[float] | None,
        model_id: str,
        embedding_dimension: int,
    ) -> ResolvedEmbedding:
        if not browser_embedding:
            raise model_http_exception(
                status_code=status.HTTP_400_BAD_REQUEST,
                error=ModelErrorCode.input_mode_mismatch,
                model_id=model_id,
                detail="This model expects a browser-provided embedding.",
                suggestion="Keep a face visible until the browser embedding is ready, then try again.",
            )

        if len(browser_embedding) != embedding_dimension:
            raise model_http_exception(
                status_code=status.HTTP_400_BAD_REQUEST,
                error=ModelErrorCode.embedding_dimension_mismatch,
                model_id=model_id,
                detail=f"Expected embedding dimension {embedding_dimension}, received {len(browser_embedding)}.",
            )

        return ResolvedEmbedding(model_id=model_id, embedding=[float(value) for value in browser_embedding])

    def health(self) -> ModelHealth:
        return ModelHealth(status="ok", detail="Browser embedding passthrough is available.")
