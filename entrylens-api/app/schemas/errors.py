from enum import Enum

from fastapi import HTTPException
from pydantic import BaseModel


class ModelErrorCode(str, Enum):
    model_not_found = "model_not_found"
    model_unavailable = "model_unavailable"
    model_degraded = "model_degraded"
    input_mode_mismatch = "input_mode_mismatch"
    embedding_dimension_mismatch = "embedding_dimension_mismatch"
    inference_failed = "inference_failed"


class ErrorResponse(BaseModel):
    error: str
    model_id: str | None = None
    detail: str
    suggestion: str | None = None


def model_http_exception(
    *,
    status_code: int,
    error: ModelErrorCode,
    detail: str,
    model_id: str | None = None,
    suggestion: str | None = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=ErrorResponse(
            error=error.value,
            model_id=model_id,
            detail=detail,
            suggestion=suggestion,
        ).model_dump(),
    )
