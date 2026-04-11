from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from app.sample_images import delete_identity_sample_dir, save_detection_image
from app.schemas.detection_log import (
    CreateDetectionLogRequest,
    CreateDetectionLogResponse,
    DetectionLogActionResponse,
    DetectionLogDetail,
    DetectionLogIdentitySummary,
    DetectionLogSummary,
    MergeDetectionLogIdentityRequest,
    PromoteDetectionLogRequest,
    UpdateDetectionLogRequest,
)
from app.supabase import (
    count_embeddings_for_identity,
    create_detection_log,
    create_embedding_record,
    create_unknown_identity_for_detection,
    delete_identity,
    find_recent_duplicate_detection_log,
    get_detection_log_by_id,
    get_embedding_signature,
    get_identity_by_id,
    list_detection_logs,
    move_detection_log_identity_links,
    promote_embedding_reference,
    reassign_detection_log_identity,
    set_profile_sample,
    update_detection_log,
    update_identity,
)


router = APIRouter(prefix="/detection-logs", tags=["detection-logs"])


def _identity_summary(identity: dict | None) -> DetectionLogIdentitySummary | None:
    if not identity:
        return None

    return DetectionLogIdentitySummary(
        id=identity["id"],
        display_name=identity.get("display_name", "Unknown"),
        identity_type=identity.get("identity_type", "visitor"),
        status=identity.get("status", "active"),
    )


async def _build_detection_log_detail(item: dict) -> DetectionLogDetail:
    current_identity = await get_identity_by_id(item["current_identity_id"]) if item.get("current_identity_id") else None
    auto_identity = await get_identity_by_id(item["auto_identity_id"]) if item.get("auto_identity_id") else None
    return DetectionLogDetail(
        id=item["id"],
        source=item.get("source", "live-feed"),
        camera_id=item.get("camera_id"),
        image_path=item.get("image_path"),
        auto_similarity=item.get("auto_similarity"),
        auto_display_name=item.get("auto_display_name"),
        auto_tagged=bool(item.get("auto_tagged")),
        review_status=item.get("review_status", "pending"),
        review_notes=item.get("review_notes"),
        reviewed_at=item.get("reviewed_at"),
        detected_at=item.get("detected_at"),
        current_identity=_identity_summary(current_identity),
        auto_identity=_identity_summary(auto_identity),
        promoted_embedding_id=item.get("promoted_embedding_id"),
        promoted_at=item.get("promoted_at"),
        embedding_present=bool(item.get("embedding_present")),
    )


async def _build_detection_log_summary(item: dict) -> DetectionLogSummary:
    current_identity = await get_identity_by_id(item["current_identity_id"]) if item.get("current_identity_id") else None
    auto_identity = await get_identity_by_id(item["auto_identity_id"]) if item.get("auto_identity_id") else None
    return DetectionLogSummary(
        id=item["id"],
        source=item.get("source", "live-feed"),
        camera_id=item.get("camera_id"),
        image_path=item.get("image_path"),
        auto_similarity=item.get("auto_similarity"),
        auto_tagged=bool(item.get("auto_tagged")),
        review_status=item.get("review_status", "pending"),
        detected_at=item.get("detected_at"),
        current_identity=_identity_summary(current_identity),
        auto_identity=_identity_summary(auto_identity),
        promoted_embedding_id=item.get("promoted_embedding_id"),
    )


@router.post("", response_model=CreateDetectionLogResponse)
async def create_detection_log_record(request: CreateDetectionLogRequest):
    if not request.embedding:
        raise HTTPException(status_code=400, detail="No embedding provided")

    if len(request.embedding) != 16:
        raise HTTPException(status_code=400, detail="Invalid embedding format - expected 16 values")

    auto_tagged = bool(
        request.auto_identity_id and request.auto_similarity is not None and request.auto_similarity >= 0.95
    )
    duplicate = await find_recent_duplicate_detection_log(
        source="live-feed",
        current_identity_id=request.auto_identity_id if auto_tagged else None,
        embedding_signature=None if auto_tagged else get_embedding_signature(request.embedding),
    )
    if duplicate:
        return CreateDetectionLogResponse(
            created=False,
            detection_log=await _build_detection_log_detail(duplicate),
        )

    if auto_tagged:
        current_identity_id = request.auto_identity_id
        review_status = "auto-tagged"
    else:
        unknown_identity = await create_unknown_identity_for_detection()
        if not unknown_identity:
            raise HTTPException(status_code=500, detail="Failed to create unknown identity placeholder")
        current_identity_id = unknown_identity["id"]
        review_status = "pending"

    created = await create_detection_log(
        source="live-feed",
        camera_id=request.camera_id,
        image_path=None,
        embedding=request.embedding,
        auto_similarity=request.auto_similarity,
        auto_identity_id=request.auto_identity_id,
        auto_display_name=request.auto_display_name,
        current_identity_id=current_identity_id,
        review_status=review_status,
    )
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create detection log")

    image_path = save_detection_image(created["id"], request.image_data_url)
    if image_path:
        created = await update_detection_log(created["id"], image_path=image_path)
        if not created:
            raise HTTPException(status_code=500, detail="Failed to update detection log image")

    return CreateDetectionLogResponse(created=True, detection_log=await _build_detection_log_detail(created))


@router.get("", response_model=list[DetectionLogSummary])
async def get_detection_log_records():
    items = await list_detection_logs()
    return [await _build_detection_log_summary(item) for item in items]


@router.get("/{detection_log_id}", response_model=DetectionLogDetail)
async def get_detection_log_record(detection_log_id: str):
    item = await get_detection_log_by_id(detection_log_id)
    if not item:
        raise HTTPException(status_code=404, detail="Detection log not found")
    return await _build_detection_log_detail(item)


@router.patch("/{detection_log_id}", response_model=DetectionLogDetail)
async def update_detection_log_record(detection_log_id: str, request: UpdateDetectionLogRequest):
    detection_log = await get_detection_log_by_id(detection_log_id)
    if not detection_log:
        raise HTTPException(status_code=404, detail="Detection log not found")

    if request.display_name is not None or request.identity_type is not None or request.status is not None:
        current_identity = await get_identity_by_id(detection_log["current_identity_id"])
        if not current_identity:
            raise HTTPException(status_code=404, detail="Current identity not found")

        updated_identity = await update_identity(
            current_identity["id"],
            display_name=request.display_name or current_identity.get("display_name", "Unknown"),
            identity_type=request.identity_type or current_identity.get("identity_type", "unknown"),
            status=request.status or current_identity.get("status", "pending_review"),
            notes=current_identity.get("notes"),
            review_source=current_identity.get("review_source"),
            merged_into_identity_id=current_identity.get("merged_into_identity_id"),
        )
        if not updated_identity:
            raise HTTPException(status_code=500, detail="Failed to update linked identity")

    updated = await update_detection_log(
        detection_log_id,
        review_status=request.review_status,
        review_notes=request.review_notes,
        reviewed_at=datetime.now(UTC).isoformat() if request.review_status is not None or request.review_notes is not None else None,
    )
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update detection log")

    return await _build_detection_log_detail(updated)


@router.post("/{detection_log_id}/merge-identity", response_model=DetectionLogActionResponse)
async def merge_detection_log_identity(detection_log_id: str, request: MergeDetectionLogIdentityRequest):
    detection_log = await get_detection_log_by_id(detection_log_id)
    if not detection_log:
        raise HTTPException(status_code=404, detail="Detection log not found")

    current_identity_id = detection_log.get("current_identity_id")
    if not current_identity_id:
        raise HTTPException(status_code=400, detail="Detection log does not have a current identity")

    target_identity = await get_identity_by_id(request.target_identity_id)
    if not target_identity:
        raise HTTPException(status_code=404, detail="Target identity not found")

    if current_identity_id != request.target_identity_id:
        moved = await move_detection_log_identity_links(current_identity_id, request.target_identity_id)
        if not moved:
            raise HTTPException(status_code=500, detail="Failed to move unknown identity data to target identity")

        reassigned = await reassign_detection_log_identity(detection_log_id, request.target_identity_id)
        if not reassigned:
            raise HTTPException(status_code=500, detail="Failed to reassign detection log to target identity")

        deleted = await delete_identity(current_identity_id)
        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to remove merged placeholder identity")

        delete_identity_sample_dir(current_identity_id)

    return DetectionLogActionResponse(
        ok=True,
        detection_log_id=detection_log_id,
        message=f"Merged review identity into {target_identity.get('display_name', 'target identity')}",
    )


@router.post("/{detection_log_id}/promote-sample", response_model=DetectionLogActionResponse)
async def promote_detection_log_sample(detection_log_id: str, request: PromoteDetectionLogRequest):
    detection_log = await get_detection_log_by_id(detection_log_id)
    if not detection_log:
        raise HTTPException(status_code=404, detail="Detection log not found")

    if not detection_log.get("embedding_present") or not detection_log.get("embedding"):
        raise HTTPException(status_code=400, detail="Detection log does not have an embedding to promote")

    target_identity_id = request.target_identity_id or detection_log.get("current_identity_id")
    if not target_identity_id:
        raise HTTPException(status_code=400, detail="No target identity selected")

    target_identity = await get_identity_by_id(target_identity_id)
    if not target_identity:
        raise HTTPException(status_code=404, detail="Target identity not found")

    created_embedding = await create_embedding_record(
        target_identity_id,
        detection_log["embedding"],
        {
            "source": request.capture_source,
            "source_confidence": detection_log.get("auto_similarity"),
            "detection_log_id": detection_log_id,
        },
        sample_kind=request.sample_kind,
        image_path=detection_log.get("image_path"),
        capture_source=request.capture_source,
        capture_confidence=detection_log.get("auto_similarity"),
    )
    if not created_embedding:
        raise HTTPException(status_code=500, detail="Failed to promote detection log into an embedding")

    if request.set_as_reference:
        promoted = await promote_embedding_reference(target_identity_id, created_embedding["id"])
        if not promoted:
            raise HTTPException(status_code=500, detail="Embedding created but failed to mark as reference")

    if request.set_as_profile:
        profiled = await set_profile_sample(target_identity_id, created_embedding["id"])
        if not profiled:
            raise HTTPException(status_code=500, detail="Embedding created but failed to mark as profile sample")

    updated = await update_detection_log(
        detection_log_id,
        current_identity_id=target_identity_id,
        promoted_embedding_id=created_embedding["id"],
        promoted_at=datetime.now(UTC).isoformat(),
        review_status="resolved",
        reviewed_at=datetime.now(UTC).isoformat(),
    )
    if not updated:
        raise HTTPException(status_code=500, detail="Embedding created but detection log update failed")

    message = f"Promoted log frame into {target_identity.get('display_name', 'selected identity')}"
    if await count_embeddings_for_identity(target_identity_id) == 1:
        message = f"{message} as the first stored sample."

    return DetectionLogActionResponse(
        ok=True,
        detection_log_id=detection_log_id,
        message=message,
    )
