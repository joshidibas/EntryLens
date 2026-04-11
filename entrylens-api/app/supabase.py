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
