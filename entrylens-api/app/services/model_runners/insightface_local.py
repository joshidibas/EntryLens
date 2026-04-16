from __future__ import annotations

import importlib.util
import sys
from io import BytesIO
from datetime import UTC, datetime

from fastapi import status

from app.config import get_settings
from app.sample_images import _decode_image_data_url
from app.schemas.errors import ModelErrorCode, model_http_exception
from app.services.model_runners.base import BaseModelRunner, ModelHealth, ResolvedEmbedding


class InsightFaceLocalRunner(BaseModelRunner):
    REQUIRED_DEPENDENCIES = ("insightface", "onnxruntime", "numpy", "PIL", "cv2")

    def __init__(self) -> None:
        self._settings = get_settings()
        self._face_app = None
        self._load_error: str | None = None
        self._last_success_at: str | None = None
        self._last_failure: str | None = None

    def is_available(self) -> bool:
        return not self._missing_dependencies()

    def _missing_dependencies(self) -> list[str]:
        return [dependency for dependency in self.REQUIRED_DEPENDENCIES if importlib.util.find_spec(dependency) is None]

    def _dependency_help_text(self) -> str:
        missing = self._missing_dependencies()
        if not missing:
            return self._python_runtime_help_text()
        missing_text = ", ".join(missing)
        base_message = (
            f"Missing backend packages: {missing_text}. "
            "Activate the API environment, then run `pip install -r entrylens-api/requirements.txt`."
        )
        runtime_help = self._python_runtime_help_text()
        return f"{base_message} {runtime_help}" if runtime_help else base_message

    def _python_runtime_help_text(self) -> str:
        major, minor = sys.version_info[:2]
        if (major, minor) >= (3, 13):
            return (
                "This machine is running Python 3.13, which is a poor fit for local InsightFace on Windows right now. "
                "Use a Python 3.11 or 3.12 virtual environment for the backend, or install Microsoft C++ Build Tools "
                "if you plan to compile InsightFace from source."
            )
        return ""

    def _runtime_summary(self) -> str:
        return (
            f"model={self._settings.insightface_model_name}, "
            f"ctx_id={self._settings.insightface_ctx_id}, "
            f"det_size={self._settings.insightface_det_size_tuple[0]}x{self._settings.insightface_det_size_tuple[1]}"
        )

    def _load_face_app(self):
        if self._face_app is not None:
            return self._face_app

        if not self.is_available():
            runtime_help = self._python_runtime_help_text()
            self._load_error = (
                "InsightFace runtime dependencies are not installed in the backend environment. "
                f"Missing: {', '.join(self._missing_dependencies())}."
            )
            if runtime_help:
                self._load_error = f"{self._load_error} {runtime_help}"
            raise model_http_exception(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                error=ModelErrorCode.model_unavailable,
                model_id="insightface-local",
                detail=self._load_error,
                suggestion=self._dependency_help_text(),
            )

        try:
            import numpy as np
            from PIL import Image
            from insightface.app import FaceAnalysis
        except Exception as exc:  # pragma: no cover - import surface depends on local env
            self._load_error = f"InsightFace dependencies could not be imported: {exc}"
            raise model_http_exception(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                error=ModelErrorCode.model_unavailable,
                model_id="insightface-local",
                detail=self._load_error,
                suggestion=self._dependency_help_text(),
            ) from exc

        try:
            app = FaceAnalysis(name=self._settings.insightface_model_name)
            app.prepare(
                ctx_id=self._settings.insightface_ctx_id,
                det_size=self._settings.insightface_det_size_tuple,
            )
        except Exception as exc:  # pragma: no cover - load behavior depends on local env
            self._load_error = (
                f"InsightFace model weights could not be prepared: {exc}. "
                f"Runtime: {self._runtime_summary()}."
            )
            raise model_http_exception(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                error=ModelErrorCode.model_unavailable,
                model_id="insightface-local",
                detail=self._load_error,
                suggestion=(
                    "Ensure the backend can download InsightFace weights on first run or that they already exist "
                    f"in the local cache. Runtime: {self._runtime_summary()}."
                ),
            ) from exc

        self._pil_image = Image
        self._np = np
        self._face_app = app
        self._load_error = None
        return self._face_app

    async def resolve_embedding(
        self,
        *,
        image_data_url: str | None,
        browser_embedding: list[float] | None,
        model_id: str,
        embedding_dimension: int,
    ) -> ResolvedEmbedding:
        if not image_data_url:
            raise model_http_exception(
                status_code=status.HTTP_400_BAD_REQUEST,
                error=ModelErrorCode.input_mode_mismatch,
                model_id=model_id,
                detail="This model expects an image capture instead of a browser embedding.",
                suggestion="Keep a face visible in the camera so the current frame can be sent to the backend.",
            )

        decoded = _decode_image_data_url(image_data_url)
        if not decoded:
            raise model_http_exception(
                status_code=status.HTTP_400_BAD_REQUEST,
                error=ModelErrorCode.input_mode_mismatch,
                model_id=model_id,
                detail="The provided image data URL could not be decoded.",
            )

        raw_bytes, _extension = decoded
        face_app = self._load_face_app()

        try:
            image = self._pil_image.open(BytesIO(raw_bytes)).convert("RGB")
            image_np = self._np.array(image)
            faces = face_app.get(image_np)
        except Exception as exc:
            self._last_failure = str(exc)
            raise model_http_exception(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error=ModelErrorCode.inference_failed,
                model_id=model_id,
                detail=f"InsightFace inference failed: {exc}",
            ) from exc

        if not faces:
            self._last_failure = "No face detected."
            raise model_http_exception(
                status_code=status.HTTP_400_BAD_REQUEST,
                error=ModelErrorCode.inference_failed,
                model_id=model_id,
                detail="InsightFace did not detect a face in the provided image.",
                suggestion="Use a clearer, front-facing image with a single visible face.",
            )

        best_face = max(
            faces,
            key=lambda face: float((face.bbox[2] - face.bbox[0]) * (face.bbox[3] - face.bbox[1])),
        )
        embedding = [float(value) for value in best_face.embedding]
        if len(embedding) != embedding_dimension:
            self._last_failure = f"Expected {embedding_dimension}, received {len(embedding)}."
            raise model_http_exception(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error=ModelErrorCode.embedding_dimension_mismatch,
                model_id=model_id,
                detail=f"Expected embedding dimension {embedding_dimension}, received {len(embedding)}.",
            )

        self._last_success_at = datetime.now(UTC).isoformat()
        self._last_failure = None
        return ResolvedEmbedding(model_id=model_id, embedding=embedding)

    def startup_probe(self) -> ModelHealth:
        try:
            self._load_face_app()
        except Exception:
            return self.health()
        return self.health()

    def health(self) -> ModelHealth:
        if not self.is_available():
            runtime_help = self._python_runtime_help_text()
            detail = (
                "InsightFace runtime dependencies are not installed in the backend environment. "
                f"Missing: {', '.join(self._missing_dependencies())}."
            )
            if runtime_help:
                detail = f"{detail} {runtime_help}"
            return ModelHealth(
                status="unavailable",
                detail=detail,
                suggestion=self._dependency_help_text(),
            )
        if self._load_error:
            return ModelHealth(
                status="unavailable",
                detail=self._load_error,
                suggestion=(
                    "Verify model weights and local runtime dependencies. "
                    f"Runtime: {self._runtime_summary()}."
                ),
            )
        if self._last_failure:
            return ModelHealth(
                status="degraded",
                detail=self._last_failure,
                last_success_at=self._last_success_at,
            )
        if self._face_app is None:
            return ModelHealth(
                status="ok",
                detail=f"InsightFace is available and will lazy-load on first inference. Runtime: {self._runtime_summary()}.",
            )
        return ModelHealth(
            status="ok",
            detail=f"InsightFace is loaded and ready. Runtime: {self._runtime_summary()}.",
            last_success_at=self._last_success_at,
        )
