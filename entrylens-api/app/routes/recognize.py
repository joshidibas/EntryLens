from fastapi import APIRouter, HTTPException
from app.schemas.recognize import RecognizeRequest, RecognizeResponse
from app.supabase import search_similar_embeddings, get_identity_by_id

router = APIRouter(prefix="/recognize", tags=["recognition"])


@router.post("", response_model=RecognizeResponse)
async def recognize(request: RecognizeRequest):
    if not request.embedding:
        raise HTTPException(status_code=400, detail="No embedding provided")
    
    if len(request.embedding) != 16:
        raise HTTPException(status_code=400, detail="Invalid embedding format")
    
    try:
        results = await search_similar_embeddings(request.embedding, limit=1)
        
        if not results or len(results) == 0:
            return RecognizeResponse(
                matched=False,
                identity_id=None,
                name=None,
                similarity=0.0,
                message="No matching identity found"
            )
        
        best_match = results[0]
        identity_id = best_match.get("identity_id")
        similarity = float(best_match.get("similarity", 0.0))
        
        identity = await get_identity_by_id(identity_id)
        
        if not identity:
            return RecognizeResponse(
                matched=False,
                identity_id=None,
                name=None,
                similarity=0.0,
                message="Identity not found"
            )
        
        return RecognizeResponse(
            matched=True,
            identity_id=identity_id,
            name=identity.get("name"),
            similarity=similarity,
            message=f"Matched: {identity.get('name')}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recognition failed: {str(e)}")