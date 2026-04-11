from pydantic import BaseModel, Field


class RecognizeRequest(BaseModel):
    embedding: list[float] = Field(..., description="Face embedding vector from MediaPipe")
    camera_id: str | None = Field(default=None, description="Optional camera identifier")


class RecognizeResponse(BaseModel):
    matched: bool
    identity_id: str | None = None
    name: str | None = None
    similarity: float = 0.0
    message: str | None = None