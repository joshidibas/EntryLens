import uuid
from fastapi import APIRouter, HTTPException
from app.schemas.enroll import EnrollRequest, EnrollResponse
from app.supabase import create_identity, store_embedding, SupabaseClient

router = APIRouter(prefix="/enroll", tags=["enrollment"])


@router.post("", response_model=EnrollResponse)
async def enroll(request: EnrollRequest):
    if not request.embedding:
        raise HTTPException(status_code=400, detail="No embedding provided")
    
    if len(request.embedding) != 16:
        raise HTTPException(status_code=400, detail="Invalid embedding format - expected 16 values")
    
    client = SupabaseClient.get_client()
    if not client:
        raise HTTPException(status_code=500, detail="Supabase client not initialized. Check SUPABASE_URL and SUPABASE_SERVICE_KEY in .env")
    
    try:
        subject_id = str(uuid.uuid4())
        
        identity = await create_identity(
            name=request.name,
            role=request.role,
            provider_subject_id=subject_id
        )
        
        if not identity:
            raise HTTPException(status_code=500, detail="Failed to create identity in Supabase. Check that 'identities' table exists and service key has proper permissions.")
        
        stored = await store_embedding(
            identity_id=identity["id"],
            embedding=request.embedding,
            metadata={"name": request.name, "role": request.role}
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