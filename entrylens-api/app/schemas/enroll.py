from pydantic import BaseModel, Field


class EnrollRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Name of the person to enroll")
    role: str = Field(default="visitor", pattern="^(staff|visitor)$")
    embedding: list[float] = Field(..., description="Face embedding vector from MediaPipe")


class EnrollResponse(BaseModel):
    enrolled: bool
    subject_id: str | None = None
    name: str
    face_count: int = 1
    message: str | None = None