from fastapi import APIRouter, HTTPException

from app.schemas.identity import CandidateMatch
from app.schemas.recognize import RecognizeRequest, RecognizeResponse
from app.supabase import count_embeddings_for_identity, get_identity_by_id, search_similar_embeddings

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
                message="No matching identity found",
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
                message="Identity not found",
            )

        display_name = identity.get("display_name") or identity.get("name")
        return RecognizeResponse(
            matched=True,
            identity_id=identity_id,
            name=display_name,
            similarity=similarity,
            message=f"Matched: {display_name}",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recognition failed: {str(e)}")


@router.post("/candidates", response_model=list[CandidateMatch])
async def candidate_matches(request: RecognizeRequest):
    if not request.embedding:
        raise HTTPException(status_code=400, detail="No embedding provided")

    if len(request.embedding) != 16:
        raise HTTPException(status_code=400, detail="Invalid embedding format")

    try:
        results = await search_similar_embeddings(request.embedding, limit=10)
        best_by_identity: dict[str, float] = {}
        for result in results:
            identity_id = result.get("identity_id")
            if not identity_id:
                continue
            similarity = float(result.get("similarity", 0.0))
            previous = best_by_identity.get(identity_id)
            if previous is None or similarity > previous:
                best_by_identity[identity_id] = similarity

        items: list[CandidateMatch] = []
        for identity_id, similarity in sorted(best_by_identity.items(), key=lambda item: item[1], reverse=True)[:5]:
            identity = await get_identity_by_id(identity_id)
            if not identity:
                continue
            items.append(
                CandidateMatch(
                    identity_id=identity_id,
                    display_name=identity.get("display_name", "Unknown"),
                    identity_type=identity.get("identity_type", "visitor"),
                    similarity=similarity,
                    sample_count=await count_embeddings_for_identity(identity_id),
                )
            )

        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Candidate lookup failed: {str(e)}")
