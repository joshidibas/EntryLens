from pydantic import BaseModel, Field


class RecognizeRequest(BaseModel):
    model_id: str = Field(default="local-default", min_length=1, description="Selected Labs recognition model")
    embedding: list[float] | None = Field(default=None, description="Optional face embedding vector")
    image_data_url: str | None = Field(default=None, description="Optional captured frame as a data URL")
    camera_id: str | None = Field(default=None, description="Optional camera identifier")


class RecognizeResponse(BaseModel):
    matched: bool
    identity_id: str | None = None
    name: str | None = None
    similarity: float = 0.0
    message: str | None = None
