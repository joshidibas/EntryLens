from datetime import UTC, datetime, timedelta
from typing import Any, Optional

from supabase import Client, create_client

from app.config import get_settings

settings = get_settings()


def _identity_payload(identity: dict[str, Any]) -> dict[str, Any]:
    return {
        **identity,
        "display_name": identity.get("display_name") or identity.get("name") or "Unknown",
        "identity_type": identity.get("identity_type") or identity.get("role") or "visitor",
        "status": identity.get("status") or "active",
        "notes": identity.get("notes"),
        "review_source": identity.get("review_source"),
        "merged_into_identity_id": identity.get("merged_into_identity_id"),
    }


def _sample_payload(sample: dict[str, Any]) -> dict[str, Any]:
    metadata = sample.get("metadata") or {}
    return {
        **sample,
        "sample_kind": sample.get("sample_kind") or "face",
        "image_path": sample.get("image_path"),
        "capture_source": sample.get("capture_source") or metadata.get("source"),
        "capture_confidence": sample.get("capture_confidence", metadata.get("source_confidence")),
        "is_reference": bool(sample.get("is_reference") or metadata.get("is_reference")),
        "is_profile_source": bool(sample.get("is_profile_source") or metadata.get("is_profile_source")),
    }


class SupabaseClient:
    """Supabase client wrapper for database and embedding operations."""

    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Optional[Client]:
        """Get Supabase client instance if configured."""
        if not settings.has_supabase_config:
            return None

        if cls._instance is None:
            cls._instance = create_client(
                settings.supabase_url,
                settings.supabase_service_key,
            )
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset client instance (useful for testing)."""
        cls._instance = None


async def get_supabase() -> Optional[Client]:
    """Dependency for getting Supabase client."""
    return SupabaseClient.get_client()


async def store_embedding(identity_id: str, embedding: list[float], metadata: Optional[dict[str, Any]] = None) -> bool:
    """Store embedding in Supabase (using pgvector)."""
    client = SupabaseClient.get_client()
    if not client:
        return False

    try:
        data = {
            "identity_id": identity_id,
            "embedding": embedding,
        }
        if metadata:
            data["metadata"] = metadata

        client.table("embeddings").insert(data).execute()
        return True
    except Exception as e:
        print(f"Failed to store embedding: {e}")
        return False


async def search_similar_embeddings(embedding: list[float], limit: int = 5) -> list[dict[str, Any]]:
    """Search for similar embeddings using vector similarity."""
    client = SupabaseClient.get_client()
    if not client:
        return []

    try:
        response = client.rpc(
            "match_embeddings",
            {
                "query_embedding": embedding,
                "match_limit": limit,
            },
        ).execute()
        return response.data or []
    except Exception as e:
        print(f"Failed to search embeddings: {e}")
        return []


async def get_identity_by_id(identity_id: str) -> Optional[dict[str, Any]]:
    """Get identity by ID from Supabase."""
    client = SupabaseClient.get_client()
    if not client:
        return None

    try:
        response = client.table("identities").select("*").eq("id", identity_id).execute()
        return _identity_payload(response.data[0]) if response.data else None
    except Exception as e:
        print(f"Failed to get identity: {e}")
        return None


async def list_identities() -> list[dict[str, Any]]:
    """List identities from Supabase."""
    client = SupabaseClient.get_client()
    if not client:
        return []

    try:
        response = client.table("identities").select("*").order("display_name").execute()
        return [_identity_payload(item) for item in (response.data or [])]
    except Exception as e:
        print(f"Failed to list identities: {e}")
        return []


async def update_identity(
    identity_id: str,
    *,
    display_name: str,
    identity_type: str,
    status: str,
    notes: str | None,
    review_source: str | None = None,
    merged_into_identity_id: str | None = None,
) -> Optional[dict[str, Any]]:
    """Update a single identity using the migrated CRUD columns."""
    client = SupabaseClient.get_client()
    if not client:
        return None

    try:
        payload = {
            "display_name": display_name,
            "identity_type": identity_type,
            "status": status,
            "notes": notes,
            "name": display_name,
            "role": identity_type,
        }
        if review_source is not None:
            payload["review_source"] = review_source
        if merged_into_identity_id is not None:
            payload["merged_into_identity_id"] = merged_into_identity_id
        response = client.table("identities").update(payload).eq("id", identity_id).execute()
        return _identity_payload(response.data[0]) if response.data else None
    except Exception as e:
        print(f"Failed to update identity: {e}")
        return None


async def count_embeddings_for_identity(identity_id: str) -> int:
    """Count how many embeddings belong to an identity."""
    client = SupabaseClient.get_client()
    if not client:
        return 0

    try:
        response = client.table("embeddings").select("id", count="exact").eq("identity_id", identity_id).execute()
        return response.count or 0
    except Exception as e:
        print(f"Failed to count embeddings: {e}")
        return 0


async def list_embeddings_for_identity(identity_id: str) -> list[dict[str, Any]]:
    """List stored embeddings for a given identity."""
    client = SupabaseClient.get_client()
    if not client:
        return []

    try:
        response = client.table("embeddings").select(
            "id, created_at, updated_at, sample_kind, image_path, capture_source, capture_confidence, is_reference, is_profile_source, metadata"
        ).eq("identity_id", identity_id).order("created_at", desc=True).execute()
        return [_sample_payload(item) for item in (response.data or [])]
    except Exception as e:
        print(f"Failed to list embeddings: {e}")
        return []


async def get_profile_sample_id_for_identity(identity_id: str) -> Optional[str]:
    """Return the embedding/sample currently marked as the profile source."""
    identity = await get_identity_by_id(identity_id)
    if identity and identity.get("profile_sample_id"):
        return identity["profile_sample_id"]

    embeddings = await list_embeddings_for_identity(identity_id)
    for embedding in embeddings:
        if embedding.get("is_profile_source"):
            return embedding["id"]
    return None


async def get_embedding_by_id(embedding_id: str) -> Optional[dict[str, Any]]:
    """Get a single embedding row by ID."""
    client = SupabaseClient.get_client()
    if not client:
        return None

    try:
        response = client.table("embeddings").select("*").eq("id", embedding_id).execute()
        return _sample_payload(response.data[0]) if response.data else None
    except Exception as e:
        print(f"Failed to get embedding: {e}")
        return None


async def update_embedding_metadata(embedding_id: str, metadata: dict[str, Any]) -> bool:
    """Replace metadata for a single embedding row."""
    client = SupabaseClient.get_client()
    if not client:
        return False

    try:
        client.table("embeddings").update({"metadata": metadata}).eq("id", embedding_id).execute()
        return True
    except Exception as e:
        print(f"Failed to update embedding metadata: {e}")
        return False


async def update_embedding_flags(embedding_id: str, *, is_reference: bool | None = None, is_profile_source: bool | None = None) -> bool:
    """Update first-class sample flags."""
    client = SupabaseClient.get_client()
    if not client:
        return False

    updates: dict[str, Any] = {}
    if is_reference is not None:
        updates["is_reference"] = is_reference
    if is_profile_source is not None:
        updates["is_profile_source"] = is_profile_source
    if not updates:
        return True

    try:
        client.table("embeddings").update(updates).eq("id", embedding_id).execute()
        return True
    except Exception as e:
        print(f"Failed to update embedding flags: {e}")
        return False


async def delete_embedding(embedding_id: str) -> bool:
    """Delete a single embedding row."""
    client = SupabaseClient.get_client()
    if not client:
        return False

    try:
        client.table("embeddings").delete().eq("id", embedding_id).execute()
        return True
    except Exception as e:
        print(f"Failed to delete embedding: {e}")
        return False


async def promote_embedding_reference(identity_id: str, embedding_id: str) -> bool:
    """Mark one embedding as the preferred reference sample for an identity."""
    embeddings = await list_embeddings_for_identity(identity_id)
    if not embeddings:
        return False

    updated_any = False
    for embedding in embeddings:
        current_id = embedding["id"]
        updated = await update_embedding_flags(current_id, is_reference=current_id == embedding_id)
        updated_any = updated_any or updated

    return updated_any


async def set_profile_sample(identity_id: str, embedding_id: str) -> bool:
    """Mark one embedding as the profile source for an identity."""
    embeddings = await list_embeddings_for_identity(identity_id)
    if not embeddings:
        return False

    updated_any = False
    for embedding in embeddings:
        current_id = embedding["id"]
        updated = await update_embedding_flags(current_id, is_profile_source=current_id == embedding_id)
        updated_any = updated_any or updated

    if not updated_any:
        return False

    client = SupabaseClient.get_client()
    if not client:
        return False

    try:
        client.table("identities").update({"profile_sample_id": embedding_id}).eq("id", identity_id).execute()
        return True
    except Exception as e:
        print(f"Failed to update profile sample on identity: {e}")
        return False


async def create_identity(
    display_name: str,
    identity_type: str,
    status: str = "active",
    notes: str | None = None,
    provider_subject_id: Optional[str] = None,
    review_source: str | None = None,
    merged_into_identity_id: str | None = None,
) -> Optional[dict[str, Any]]:
    """Create a new identity in Supabase."""
    client = SupabaseClient.get_client()
    if not client:
        return None

    try:
        data = {
            "display_name": display_name,
            "identity_type": identity_type,
            "status": status,
            "notes": notes,
            "name": display_name,
            "role": identity_type,
        }
        if provider_subject_id:
            data["provider_subject_id"] = provider_subject_id
        if review_source is not None:
            data["review_source"] = review_source
        if merged_into_identity_id is not None:
            data["merged_into_identity_id"] = merged_into_identity_id

        response = client.table("identities").insert(data).execute()
        return _identity_payload(response.data[0]) if response.data else None
    except Exception as e:
        print(f"Failed to create identity: {e}")
        return None


async def add_embedding_to_identity(
    identity_id: str,
    embedding: list[float],
    metadata: Optional[dict[str, Any]] = None,
    *,
    sample_kind: str = "face",
    image_path: str | None = None,
    capture_source: str | None = None,
    capture_confidence: float | None = None,
) -> bool:
    """Append a new embedding to an existing identity."""
    identity = await get_identity_by_id(identity_id)
    if not identity:
        return False

    client = SupabaseClient.get_client()
    if not client:
        return False

    try:
        payload: dict[str, Any] = {
            "identity_id": identity_id,
            "embedding": embedding,
            "sample_kind": sample_kind,
            "image_path": image_path,
            "capture_source": capture_source,
            "capture_confidence": capture_confidence,
            "metadata": metadata or {},
        }
        client.table("embeddings").insert(payload).execute()
        return True
    except Exception as e:
        print(f"Failed to add embedding to identity: {e}")
        return False


async def create_embedding_record(
    identity_id: str,
    embedding: list[float],
    metadata: Optional[dict[str, Any]] = None,
    *,
    sample_kind: str = "face",
    image_path: str | None = None,
    capture_source: str | None = None,
    capture_confidence: float | None = None,
    is_reference: bool = False,
    is_profile_source: bool = False,
) -> Optional[dict[str, Any]]:
    """Create and return a single embedding/sample row."""
    identity = await get_identity_by_id(identity_id)
    if not identity:
        return None

    client = SupabaseClient.get_client()
    if not client:
        return None

    try:
        payload: dict[str, Any] = {
            "identity_id": identity_id,
            "embedding": embedding,
            "sample_kind": sample_kind,
            "image_path": image_path,
            "capture_source": capture_source,
            "capture_confidence": capture_confidence,
            "is_reference": is_reference,
            "is_profile_source": is_profile_source,
            "metadata": metadata or {},
        }
        response = client.table("embeddings").insert(payload).execute()
        return _sample_payload(response.data[0]) if response.data else None
    except Exception as e:
        print(f"Failed to create embedding record: {e}")
        return None


async def delete_identity(identity_id: str) -> bool:
    """Delete identity from Supabase."""
    client = SupabaseClient.get_client()
    if not client:
        return False

    try:
        client.table("identities").delete().eq("id", identity_id).execute()
        return True
    except Exception as e:
        print(f"Failed to delete identity: {e}")
        return False


def get_embedding_signature(embedding: list[float], precision: int = 3, prefix_length: int = 8) -> str:
    return "|".join(f"{value:.{precision}f}" for value in embedding[:prefix_length])


def _detection_log_payload(item: dict[str, Any]) -> dict[str, Any]:
    return {
        **item,
        "auto_tagged": bool(item.get("auto_tagged")),
        "embedding_present": item.get("embedding") is not None,
    }


async def create_unknown_identity_for_detection() -> Optional[dict[str, Any]]:
    label = f"Unknown {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}"
    return await create_identity(
        display_name=label,
        identity_type="unknown",
        status="pending_review",
        notes="Created automatically from live detection.",
        review_source="live-detection",
    )


async def find_recent_duplicate_detection_log(
    *,
    source: str,
    current_identity_id: str | None = None,
    embedding_signature: str | None = None,
    window_seconds: int = 15,
) -> Optional[dict[str, Any]]:
    client = SupabaseClient.get_client()
    if not client:
        return None

    try:
        since = (datetime.now(UTC) - timedelta(seconds=window_seconds)).isoformat()
        query = client.table("detection_logs").select("*").eq("source", source).gte("detected_at", since)
        if current_identity_id:
            query = query.eq("current_identity_id", current_identity_id)
        elif embedding_signature:
            query = query.eq("embedding_signature", embedding_signature).eq("auto_tagged", False)
        else:
            return None
        response = query.order("detected_at", desc=True).limit(1).execute()
        return _detection_log_payload(response.data[0]) if response.data else None
    except Exception as e:
        print(f"Failed to look up duplicate detection log: {e}")
        return None


async def create_detection_log(
    *,
    source: str,
    camera_id: str | None,
    image_path: str | None,
    embedding: list[float],
    auto_similarity: float | None,
    auto_identity_id: str | None,
    auto_display_name: str | None,
    current_identity_id: str,
    review_status: str,
) -> Optional[dict[str, Any]]:
    client = SupabaseClient.get_client()
    if not client:
        return None

    try:
        payload = {
            "source": source,
            "camera_id": camera_id,
            "image_path": image_path,
            "embedding": embedding,
            "embedding_signature": get_embedding_signature(embedding),
            "auto_similarity": auto_similarity,
            "auto_identity_id": auto_identity_id,
            "auto_display_name": auto_display_name,
            "auto_tagged": bool(auto_identity_id and auto_similarity is not None and auto_similarity >= 0.95),
            "current_identity_id": current_identity_id,
            "review_status": review_status,
        }
        response = client.table("detection_logs").insert(payload).execute()
        return _detection_log_payload(response.data[0]) if response.data else None
    except Exception as e:
        print(f"Failed to create detection log: {e}")
        return None


async def list_detection_logs(limit: int = 100) -> list[dict[str, Any]]:
    client = SupabaseClient.get_client()
    if not client:
        return []

    try:
        response = client.table("detection_logs").select("*").order("detected_at", desc=True).limit(limit).execute()
        return [_detection_log_payload(item) for item in (response.data or [])]
    except Exception as e:
        print(f"Failed to list detection logs: {e}")
        return []


async def get_detection_log_by_id(detection_log_id: str) -> Optional[dict[str, Any]]:
    client = SupabaseClient.get_client()
    if not client:
        return None

    try:
        response = client.table("detection_logs").select("*").eq("id", detection_log_id).execute()
        return _detection_log_payload(response.data[0]) if response.data else None
    except Exception as e:
        print(f"Failed to get detection log: {e}")
        return None


async def update_detection_log(
    detection_log_id: str,
    *,
    image_path: str | None = None,
    review_status: str | None = None,
    review_notes: str | None = None,
    current_identity_id: str | None = None,
    promoted_embedding_id: str | None = None,
    promoted_at: str | None = None,
    reviewed_at: str | None = None,
) -> Optional[dict[str, Any]]:
    client = SupabaseClient.get_client()
    if not client:
        return None

    updates: dict[str, Any] = {}
    if image_path is not None:
        updates["image_path"] = image_path
    if review_status is not None:
        updates["review_status"] = review_status
    if review_notes is not None:
        updates["review_notes"] = review_notes
    if current_identity_id is not None:
        updates["current_identity_id"] = current_identity_id
    if promoted_embedding_id is not None:
        updates["promoted_embedding_id"] = promoted_embedding_id
    if promoted_at is not None:
        updates["promoted_at"] = promoted_at
    if reviewed_at is not None:
        updates["reviewed_at"] = reviewed_at
    if not updates:
        return await get_detection_log_by_id(detection_log_id)

    try:
        response = client.table("detection_logs").update(updates).eq("id", detection_log_id).execute()
        return _detection_log_payload(response.data[0]) if response.data else None
    except Exception as e:
        print(f"Failed to update detection log: {e}")
        return None


async def move_detection_log_identity_links(from_identity_id: str, to_identity_id: str) -> bool:
    client = SupabaseClient.get_client()
    if not client:
        return False

    try:
        client.table("detection_logs").update({"current_identity_id": to_identity_id}).eq("current_identity_id", from_identity_id).execute()
        client.table("embeddings").update({"identity_id": to_identity_id}).eq("identity_id", from_identity_id).execute()
        return True
    except Exception as e:
        print(f"Failed to move identity links from detection log merge: {e}")
        return False


async def reassign_detection_log_identity(detection_log_id: str, target_identity_id: str) -> Optional[dict[str, Any]]:
    client = SupabaseClient.get_client()
    if not client:
        return None

    try:
        response = client.table("detection_logs").update(
            {
                "current_identity_id": target_identity_id,
                "review_status": "resolved",
                "reviewed_at": datetime.now(UTC).isoformat(),
            }
        ).eq("id", detection_log_id).execute()
        return _detection_log_payload(response.data[0]) if response.data else None
    except Exception as e:
        print(f"Failed to reassign detection log identity: {e}")
        return None
