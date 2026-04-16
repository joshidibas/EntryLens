import asyncio
import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import get_settings
from app.sample_images import _decode_image_data_url


settings = get_settings()


@dataclass(frozen=True)
class InsightFaceColabResponse:
    embedding: list[float]
    face_detected: bool
    bbox: dict | None = None
    confidence: float | None = None


def _post_to_colab(image_data_url: str) -> InsightFaceColabResponse:
    if not settings.has_insightface_colab_config:
        raise RuntimeError("InsightFace Colab is not configured. Set INSIGHTFACE_COLAB_URL in the root .env and restart the API.")

    decoded = _decode_image_data_url(image_data_url)
    if not decoded:
        raise ValueError("Invalid image data URL.")

    raw_bytes, extension = decoded
    payload = {
        "image_base64": image_data_url.split(",", 1)[1],
        "image_extension": extension,
    }
    request = Request(
        settings.insightface_colab_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {settings.insightface_colab_token}"} if settings.insightface_colab_token else {}),
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=settings.insightface_timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"InsightFace Colab request failed with {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach InsightFace Colab endpoint: {exc.reason}") from exc

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("InsightFace Colab returned invalid JSON.") from exc

    embedding = payload.get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise RuntimeError("InsightFace Colab did not return an embedding.")

    try:
        normalized_embedding = [float(value) for value in embedding]
    except (TypeError, ValueError) as exc:
        raise RuntimeError("InsightFace Colab returned a non-numeric embedding.") from exc

    return InsightFaceColabResponse(
        embedding=normalized_embedding,
        face_detected=bool(payload.get("face_detected", True)),
        bbox=payload.get("bbox"),
        confidence=float(payload["confidence"]) if payload.get("confidence") is not None else None,
    )


async def request_insightface_embedding(image_data_url: str) -> InsightFaceColabResponse:
    return await asyncio.to_thread(_post_to_colab, image_data_url)
