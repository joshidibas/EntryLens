import base64
import binascii
import shutil
import re
import uuid
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_IMAGE_ROOT = PROJECT_ROOT / "runtime-data" / "identity-samples"
DETECTION_IMAGE_ROOT = PROJECT_ROOT / "runtime-data" / "detection-logs"

DATA_URL_PATTERN = re.compile(r"^data:(image/(?P<ext>[a-zA-Z0-9.+-]+));base64,(?P<data>.+)$")


def _decode_image_data_url(image_data_url: str | None) -> tuple[bytes, str] | None:
    if not image_data_url:
        return None

    match = DATA_URL_PATTERN.match(image_data_url)
    if not match:
        return None

    extension = match.group("ext").split("/")[-1].lower()
    if extension == "jpeg":
        extension = "jpg"
    if extension not in {"jpg", "png", "webp"}:
        extension = "jpg"

    try:
        raw_bytes = base64.b64decode(match.group("data"), validate=True)
    except (binascii.Error, ValueError):
        return None

    return raw_bytes, extension


def _save_image(root: Path, folder_name: str, image_data_url: str | None) -> str | None:
    decoded = _decode_image_data_url(image_data_url)
    if not decoded:
        return None

    raw_bytes, extension = decoded
    target_dir = root / folder_name
    target_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"{uuid.uuid4().hex}.{extension}"
    file_path = target_dir / file_name
    file_path.write_bytes(raw_bytes)

    return str(file_path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def save_sample_image(identity_id: str, image_data_url: str | None) -> str | None:
    """Persist a data-url image under the identity sample runtime folder."""
    return _save_image(SAMPLE_IMAGE_ROOT, identity_id, image_data_url)


def save_detection_image(detection_log_id: str, image_data_url: str | None) -> str | None:
    """Persist a data-url image captured for a detection log review."""
    return _save_image(DETECTION_IMAGE_ROOT, detection_log_id, image_data_url)


def resolve_sample_image_path(image_path: str | None) -> Path | None:
    """Resolve a stored relative image path to a safe local file path."""
    if not image_path:
        return None

    candidate = (PROJECT_ROOT / image_path).resolve()
    sample_root = SAMPLE_IMAGE_ROOT.resolve()
    detection_root = DETECTION_IMAGE_ROOT.resolve()

    try:
        candidate.relative_to(sample_root)
    except ValueError:
        try:
            candidate.relative_to(detection_root)
        except ValueError:
            return None

    if not candidate.is_file():
        return None

    return candidate


def delete_sample_image(image_path: str | None) -> None:
    resolved = resolve_sample_image_path(image_path)
    if not resolved:
        return

    try:
        resolved.unlink(missing_ok=True)
    except OSError:
        return

    current_dir = resolved.parent
    sample_root = SAMPLE_IMAGE_ROOT.resolve()
    while current_dir != sample_root:
        try:
            current_dir.rmdir()
        except OSError:
            break
        current_dir = current_dir.parent


def delete_identity_sample_dir(identity_id: str) -> None:
    identity_dir = (SAMPLE_IMAGE_ROOT / identity_id).resolve()
    sample_root = SAMPLE_IMAGE_ROOT.resolve()

    try:
        identity_dir.relative_to(sample_root)
    except ValueError:
        return

    if identity_dir.exists():
        shutil.rmtree(identity_dir, ignore_errors=True)


def delete_detection_image_dir(detection_log_id: str) -> None:
    detection_dir = (DETECTION_IMAGE_ROOT / detection_log_id).resolve()
    detection_root = DETECTION_IMAGE_ROOT.resolve()

    try:
        detection_dir.relative_to(detection_root)
    except ValueError:
        return

    if detection_dir.exists():
        shutil.rmtree(detection_dir, ignore_errors=True)
