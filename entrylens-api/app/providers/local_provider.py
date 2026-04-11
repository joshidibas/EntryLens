import io
import uuid
from typing import Optional

import numpy as np
from PIL import Image

from app.providers.base import FaceProvider
from app.providers.schemas import EnrollResponse, ProviderResponse
from app.supabase import (
    SupabaseClient,
    create_identity,
    delete_identity,
    get_identity_by_id,
    store_embedding,
    search_similar_embeddings,
)


class LocalProvider(FaceProvider):
    """Supabase-backed local recognition provider.
    
    Uses MediaPipe for face detection and embedding extraction.
    Stores embeddings in Supabase with pgvector for similarity search.
    """

    async def identify(self, image_bytes: bytes) -> ProviderResponse:
        """Identify a face by searching Supabase embeddings."""
        client = SupabaseClient.get_client()
        if not client:
            return ProviderResponse(subject_id=None, similarity=0.0, bbox=None)

        try:
            embedding = await self._extract_embedding(image_bytes)
            if not embedding:
                return ProviderResponse(subject_id=None, similarity=0.0, bbox=None)

            results = await search_similar_embeddings(embedding, limit=1)
            if not results:
                return ProviderResponse(subject_id=None, similarity=0.0, bbox=None)

            best_match = results[0]
            return ProviderResponse(
                subject_id=best_match.get("identity_id"),
                similarity=best_match.get("similarity", 0.0),
                bbox=None
            )
        except Exception as e:
            print(f"Identify error: {e}")
            return ProviderResponse(subject_id=None, similarity=0.0, bbox=None)

    async def enroll(self, user_id: str, images: list[bytes]) -> EnrollResponse:
        """Enroll a new user with face images."""
        client = SupabaseClient.get_client()
        if not client:
            return EnrollResponse(enrolled=False, face_count=0, subject_id=user_id)

        if not images:
            return EnrollResponse(enrolled=False, face_count=0, subject_id=user_id)

        try:
            subject_id = str(uuid.uuid4())
            
            stored_count = 0
            for image_bytes in images:
                embedding = await self._extract_embedding(image_bytes)
                if embedding:
                    await store_embedding(
                        identity_id=subject_id,
                        embedding=embedding,
                        metadata={"user_id": user_id}
                    )
                    stored_count += 1

            return EnrollResponse(
                enrolled=stored_count > 0,
                face_count=stored_count,
                subject_id=subject_id
            )
        except Exception as e:
            print(f"Enroll error: {e}")
            return EnrollResponse(enrolled=False, face_count=len(images), subject_id=user_id)

    async def delete_subject(self, subject_id: str) -> bool:
        """Delete identity from Supabase."""
        try:
            return await delete_identity(subject_id)
        except Exception as e:
            print(f"Delete subject error: {e}")
            return False

    async def _extract_embedding(self, image_bytes: bytes) -> Optional[list[float]]:
        """Extract face embedding from image bytes using MediaPipe.
        
        This is a placeholder - real implementation requires MediaPipe
        running server-side or using a local ML model.
        """
        return None