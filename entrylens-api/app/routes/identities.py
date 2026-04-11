import mimetypes

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.sample_images import delete_identity_sample_dir, delete_sample_image, resolve_sample_image_path, save_sample_image
from app.schemas.identity import (
    AddIdentitySampleRequest,
    AddIdentitySampleResponse,
    CreateIdentityRequest,
    IdentityDetail,
    IdentitySampleActionResponse,
    IdentitySampleSummary,
    IdentitySummary,
    UpdateIdentityRequest,
)
from app.supabase import (
    add_embedding_to_identity,
    count_embeddings_for_identity,
    create_identity,
    delete_embedding,
    delete_identity,
    get_embedding_by_id,
    get_identity_by_id,
    get_profile_sample_id_for_identity,
    list_embeddings_for_identity,
    list_identities,
    promote_embedding_reference,
    set_profile_sample,
    update_identity,
)

router = APIRouter(prefix="/identities", tags=["identities"])


@router.get("", response_model=list[IdentitySummary])
async def get_identities():
    identities = await list_identities()
    items: list[IdentitySummary] = []
    for identity in identities:
        profile_sample_id = await get_profile_sample_id_for_identity(identity["id"])
        items.append(
            IdentitySummary(
                id=identity["id"],
                display_name=identity.get("display_name", "Unknown"),
                identity_type=identity.get("identity_type", "visitor"),
                status=identity.get("status", "active"),
                notes=identity.get("notes"),
                created_at=identity.get("created_at"),
                updated_at=identity.get("updated_at"),
                embedding_count=await count_embeddings_for_identity(identity["id"]),
                profile_sample_id=profile_sample_id,
            )
        )
    return items


@router.post("", response_model=IdentityDetail)
async def create_identity_record(request: CreateIdentityRequest):
    identity = await create_identity(
        display_name=request.display_name,
        identity_type=request.identity_type,
        status=request.status,
        notes=request.notes,
    )
    if not identity:
        raise HTTPException(status_code=500, detail="Failed to create identity")

    return IdentityDetail(
        id=identity["id"],
        display_name=identity.get("display_name", request.display_name),
        identity_type=identity.get("identity_type", request.identity_type),
        status=identity.get("status", request.status),
        notes=identity.get("notes"),
        created_at=identity.get("created_at"),
        updated_at=identity.get("updated_at"),
        sample_count=0,
        profile_sample_id=None,
    )


@router.get("/sample-image")
async def get_identity_sample_image(image_path: str = Query(..., min_length=1)):
    resolved = resolve_sample_image_path(image_path)
    if not resolved:
        raise HTTPException(status_code=404, detail="Sample image not found")

    media_type, _ = mimetypes.guess_type(resolved.name)
    return FileResponse(resolved, media_type=media_type or "application/octet-stream")


@router.get("/{identity_id}", response_model=IdentityDetail)
async def get_identity_detail(identity_id: str):
    identity = await get_identity_by_id(identity_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    return IdentityDetail(
        id=identity["id"],
        display_name=identity.get("display_name", "Unknown"),
        identity_type=identity.get("identity_type", "visitor"),
        status=identity.get("status", "active"),
        notes=identity.get("notes"),
        created_at=identity.get("created_at"),
        updated_at=identity.get("updated_at"),
        sample_count=await count_embeddings_for_identity(identity_id),
        profile_sample_id=await get_profile_sample_id_for_identity(identity_id),
    )


@router.patch("/{identity_id}", response_model=IdentityDetail)
async def update_identity_record(identity_id: str, request: UpdateIdentityRequest):
    identity = await update_identity(
        identity_id,
        display_name=request.display_name,
        identity_type=request.identity_type,
        status=request.status,
        notes=request.notes,
    )
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found or not updated")

    return IdentityDetail(
        id=identity["id"],
        display_name=identity.get("display_name", request.display_name),
        identity_type=identity.get("identity_type", request.identity_type),
        status=identity.get("status", request.status),
        notes=identity.get("notes"),
        created_at=identity.get("created_at"),
        updated_at=identity.get("updated_at"),
        sample_count=await count_embeddings_for_identity(identity_id),
        profile_sample_id=await get_profile_sample_id_for_identity(identity_id),
    )


@router.delete("/{identity_id}", response_model=dict[str, bool | str])
async def delete_identity_record(identity_id: str):
    identity = await get_identity_by_id(identity_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    deleted = await delete_identity(identity_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete identity")

    delete_identity_sample_dir(identity_id)

    return {"ok": True, "identity_id": identity_id}


@router.get("/{identity_id}/embeddings", response_model=list[IdentitySampleSummary])
async def get_identity_embeddings(identity_id: str):
    identity = await get_identity_by_id(identity_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    embeddings = await list_embeddings_for_identity(identity_id)
    return [
        IdentitySampleSummary(
            id=item["id"],
            created_at=item.get("created_at"),
            updated_at=item.get("updated_at"),
            sample_kind=item.get("sample_kind", "face"),
            image_path=item.get("image_path"),
            capture_source=item.get("capture_source"),
            capture_confidence=item.get("capture_confidence"),
            is_reference=bool(item.get("is_reference")),
            is_profile_source=bool(item.get("is_profile_source")),
        )
        for item in embeddings
    ]


@router.post("/{identity_id}/embeddings", response_model=AddIdentitySampleResponse)
async def add_identity_embedding(identity_id: str, request: AddIdentitySampleRequest):
    if not request.embedding:
        raise HTTPException(status_code=400, detail="No embedding provided")

    if len(request.embedding) != 16:
        raise HTTPException(status_code=400, detail="Invalid embedding format - expected 16 values")

    identity = await get_identity_by_id(identity_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    metadata = {}
    if request.capture_source is not None:
        metadata["source"] = request.capture_source
    if request.capture_confidence is not None:
        metadata["source_confidence"] = request.capture_confidence

    stored_image_path = request.image_path or save_sample_image(identity_id, request.image_data_url)

    added = await add_embedding_to_identity(
        identity_id,
        request.embedding,
        metadata,
        sample_kind=request.sample_kind,
        image_path=stored_image_path,
        capture_source=request.capture_source or "unknown-review",
        capture_confidence=request.capture_confidence,
    )
    if not added:
        raise HTTPException(status_code=500, detail="Failed to store embedding")

    return AddIdentitySampleResponse(
        added=True,
        identity_id=identity_id,
        sample_count=await count_embeddings_for_identity(identity_id),
        message=f"Added a new face sample to {identity.get('display_name', 'this identity')}",
    )


@router.delete("/{identity_id}/embeddings/{embedding_id}", response_model=IdentitySampleActionResponse)
async def delete_identity_embedding(identity_id: str, embedding_id: str):
    identity = await get_identity_by_id(identity_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    embedding = await get_embedding_by_id(embedding_id)
    if not embedding or embedding.get("identity_id") != identity_id:
        raise HTTPException(status_code=404, detail="Embedding not found for this identity")

    deleted = await delete_embedding(embedding_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete embedding")

    delete_sample_image(embedding.get("image_path"))

    return IdentitySampleActionResponse(
        ok=True,
        identity_id=identity_id,
        sample_id=embedding_id,
        message="Deleted sample",
    )


@router.post("/{identity_id}/embeddings/{embedding_id}/promote", response_model=IdentitySampleActionResponse)
async def promote_identity_embedding(identity_id: str, embedding_id: str):
    identity = await get_identity_by_id(identity_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    embedding = await get_embedding_by_id(embedding_id)
    if not embedding or embedding.get("identity_id") != identity_id:
        raise HTTPException(status_code=404, detail="Embedding not found for this identity")

    promoted = await promote_embedding_reference(identity_id, embedding_id)
    if not promoted:
        raise HTTPException(status_code=500, detail="Failed to promote embedding")

    return IdentitySampleActionResponse(
        ok=True,
        identity_id=identity_id,
        sample_id=embedding_id,
        message="Promoted sample as preferred reference",
    )


@router.post("/{identity_id}/embeddings/{embedding_id}/set-profile", response_model=IdentitySampleActionResponse)
async def set_identity_profile_sample(identity_id: str, embedding_id: str):
    identity = await get_identity_by_id(identity_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    embedding = await get_embedding_by_id(embedding_id)
    if not embedding or embedding.get("identity_id") != identity_id:
        raise HTTPException(status_code=404, detail="Embedding not found for this identity")

    updated = await set_profile_sample(identity_id, embedding_id)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to set profile sample")

    return IdentitySampleActionResponse(
        ok=True,
        identity_id=identity_id,
        sample_id=embedding_id,
        message="Set sample as profile source",
    )
