import asyncio
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status

from app.services.model_registry import get_registered_models


REPO_ROOT = Path(__file__).resolve().parents[3]
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _local_recognition_models() -> list[dict[str, Any]]:
    return [
        {
            "id": model.id,
            "label": model.label,
            "description": model.description,
            "input_mode": model.input_mode,
            "enabled": model.enabled,
            "status": model.status,
            "health": model.health,
            "unavailable_reason": model.unavailable_reason,
        }
        for model in get_registered_models()
    ]

PLAYGROUND_TARGETS: dict[str, dict[str, Any]] = {
    "mediapipe": {
        "label": "MediaPipe",
        "description": "Local browser-side face detection and landmark playground.",
        "operation": "detect",
        "engine_kind": "local",
        "models": [
            {
                "id": "face-landmarker",
                "label": "Face Landmarker",
                "description": "Browser-side landmarks, face presence, and pose gating.",
            }
        ],
        "root": REPO_ROOT / "playgrounds" / "mediapipe-playground",
        "enroll_root": None,
        "probe_root": REPO_ROOT / "playgrounds" / "mediapipe-playground" / "test-data" / "input",
        "output_root": REPO_ROOT / "playgrounds" / "mediapipe-playground" / "output",
        "command_script": None,
        "allowed_commands": set(),
        "supports_enroll_upload": False,
        "supports_probe_upload": True,
        "requires_group_id": False,
        "artifacts_subdir": None,
    },
    "local-recognition": {
        "label": "Local Recognition",
        "description": "Local enrollment and recognition flow backed by MediaPipe embeddings and Supabase storage.",
        "operation": "recognize",
        "engine_kind": "local",
        "models": _local_recognition_models(),
        "root": REPO_ROOT,
        "enroll_root": None,
        "probe_root": None,
        "output_root": REPO_ROOT,
        "command_script": None,
        "allowed_commands": set(),
        "supports_enroll_upload": False,
        "supports_probe_upload": False,
        "requires_group_id": False,
        "artifacts_subdir": None,
        "status": "ready",
    },
}


def _get_target_config(target: str) -> dict[str, Any]:
    config = PLAYGROUND_TARGETS.get(target)
    if not config:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported playground target.")
    return config


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _safe_slug(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-_").lower()
    return slug or fallback


def _validate_image_name(filename: str | None) -> str:
    if not filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing file name.")

    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image type: {extension or 'unknown'}.",
        )

    stem = _safe_slug(Path(filename).stem, "image")
    return f"{stem}{extension}"


def _sorted_relative_files(root: Path | None, playground_root: Path) -> list[str]:
    if root is None or not root.exists():
        return []

    files = [path for path in root.rglob("*") if path.is_file() and path.name != ".gitkeep"]
    return [str(path.relative_to(playground_root)).replace("\\", "/") for path in sorted(files)]


def _load_latest_artifacts(output_root: Path, limit: int = 10, artifacts_subdir: str | None = None) -> list[dict[str, Any]]:
    artifacts_root = output_root / artifacts_subdir if artifacts_subdir else output_root
    if not artifacts_root.exists():
        return []

    files = sorted(
        [path for path in artifacts_root.rglob("*.json") if path.name != "state.json"],
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )[:limit]

    artifacts: list[dict[str, Any]] = []
    for file in files:
        try:
            payload = json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {"error": "Invalid JSON artifact."}

        artifacts.append(
            {
                "name": file.name,
                "relative_path": str(file.relative_to(artifacts_root)).replace("\\", "/"),
                "modified_at": file.stat().st_mtime,
                "payload": payload,
            }
        )
    return artifacts


def _load_state(output_root: Path) -> dict[str, Any] | None:
    state_path = output_root / "state.json"
    if not state_path.exists():
        return None

    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"error": "Invalid state file."}


def _credential_state(requires_group_id: bool) -> dict[str, bool]:
    return {
        "has_api_key": False,
        "has_endpoint": False,
        "has_group_id": False,
        "requires_group_id": requires_group_id,
    }


def _target_summaries() -> list[dict[str, Any]]:
    return [
        {
            "id": target_id,
            "label": config["label"],
            "description": config["description"],
            "status": config.get("status", "ready"),
            "operation": config["operation"],
            "engine_kind": config["engine_kind"],
            "models": _local_recognition_models() if target_id == "local-recognition" else config.get("models", []),
            "supports_enroll_upload": config["supports_enroll_upload"],
            "supports_probe_upload": config["supports_probe_upload"],
        }
        for target_id, config in PLAYGROUND_TARGETS.items()
    ]


async def save_enrollment_images(target: str, person_name: str, files: list[UploadFile]) -> dict[str, Any]:
    config = _get_target_config(target)
    target_dir_root = config["enroll_root"]
    playground_root = config["root"]

    if not config["supports_enroll_upload"] or target_dir_root is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The selected playground does not accept enrollment uploads.",
        )
    if not person_name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Person name is required.")
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one image is required.")

    person_slug = _safe_slug(person_name, "person")
    target_dir = target_dir_root / person_slug
    _ensure_dir(target_dir)

    saved_files: list[str] = []
    for file in files:
        target_name = _validate_image_name(file.filename)
        payload = await file.read()
        if not payload:
            continue
        target_path = target_dir / target_name
        target_path.write_bytes(payload)
        saved_files.append(str(target_path.relative_to(playground_root)).replace("\\", "/"))

    if not saved_files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No non-empty images were uploaded.")

    return {"target": target, "person": person_slug, "saved_files": saved_files}


async def save_probe_image(target: str, file: UploadFile, probe_name: str | None = None) -> dict[str, Any]:
    config = _get_target_config(target)
    probe_root = config["probe_root"]
    playground_root = config["root"]

    if not config["supports_probe_upload"] or probe_root is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The selected playground does not accept probe uploads.",
        )

    _ensure_dir(probe_root)
    target_name = _validate_image_name(probe_name or file.filename)
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded image was empty.")

    target_path = probe_root / target_name
    target_path.write_bytes(payload)
    relative_path = str(target_path.relative_to(playground_root)).replace("\\", "/")
    return {"target": target, "probe_file": relative_path}


def get_lab_state(*, target: str) -> dict[str, Any]:
    config = _get_target_config(target)

    return {
        "selected_target": target,
        "target_status": config.get("status", "ready"),
        "targets": _target_summaries(),
        "credentials": _credential_state(config["requires_group_id"]),
        "enroll_files": _sorted_relative_files(config["enroll_root"], config["root"]),
        "probe_files": _sorted_relative_files(config["probe_root"], config["root"]),
        "state": _load_state(config["output_root"]),
        "artifacts": _load_latest_artifacts(
            config["output_root"],
            artifacts_subdir=config["artifacts_subdir"],
        ),
    }


def resolve_lab_file(target: str, file_path: str) -> Path:
    config = _get_target_config(target)
    root = config["root"].resolve()
    requested = (root / file_path).resolve()

    try:
        requested.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File path is outside the selected playground.") from exc

    if not requested.exists() or not requested.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requested playground file was not found.")

    return requested


async def run_playground_command(
    target: str,
    command: str,
    *,
    file_path: str | None = None,
    person_name: str | None = None,
) -> dict[str, Any]:
    config = _get_target_config(target)

    if config.get("status") == "planned":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The selected playground is planned but not implemented yet.",
        )

    if command not in config["allowed_commands"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported playground command.")

    cmd = ["npm.cmd", "run", config["command_script"], "--", command]
    if file_path:
        cmd.extend(["--file", file_path])
    if person_name:
        cmd.extend(["--person", person_name])

    command_line = subprocess.list2cmdline(cmd)
    process = await asyncio.create_subprocess_shell(
        command_line,
        cwd=str(REPO_ROOT),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=os.environ.copy(),
    )
    stdout, stderr = await process.communicate()

    stdout_text = stdout.decode("utf-8", errors="replace")
    stderr_text = stderr.decode("utf-8", errors="replace")

    return {
        "target": target,
        "command": command,
        "file_path": file_path,
        "person_name": person_name,
        "exit_code": process.returncode,
        "stdout": stdout_text,
        "stderr": stderr_text,
        "ok": process.returncode == 0,
    }
