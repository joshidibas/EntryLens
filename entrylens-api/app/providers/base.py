from abc import ABC, abstractmethod

from app.providers.schemas import EnrollResponse, ProviderResponse


class FaceProvider(ABC):
    @abstractmethod
    async def identify(self, image_bytes: bytes) -> ProviderResponse:
        raise NotImplementedError

    @abstractmethod
    async def enroll(self, user_id: str, images: list[bytes]) -> EnrollResponse:
        raise NotImplementedError

    @abstractmethod
    async def delete_subject(self, subject_id: str) -> bool:
        raise NotImplementedError
