from pydantic import BaseModel, Field


class CreateDetectionLogRequest(BaseModel):
    embedding: list[float] = Field(..., description="Face embedding vector from MediaPipe")
    image_data_url: str | None = Field(default=None, description="Optional captured frame as a data URL")
    camera_id: str | None = None
    auto_similarity: float | None = None
    auto_identity_id: str | None = None
    auto_display_name: str | None = None


class DetectionLogIdentitySummary(BaseModel):
    id: str
    display_name: str
    identity_type: str
    status: str


class DetectionLogSummary(BaseModel):
    id: str
    source: str
    camera_id: str | None = None
    image_path: str | None = None
    auto_similarity: float | None = None
    auto_tagged: bool = False
    review_status: str
    detected_at: str | None = None
    current_identity: DetectionLogIdentitySummary | None = None
    auto_identity: DetectionLogIdentitySummary | None = None
    promoted_embedding_id: str | None = None


class DetectionLogDetail(BaseModel):
    id: str
    source: str
    camera_id: str | None = None
    image_path: str | None = None
    auto_similarity: float | None = None
    auto_display_name: str | None = None
    auto_tagged: bool = False
    review_status: str
    review_notes: str | None = None
    reviewed_at: str | None = None
    detected_at: str | None = None
    current_identity: DetectionLogIdentitySummary | None = None
    auto_identity: DetectionLogIdentitySummary | None = None
    promoted_embedding_id: str | None = None
    promoted_at: str | None = None
    embedding_present: bool = False


class CreateDetectionLogResponse(BaseModel):
    created: bool
    detection_log: DetectionLogDetail


class UpdateDetectionLogRequest(BaseModel):
    review_status: str | None = None
    review_notes: str | None = None
    display_name: str | None = None
    identity_type: str | None = None
    status: str | None = None


class MergeDetectionLogIdentityRequest(BaseModel):
    target_identity_id: str = Field(..., min_length=1)


class PromoteDetectionLogRequest(BaseModel):
    target_identity_id: str | None = None
    sample_kind: str = "face"
    capture_source: str = "detection-log"
    set_as_reference: bool = False
    set_as_profile: bool = False


class DetectionLogActionResponse(BaseModel):
    ok: bool
    detection_log_id: str
    message: str
