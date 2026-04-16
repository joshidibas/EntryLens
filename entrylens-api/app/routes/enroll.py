import uuid
from fastapi import APIRouter, HTTPException
from app.sample_images import save_sample_image
from app.schemas.enroll import EnrollRequest, EnrollResponse
from app.services.embedding_models import resolve_embedding
from app.supabase import create_identity, add_embedding_to_identity, SupabaseClient

router = APIRouter(prefix="/enroll", tags=["enrollment"])


@router.post("", response_model=EnrollResponse)
async def enroll(request: EnrollRequest):
    client = SupabaseClient.get_client()
    if not client:
        raise HTTPException(status_code=500, detail="Supabase client not initialized. Check SUPABASE_URL and SUPABASE_SERVICE_KEY in .env")
    
    try:
        subject_id = str(uuid.uuid4())
        
        identity = await create_identity(
            display_name=request.name,
            identity_type=request.role,
            provider_subject_id=subject_id
        )
        
        if not identity:
            raise HTTPException(status_code=500, detail="Failed to create identity in Supabase. Check that 'identities' table exists and service key has proper permissions.")
        
        resolved_embedding = await resolve_embedding(
            model_id=request.model_id,
            embedding=request.embedding,
            image_data_url=request.image_data_url,
        )
        image_path = save_sample_image(identity["id"], request.image_data_url)

        stored = await add_embedding_to_identity(
            identity_id=identity["id"],
            embedding=resolved_embedding.embedding,
            metadata={"name": request.name, "role": request.role, "model_id": resolved_embedding.model_id},
            model_id=resolved_embedding.model_id,
            sample_kind="face",
            image_path=image_path,
            capture_source="enroll",
        )
        
        if not stored:
            raise HTTPException(status_code=500, detail="Failed to store embedding in Supabase. Check that 'embeddings' table exists.")
        
        return EnrollResponse(
            enrolled=True,
            subject_id=identity["id"],
            name=request.name,
            face_count=1,
            message=f"Enrolled as {request.name}"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Enrollment error: {e}")
        raise HTTPException(status_code=500, detail=f"Enrollment failed: {str(e)}")
