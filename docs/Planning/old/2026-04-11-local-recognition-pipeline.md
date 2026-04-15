# Local Recognition Pipeline - Initial Implementation Plan

## Task Summary

Implement the initial local recognition pipeline: enrollment endpoint, recognition endpoint, and wire them into the Labs UI so "Recognize Face" → "Local Recognition" actually works.

## Current Repo Truth

- `entrylens-api/app/providers/local_provider.py` - scaffold exists but `_extract_embedding()` returns `None` (placeholder)
- `entrylens-api/app/supabase.py` - Supabase client exists with `store_embedding()`, `search_similar_embeddings()`
- Labs page at `entrylens-frontend/src/pages/LabsPage.tsx` - "Local Recognition" target shows as "planned" (status: "planned")
- No `/api/v1/enroll` or `/api/v1/recognize` routes exist yet
- Supabase env vars already configured in `.env`

## Assumptions

- Supabase has the required tables (`identities`, `embeddings`) - need to verify/create
- InsightFace is the chosen library for server-side embedding extraction (per build plan)
- Initial implementation targets: enrollment via file upload, recognition via file probe
- Live camera → recognition comes later (Phase 2)

## File Paths Expected To Change

- `entrylens-api/requirements.txt` - add insightface, onnxruntime, opencv-python-headless
- `entrylens-api/app/providers/local_provider.py` - implement real `_extract_embedding()` with InsightFace
- `entrylens-api/app/routes/enroll.py` - create enrollment endpoint
- `entrylens-api/app/routes/recognize.py` - create recognition endpoint
- `entrylens-api/app/schemas/enroll.py` - create request/response models
- `entrylens-api/app/schemas/recognize.py` - create request/response models
- `entrylens-api/app/main.py` - register new routers
- `entrylens-frontend/src/api/recognition.ts` - create API calls for enroll/recognize
- `entrylens-frontend/src/pages/LabsPage.tsx` - wire Local Recognition to use real endpoints

## Implementation Steps

### Step 1: Add Python Dependencies

1. Add to `entrylens-api/requirements.txt`:
   - `insightface==0.7.3`
   - `onnxruntime==1.17.1` (CPU only)
   - `opencv-python-headless==4.9.0.80`

2. Install dependencies

### Step 2: Implement Real Embedding Extraction

1. Update `LocalProvider._extract_embedding()` to use InsightFace:
   - Load `buffalo_sc` model on provider init
   - Decode image bytes with OpenCV
   - Extract 512-dim embedding
   - Return normalized embedding vector

2. Verify embedding extraction works with a test image

### Step 3: Create Enrollment Endpoint

1. Create `app/schemas/enroll.py`:
   - `EnrollRequest`: name (str), role (staff/visitor), images (list[base64])
   - `EnrollResponse`: enrolled (bool), subject_id (uuid), face_count (int)

2. Create `app/routes/enroll.py`:
   - `POST /api/v1/enroll` - accepts form data with name + multiple images
   - Decode base64 images to bytes
   - Call `provider.enroll(name, images)`
   - Store identity in Supabase

3. Register router in `main.py`

### Step 4: Create Recognition Endpoint

1. Create `app/schemas/recognize.py`:
   - `RecognizeRequest`: image (base64), camera_id (optional)
   - `RecognizeResponse`: matched (bool), identity_id (uuid), name (str), similarity (float)

2. Create `app/routes/recognize.py`:
   - `POST /api/v1/recognize` - accepts JSON with base64 image
   - Call `provider.identify(image_bytes)`
   - Return match result with similarity score

3. Register router in `main.py`

### Step 5: Update Frontend Labs UI

1. Create `entrylens-frontend/src/api/recognition.ts`:
   - `enroll(name, role, images[])` - POST to /api/v1/enroll
   - `recognize(image)` - POST to /api/v1/recognize

2. Update `LabsPage.tsx`:
   - Change "Local Recognition" target from status: "planned" to "ready"
   - Wire enroll form to call real API
   - Wire "identify" command to call real API
   - Display recognition results in result panel

### Step 6: Verification

1. Start backend server
2. Open Labs page, select "Recognize Face" → "Local Recognition"
3. Upload enrollment photos for a test person
4. Upload a probe image
5. Run "identify" command
6. Verify result shows matched identity + similarity score

## Docs Update Checklist

- [ ] Update `docs/tasks/todo.md` with new active task
- [ ] Update `docs/project-truth/architecture-truth.md` with new routes



<!-- graphify-links:start -->
## Graph Links

- [[graphify-out/wiki/index|Graphify Wiki]]
- [[graphify-out/GRAPH_REPORT|Graph Report]]
- Related file notes:
  - [[graphify-out/wiki/entrylens-api/app/main.py|entrylens-api/app/main.py]]
  - [[graphify-out/wiki/entrylens-api/app/providers/local_provider.py|entrylens-api/app/providers/local_provider.py]]
  - [[graphify-out/wiki/entrylens-api/app/routes/enroll.py|entrylens-api/app/routes/enroll.py]]
  - [[graphify-out/wiki/entrylens-api/app/routes/recognize.py|entrylens-api/app/routes/recognize.py]]
  - [[graphify-out/wiki/entrylens-api/app/schemas/enroll.py|entrylens-api/app/schemas/enroll.py]]
  - [[graphify-out/wiki/entrylens-api/app/schemas/recognize.py|entrylens-api/app/schemas/recognize.py]]
  - [[graphify-out/wiki/entrylens-api/app/supabase.py|entrylens-api/app/supabase.py]]
  - [[graphify-out/wiki/entrylens-frontend/src/pages/LabsPage.tsx|entrylens-frontend/src/pages/LabsPage.tsx]]
- Related communities:
  - [[graphify-out/wiki/communities/Community 0|Community 0]]
  - [[graphify-out/wiki/communities/Community 2|Community 2]]
  - [[graphify-out/wiki/communities/Community 3|Community 3]]
  - [[graphify-out/wiki/communities/Community 8|Community 8]]
<!-- graphify-links:end -->
