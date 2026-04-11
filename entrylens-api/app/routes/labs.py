from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.auth import verify_api_key
from app.services.labs import (
    get_lab_state,
    resolve_lab_file,
    run_playground_command,
    save_enrollment_images,
    save_probe_image,
)

router = APIRouter(tags=["labs"])


@router.get("", dependencies=[Depends(verify_api_key)])
async def lab_state(target: str = "mediapipe") -> dict:
    return get_lab_state(target=target)


@router.get("/files", dependencies=[Depends(verify_api_key)])
async def lab_file(target: str, file_path: str) -> FileResponse:
    return FileResponse(resolve_lab_file(target, file_path))


@router.post("/enroll-images", dependencies=[Depends(verify_api_key)])
async def upload_enroll_images(
    person_name: Annotated[str, Form()],
    files: Annotated[list[UploadFile], File()],
    target: Annotated[str, Form()] = "local-recognition",
) -> dict:
    return await save_enrollment_images(target, person_name, files)


@router.post("/probe-image", dependencies=[Depends(verify_api_key)])
async def upload_probe_image(
    file: Annotated[UploadFile, File()],
    probe_name: Annotated[str | None, Form()] = None,
    target: Annotated[str, Form()] = "mediapipe",
) -> dict:
    return await save_probe_image(target, file, probe_name)


@router.post("/commands/{command}", dependencies=[Depends(verify_api_key)])
async def execute_playground_command(
    command: str,
    target: str = "mediapipe",
    file_path: str | None = None,
    person_name: str | None = None,
) -> dict:
    try:
        return await run_playground_command(target, command, file_path=file_path, person_name=person_name)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vision lab command failed before execution: {exc}",
        ) from exc
