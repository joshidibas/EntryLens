from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class ResolvedEmbedding:
    model_id: str
    embedding: list[float]


@dataclass(frozen=True)
class ModelHealth:
    status: str
    detail: str | None = None
    last_success_at: str | None = None
    suggestion: str | None = None


class BaseModelRunner(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def resolve_embedding(
        self,
        *,
        image_data_url: str | None,
        browser_embedding: list[float] | None,
        model_id: str,
        embedding_dimension: int,
    ) -> ResolvedEmbedding:
        raise NotImplementedError

    @abstractmethod
    def health(self) -> ModelHealth:
        raise NotImplementedError

    def startup_probe(self) -> ModelHealth:
        return self.health()

    def _now_iso(self) -> str:
        return datetime.now(UTC).isoformat()
