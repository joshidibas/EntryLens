# Local Recognition Pipeline - Sequence 1: Enrollment from Live Feed

## Task Summary

Create enrollment flow where user views live camera feed in Labs, sees face detected in real-time, enters their name, and clicks Enroll to capture their face chip and store identity in Supabase.

**Note: This should be accessible from Labs page first, not the dedicated Enrollment page. Attendance logging comes later.**

## Flow Description

1. User opens Labs page → select "Recognize Face" → "Local Recognition"
2. Live camera feed displays in Labs (reuse existing CameraPanel)
3. MediaPipe runs in browser, shows real-time face detection status
4. When stable face detected → show "Face detected" indicator
5. User enters their name in Labs enrollment form
6. User clicks "Enroll" button in Labs
7. Frontend captures current face chip as base64
8. POST to `/api/v1/enroll` with: `{ name, image: base64 }`
9. Backend: extract embedding with InsightFace → store in Supabase
10. Return success: "Enrolled as {name}"

## Current Repo Truth

- `entrylens-frontend/src/pages/LabsPage.tsx` - has enrollment form for Azure backend, "Local Recognition" shows as "planned"
- `entrylens-frontend/src/components/CameraPanel.tsx` - live camera with MediaPipe detection
- `entrylens-frontend/src/hooks/useMediaPipeLab.ts` - MediaPipe detection working in Labs
- `entrylens-api/app/providers/local_provider.py` - scaffold with placeholder `_extract_embedding()`
- `entrylens-api/app/supabase.py` - client exists
- No `/api/v1/enroll` route exists

## File Paths Expected To Change

### Backend
- `entrylens-api/requirements.txt` - add insightface, onnxruntime, opencv-python-headless
- `entrylens-api/app/providers/local_provider.py` - implement `_extract_embedding()` with InsightFace
- `entrylens-api/app/routes/enroll.py` - create POST /api/v1/enroll
- `entrylens-api/app/schemas/enroll.py` - request/response models
- `entrylens-api/app/main.py` - register enroll router

### Frontend (Labs Integration First)
- `entrylens-frontend/src/pages/LabsPage.tsx` - change Local Recognition from "planned" to "ready", wire to real API
- `entrylens-frontend/src/api/enroll.ts` - create API call to backend
- `entrylens-frontend/src/components/CameraPanel.tsx` - may need to expose face chip capture
- `entrylens-frontend/src/hooks/useMediaPipeLab.ts` - may need to expose current frame as base64

## Implementation Steps

### Step 1: Verify Frontend MediaPipe Setup

MediaPipe is already installed in frontend (`@mediapipe/tasks-vision`). Verify it can output embeddings:
- Check `useMediaPipeLab.ts` - currently returns landmarks, not embeddings
- Need to enable `outputFacialTransformationMatrixes: true` to get face embedding

### Step 2: Update Frontend to Extract Face Embedding

Update `useMediaPipeLab.ts` to:
1. Enable facial transformation matrix output
2. Extract embedding vector from MediaPipe result
3. Export function to get current frame as base64 + embedding

### Step 3: Create Enrollment API

Create `app/routes/enroll.py` that accepts:
```json
{
  "name": "Alice",
  "embedding": [0.1, 0.2, ...]  // 128-256 float array from MediaPipe
}
```

Backend: store embedding directly in Supabase (no InsightFace needed)

### Step 4: Create Recognition API

Create `app/routes/recognize.py` that accepts:
```json
{
  "embedding": [0.1, 0.2, ...]
}
```

Backend: search Supabase for similar embedding using pgvector

### Step 5: Wire Labs Page

Update LabsPage.tsx:
- When user clicks "Enroll" → capture current MediaPipe embedding → POST to /api/v1/enroll
- When user clicks "identify" → capture embedding → POST to /api/v1/recognize → show result

## Why This Approach

- MediaPipe runs in browser - no server ML needed
- Embedding vectors (~256 floats) smaller than base64 images
- Supabase with pgvector handles similarity search
- Same end result: enrollment + recognition in Labs

## Notes

- This is Sequence 1 (Enrollment)
- Sequence 2 will be: Recognition from live feed
- Sequence 3 will be: Full recognition flow with name display

## Docs Update Checklist

- [ ] Update `docs/tasks/todo.md` - mark this as active
- [ ] Update `docs/project-truth/architecture-truth.md` - add /api/v1/enroll route




<!-- graphify-links:start -->
## Graph Links

- [[graphify-out/wiki/index|Graphify Wiki]]
- [[graphify-out/GRAPH_REPORT|Graph Report]]
- Related file notes:
  - [[graphify-out/wiki/entrylens-api/app/main.py|entrylens-api/app/main.py]]
  - [[graphify-out/wiki/entrylens-api/app/providers/local_provider.py|entrylens-api/app/providers/local_provider.py]]
  - [[graphify-out/wiki/entrylens-api/app/routes/enroll.py|entrylens-api/app/routes/enroll.py]]
  - [[graphify-out/wiki/entrylens-api/app/schemas/enroll.py|entrylens-api/app/schemas/enroll.py]]
  - [[graphify-out/wiki/entrylens-api/app/supabase.py|entrylens-api/app/supabase.py]]
  - [[graphify-out/wiki/entrylens-frontend/src/api/enroll.ts|entrylens-frontend/src/api/enroll.ts]]
  - [[graphify-out/wiki/entrylens-frontend/src/components/CameraPanel.tsx|entrylens-frontend/src/components/CameraPanel.tsx]]
  - [[graphify-out/wiki/entrylens-frontend/src/hooks/useMediaPipeLab.ts|entrylens-frontend/src/hooks/useMediaPipeLab.ts]]
  - [[graphify-out/wiki/entrylens-frontend/src/pages/LabsPage.tsx|entrylens-frontend/src/pages/LabsPage.tsx]]
- Related communities:
  - [[graphify-out/wiki/communities/Community 0|Community 0]]
  - [[graphify-out/wiki/communities/Community 2|Community 2]]
  - [[graphify-out/wiki/communities/Community 3|Community 3]]
  - [[graphify-out/wiki/communities/Community 4|Community 4]]
  - [[graphify-out/wiki/communities/Community 9|Community 9]]
  - [[graphify-out/wiki/communities/Community 10|Community 10]]
<!-- graphify-links:end -->
