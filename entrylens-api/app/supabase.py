from typing import Any, Optional
from supabase import create_client, Client
from app.config import get_settings

settings = get_settings()


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
                settings.supabase_service_key
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
                "match_limit": limit
            }
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
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Failed to get identity: {e}")
        return None


async def create_identity(name: str, role: str, provider_subject_id: Optional[str] = None) -> Optional[dict[str, Any]]:
    """Create a new identity in Supabase."""
    client = SupabaseClient.get_client()
    if not client:
        return None
    
    try:
        data = {
            "name": name,
            "role": role,
        }
        if provider_subject_id:
            data["provider_subject_id"] = provider_subject_id
        
        response = client.table("identities").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Failed to create identity: {e}")
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