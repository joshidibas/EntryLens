from pydantic import BaseModel, Field


class IdentitySummary(BaseModel):
    id: str
    display_name: str
    identity_type: str
    status: str = "active"
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    embedding_count: int = 0
    profile_sample_id: str | None = None


class IdentitySampleSummary(BaseModel):
    id: str
    created_at: str | None = None
    updated_at: str | None = None
    sample_kind: str = "face"
    image_path: str | None = None
    capture_source: str | None = None
    capture_confidence: float | None = None
    is_reference: bool = False
    is_profile_source: bool = False


class AddIdentitySampleRequest(BaseModel):
    embedding: list[float] = Field(..., description="Face embedding vector from MediaPipe")
    sample_kind: str = Field(default="face", min_length=1)
    image_path: str | None = Field(default=None, description="Optional stored path or object key for the image")
    image_data_url: str | None = Field(default=None, description="Optional captured frame as a data URL")
    capture_source: str | None = Field(default=None, description="Where the sample came from")
    capture_confidence: float | None = Field(default=None, description="Confidence seen when this sample was reviewed")


class AddIdentitySampleResponse(BaseModel):
    added: bool
    identity_id: str
    sample_count: int
    message: str | None = None


class IdentitySampleActionResponse(BaseModel):
    ok: bool
    identity_id: str
    sample_id: str
    message: str | None = None


class CandidateMatch(BaseModel):
    identity_id: str
    display_name: str
    identity_type: str
    similarity: float
    sample_count: int = 0


class IdentityDetail(BaseModel):
    id: str
    display_name: str
    identity_type: str
    status: str = "active"
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    sample_count: int = 0
    profile_sample_id: str | None = None


class CreateIdentityRequest(BaseModel):
    display_name: str = Field(..., min_length=1)
    identity_type: str = Field(default="visitor", min_length=1)
    status: str = Field(default="active", min_length=1)
    notes: str | None = None


class UpdateIdentityRequest(BaseModel):
    display_name: str = Field(..., min_length=1)
    identity_type: str = Field(default="visitor", min_length=1)
    status: str = Field(default="active", min_length=1)
    notes: str | None = None
