# Local Recognition Pipeline - Sequence 2: Recognition from Live Feed

## Task Summary

Create recognition flow from Labs page where user can test recognition with live camera feed. System detects faces in real-time, extracts embedding, queries Supabase for similar embeddings, displays matched identity name or "Unknown".

**Note: This runs in Labs first for testing. Attendance logging and visitor logs come in a later phase.**

## Flow Description

1. User opens Labs page → select "Recognize Face" → "Local Recognition"
2. Live camera feed displays in Labs (reuse existing CameraPanel)
3. MediaPipe runs in browser, detects faces in real-time
4. User clicks "Identify" or "Verify" command in Labs UI
5. Frontend captures current face chip as base64
6. POST to `/api/v1/recognize` with base64 image
7. Backend: extract embedding with InsightFace → search Supabase embeddings
8. Return match result: `{ identity_id, name, similarity }`
9. Frontend: display result in Labs "Latest Result" panel
10. Show recognized name OR "Unknown" with confidence indicator

## Current Repo Truth (Pre-requisites)

- Sequence 1 (Enrollment) must be complete first
- Supabase has `identities` table with enrolled users
- `POST /api/v1/enroll` works in Labs
- `/api/v1/recognize` does NOT exist yet
- Labs page has "identify" command button for "Local Recognition" target

## File Paths Expected To Change

### Backend
- `entrylens-api/app/routes/recognize.py` - create POST /api/v1/recognize
- `entrylens-api/app/schemas/recognize.py` - request/response models
- May need to update `app/providers/local_provider.py` - ensure identify() works with Supabase search

### Frontend (Labs Integration)
- `entrylens-frontend/src/pages/LabsPage.tsx` - wire "identify" command to call real API, show result in panel
- `entrylens-frontend/src/api/recognize.ts` - create API call to backend
- `entrylens-frontend/src/hooks/useMediaPipeLab.ts` - may need to expose current frame as base64 for identify

## Implementation Steps

### Step 1: Create Recognition Endpoint

Create `app/routes/recognize.py`:
```python
@router.post("/recognize")
async def recognize(request: RecognizeRequest):
    # Decode base64 to bytes
    image_bytes = base64.b64decode(request.image)
    
    # Call provider to identify
    result = await provider.identify(image_bytes)
    
    # If matched, get identity details from Supabase
    if result.subject_id:
        identity = await get_identity_by_id(result.subject_id)
        return {
            "matched": True,
            "identity_id": result.subject_id,
            "name": identity.get("name"),
            "similarity": result.similarity
        }
    
    return {
        "matched": False,
        "identity_id": None,
        "name": None,
        "similarity": 0.0
    }
```

### Step 2: Implement Identify in LocalProvider

Update `LocalProvider.identify()`:
```python
async def identify(self, image_bytes: bytes) -> ProviderResponse:
    # Extract embedding
    embedding = self._extract_embedding(image_bytes)
    if not embedding:
        return ProviderResponse(subject_id=None, similarity=0.0, bbox=None)
    
    # Search Supabase for similar embeddings
    results = await search_similar_embeddings(embedding, limit=1)
    
    if not results:
        return ProviderResponse(subject_id=None, similarity=0.0, bbox=None)
    
    best = results[0]
    return ProviderResponse(
        subject_id=best.get("identity_id"),
        similarity=best.get("similarity", 0.0),
        bbox=None
    )
```

### Step 3: Update Labs Page for Recognition

Update `LabsPage.tsx`:

1. When user clicks "identify" command in Local Recognition section:
   - Capture current camera frame as base64
   - POST to `/api/v1/recognize`
   
2. Display result in "Latest Result" panel:
   - If matched: Show name with similarity %
   - If not matched: Show "Unknown"

3. Add indicator during API call: "Recognizing..."

### Step 4: Verification

1. Ensure at least one identity is enrolled (from Sequence 1) via Labs
2. Open Labs page → select "Recognize Face" → "Local Recognition"
3. Ensure camera is active
4. Click "identify" command button
5. See result in "Latest Result" panel
6. Verify shows correct enrolled name with confidence
7. Test with non-enrolled person → shows "Unknown"

## Visual States (in Labs Context)

| State | UI Indicator |
|-------|-------------|
| No face | "No face detected" in detection status |
| Face detected | "Face detected" (yellow) in detection status |
| Recognizing | Button shows "Identifying..." while API call |
| Matched | "Latest Result" shows: `{ matched: true, name: "Alice", similarity: 0.95 }` |
| Not matched | "Latest Result" shows: `{ matched: false, name: null }` |

## Notes

- This runs in Labs page first for testing/verification
- No attendance logs created - that comes in a later phase
- No visitor logs created - that comes in a later phase
- Sequence 3 will be: Continuous auto-recognition on Live page with attendance logging

## Docs Update Checklist

- [ ] Update `docs/tasks/todo.md` - mark this as active after Sequence 1
- [ ] Update `docs/project-truth/architecture-truth.md` - add /api/v1/recognize route




<!-- graphify-links:start -->
## Graph Links

- [[graphify-out/wiki/index|Graphify Wiki]]
- [[graphify-out/GRAPH_REPORT|Graph Report]]
- Related file notes:
  - [[graphify-out/wiki/entrylens-api/app/routes/recognize.py|entrylens-api/app/routes/recognize.py]]
  - [[graphify-out/wiki/entrylens-api/app/schemas/recognize.py|entrylens-api/app/schemas/recognize.py]]
  - [[graphify-out/wiki/entrylens-frontend/src/api/recognize.ts|entrylens-frontend/src/api/recognize.ts]]
  - [[graphify-out/wiki/entrylens-frontend/src/hooks/useMediaPipeLab.ts|entrylens-frontend/src/hooks/useMediaPipeLab.ts]]
  - [[graphify-out/wiki/entrylens-frontend/src/pages/LabsPage.tsx|entrylens-frontend/src/pages/LabsPage.tsx]]
- Related communities:
  - [[graphify-out/wiki/communities/Community 3|Community 3]]
  - [[graphify-out/wiki/communities/Community 9|Community 9]]
  - [[graphify-out/wiki/communities/Community 10|Community 10]]
<!-- graphify-links:end -->
