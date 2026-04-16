from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.errors import ModelErrorCode, model_http_exception
from app.services.model_runners.base import BaseModelRunner, ModelHealth
from app.services.model_runners.insightface_local import InsightFaceLocalRunner
from app.services.model_runners.mediapipe_browser import MediaPipeEmbeddingRunner


class ModelDefinition(BaseModel):
    id: str
    label: str
    description: str
    embedding_dimension: int = Field(gt=0)
    input_mode: Literal["browser-embedding", "image-data"]
    storage_table: str
    match_rpc: str
    enabled: bool = True
    status: Literal["ready", "experimental", "disabled"] = "ready"
    health: Literal["ok", "degraded", "unavailable"] = "ok"
    unavailable_reason: str | None = None
    load_strategy: Literal["eager", "lazy", "preloaded"] = "lazy"
    weight_source: str | None = None


LOCAL_DEFAULT_MODEL_ID = "local-default"
INSIGHTFACE_LOCAL_MODEL_ID = "insightface-local"
LEGACY_INSIGHTFACE_COLAB_MODEL_ID = "insightface-colab"


@lru_cache
def _runner_instances() -> dict[str, BaseModelRunner]:
    runners: dict[str, BaseModelRunner] = {
        LOCAL_DEFAULT_MODEL_ID: MediaPipeEmbeddingRunner(),
        INSIGHTFACE_LOCAL_MODEL_ID: InsightFaceLocalRunner(),
    }
    for model_id, runner in runners.items():
        if not isinstance(runner, BaseModelRunner):
            raise RuntimeError(f"Registered runner for {model_id} does not implement BaseModelRunner.")
    return runners


def get_runner(model_id: str) -> BaseModelRunner:
    runner = _runner_instances().get(model_id)
    if not runner:
        raise model_http_exception(
            status_code=404,
            error=ModelErrorCode.model_not_found,
            model_id=model_id,
            detail=f"Unknown recognition model: {model_id}",
        )
    return runner


def get_registered_models() -> list[ModelDefinition]:
    return [
        build_model_definition(LOCAL_DEFAULT_MODEL_ID),
        build_model_definition(INSIGHTFACE_LOCAL_MODEL_ID),
    ]


def get_model_definition(model_id: str) -> ModelDefinition:
    normalized = INSIGHTFACE_LOCAL_MODEL_ID if model_id == LEGACY_INSIGHTFACE_COLAB_MODEL_ID else model_id
    if normalized == LOCAL_DEFAULT_MODEL_ID:
        runner = get_runner(LOCAL_DEFAULT_MODEL_ID)
        health = runner.health()
        return ModelDefinition(
            id=LOCAL_DEFAULT_MODEL_ID,
            label="Local Default",
            description="Local recognition with MediaPipe browser embeddings.",
            embedding_dimension=16,
            input_mode="browser-embedding",
            storage_table="embeddings",
            match_rpc="match_embeddings",
            enabled=True,
            status="ready",
            health=health.status,
            unavailable_reason=health.detail if health.status != "ok" else None,
            load_strategy="lazy",
            weight_source=None,
        )
    if normalized == INSIGHTFACE_LOCAL_MODEL_ID:
        runner = get_runner(INSIGHTFACE_LOCAL_MODEL_ID)
        health = runner.health()
        return ModelDefinition(
            id=INSIGHTFACE_LOCAL_MODEL_ID,
            label="InsightFace (Local)",
            description="Backend-hosted InsightFace embedding extraction using a local runtime.",
            embedding_dimension=512,
            input_mode="image-data",
            storage_table="insightface_embeddings",
            match_rpc="match_insightface_embeddings",
            enabled=runner.is_available(),
            status="experimental" if runner.is_available() else "disabled",
            health=health.status,
            unavailable_reason=health.detail if health.status != "ok" else None,
            load_strategy="lazy",
            weight_source="local-runtime",
        )
    raise model_http_exception(
        status_code=404,
        error=ModelErrorCode.model_not_found,
        model_id=model_id,
        detail=f"Unknown recognition model: {model_id}",
    )


def build_model_definition(model_id: str) -> ModelDefinition:
    return get_model_definition(model_id)


def list_enabled_models() -> list[ModelDefinition]:
    return [model for model in get_registered_models() if model.enabled]


def is_model_available(model_id: str) -> bool:
    return get_model_definition(model_id).enabled


def get_model_health(model_id: str) -> ModelHealth:
    return get_runner(
        INSIGHTFACE_LOCAL_MODEL_ID if model_id == LEGACY_INSIGHTFACE_COLAB_MODEL_ID else model_id
    ).health()


def get_all_storage_tables() -> list[str]:
    return sorted({model.storage_table for model in get_registered_models()})


def probe_models_startup() -> dict[str, ModelHealth]:
    return {model_id: runner.startup_probe() for model_id, runner in _runner_instances().items()}
