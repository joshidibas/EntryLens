from pydantic import BaseModel


class ProviderResponse(BaseModel):
    subject_id: str | None = None
    similarity: float = 0.0
    bbox: dict[str, float] | None = None


class EnrollResponse(BaseModel):
    enrolled: bool
    face_count: int
    subject_id: str | None = None
