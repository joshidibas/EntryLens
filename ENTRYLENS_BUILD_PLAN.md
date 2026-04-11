# EntryLens — Agent Build Instructions

## Who You Are
You are an expert software agent building the **EntryLens** face-recognition attendance system.
Before writing a single line of code, you MUST explore the existing project structure so you understand what is already there. Never assume a file path — always verify it exists first.

## Decision Protocol
When you are unsure how to proceed, **make a decision, act on it, and tell the developer what you chose and why.** Do not ask permission for implementation details. Only pause and ask the developer if a decision is **irreversible** (e.g. dropping a database table, deleting files).

---

## Step 0 — Explore the Project First (MANDATORY)

Run the following before doing anything else. Use the results to guide every file path decision in all later steps.

```bash
# 1. Print the full project tree (2 levels deep to start)
find . -maxdepth 2 -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/__pycache__/*' -not -path '*/.venv/*'

# 2. Find the FastAPI entry point
find . -name "main.py" -not -path '*/__pycache__/*'

# 3. Find existing routers/routes
find . -name "*.py" | xargs grep -l "APIRouter\|@app\." 2>/dev/null

# 4. Find the existing face detection hook
find . -name "*.ts" -o -name "*.tsx" | xargs grep -l "mediapipe\|useFace\|sentry\|webcam" 2>/dev/null

# 5. Find requirements file
find . -name "requirements*.txt"

# 6. Find existing .env or .env.example
find . -name ".env*" -not -path '*/.git/*'

# 7. Find frontend source root
find . -name "vite.config.*" -o -name "package.json" -maxdepth 3 | grep -v node_modules
```

**After running these:** Decide the correct paths for every file in this plan based on what you find. Tell the developer: "I found the project structure. Here is how I am mapping the build plan to your actual project:" and list each file with its resolved path before proceeding.

---

## Context
You are building onto an **existing EntryLens bootstrap** that already has:
- ✅ Webcam feed working
- ✅ MediaPipe (`@mediapipe/tasks-vision`) face detection working
- ✅ FastAPI app scaffolded with existing routes
- ❌ No recognition engine yet
- ❌ No database connection yet

You are pivoting FROM cloud (AWS Rekognition) TO fully local recognition using **InsightFace (Python)** + **Supabase (pgvector)**.

**Do NOT touch the webcam feed or MediaPipe detection logic unless explicitly told to.**

---

## Tech Stack (Final)
| Layer | Technology |
|---|---|
| Frontend | React + Vite + TypeScript |
| Face Detection (gating) | `@mediapipe/tasks-vision` (already working — do not reinstall) |
| Face Recognition | `insightface` + `onnxruntime` (Python, CPU) |
| Backend | FastAPI (Python, already scaffolded) |
| Database | Supabase (PostgreSQL + `pgvector` extension) |
| Model | `buffalo_sc` (InsightFace small CPU model, ~100MB, downloads once on first run) |

---

## Phase 1 — Supabase Database Setup

### 1A. Explore before acting
First, check whether a Supabase client already exists in the project:
```bash
find . -name "*.py" | xargs grep -l "supabase\|create_client" 2>/dev/null
```
If one exists, read it and extend it rather than creating a new one. Tell the developer what you found.

### 1B. Run this SQL in the Supabase SQL editor (in this exact order):

```sql
-- Step 1: Enable pgvector
create extension if not exists vector;

-- Step 2: Identities table (one row per enrolled person)
create table identities (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  embedding vector(512),         -- InsightFace buffalo_sc produces 512-dim vectors
  created_at timestamptz default now()
);

-- Step 3: Cosine similarity index for fast nearest-neighbour search
create index on identities
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

-- Step 4: Attendance log (one row per recognised scan)
create table attendance_logs (
  id uuid primary key default gen_random_uuid(),
  person_id uuid references identities(id) on delete cascade,
  confidence float,
  timestamp timestamptz default now()
);

-- Step 5: Vector similarity search function
create or replace function match_identity(
  query_embedding vector(512),
  match_threshold float,
  match_count int
)
returns table (
  id uuid,
  name text,
  similarity float
)
language sql stable
as $$
  select
    id,
    name,
    1 - (embedding <=> query_embedding) as similarity
  from identities
  where 1 - (embedding <=> query_embedding) > match_threshold
  order by similarity desc
  limit match_count;
$$;
```

### 1C. Environment variables
Find the existing `.env` file (from Step 0 exploration). Add these variables to it — do not overwrite existing content:
```
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key_here
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres
```

> Use the **service role key** (not anon key) — FastAPI needs write access.
> Tell the developer: "I have added the Supabase variable placeholders to [path you found]. Please fill in your actual values before running the server."

---

## Phase 2 — Python Dependencies

### 2A. Find the existing requirements file
From Step 0 you found the requirements file path. Open it and **append** these — do not replace existing dependencies:
```
insightface==0.7.3
onnxruntime==1.17.1        # CPU version — do NOT install onnxruntime-gpu
numpy==1.26.4
opencv-python-headless==4.9.0.80
supabase==2.4.0
psycopg2-binary==2.9.9
python-dotenv==1.0.1
```

### 2B. Check for conflicts
```bash
# Check if any of these are already installed / at different versions
pip show insightface onnxruntime numpy opencv-python supabase 2>/dev/null
```
If a package is already present at a different version, decide which version to keep based on compatibility and tell the developer your decision.

### 2C. Install
```bash
pip install -r [path-to-requirements-file]
```

> InsightFace will auto-download `buffalo_sc` model files on first run. This is expected — not an error.

---

## Phase 3 — Backend: Supabase Client

### 3A. Find the best location
From Step 0, identify where database/config utilities live in the existing project. Place the Supabase client there. If no `db/` or `utils/` folder exists, create one adjacent to `main.py`.

### 3B. Create `supabase_client.py` in the location you chose:
```python
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_client: Client | None = None

def get_supabase() -> Client:
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SERVICE_KEY"]
        _client = create_client(url, key)
    return _client
```

---

## Phase 4 — Backend: Strategy Pattern (Provider Interface)

### 4A. Find the best location
Check if the project already has a `providers/`, `services/`, or `core/` folder. Place the interface there. If none exist, create `providers/` adjacent to `main.py`. Tell the developer what you chose.

### 4B. Create `base.py` (the FaceProvider interface):
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class RecognitionResult:
    person_id: Optional[str]   # UUID from local identities table
    name: Optional[str]
    confidence: float           # 0.0 – 1.0 cosine similarity
    matched: bool               # True if confidence >= threshold

class FaceProvider(ABC):
    @abstractmethod
    async def identify(self, image_bytes: bytes) -> RecognitionResult:
        """Compare face chip against enrolled embeddings. Returns best match."""
        pass

    @abstractmethod
    async def enroll(self, person_name: str, images: List[bytes]) -> str:
        """Generate embeddings for all images, average them, store in DB. Returns UUID."""
        pass
```

### 4C. Create `local_face_provider.py` in the same folder:
```python
import cv2
import numpy as np
from insightface.app import FaceAnalysis
from typing import List

from .base import FaceProvider, RecognitionResult
from [supabase_client_import_path] import get_supabase  # use path you resolved in Phase 3

CONFIDENCE_THRESHOLD = 0.45   # Cosine similarity — tune between 0.40–0.55

class LocalFaceProvider(FaceProvider):
    def __init__(self):
        # buffalo_sc: small CPU-optimised model (~100MB, downloads once automatically)
        self.app = FaceAnalysis(
            name="buffalo_sc",
            providers=["CPUExecutionProvider"]
        )
        self.app.prepare(ctx_id=0, det_size=(640, 640))

    def _decode_image(self, image_bytes: bytes) -> np.ndarray:
        arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image bytes")
        return img

    def _get_embedding(self, image_bytes: bytes) -> np.ndarray:
        img = self._decode_image(image_bytes)
        faces = self.app.get(img)
        if not faces:
            raise ValueError("No face detected in image")
        if len(faces) > 1:
            raise ValueError("Multiple faces detected — send a single face chip")
        return faces[0].embedding  # 512-dim float32 array

    async def enroll(self, person_name: str, images: List[bytes]) -> str:
        embeddings = [self._get_embedding(b) for b in images]
        centroid = np.mean(embeddings, axis=0)
        centroid = centroid / np.linalg.norm(centroid)  # L2 normalise

        supabase = get_supabase()
        result = supabase.table("identities").insert({
            "name": person_name,
            "embedding": centroid.tolist()
        }).execute()
        return result.data[0]["id"]

    async def identify(self, image_bytes: bytes) -> RecognitionResult:
        try:
            query_embedding = self._get_embedding(image_bytes)
        except ValueError:
            return RecognitionResult(person_id=None, name=None, confidence=0.0, matched=False)

        query_embedding = query_embedding / np.linalg.norm(query_embedding)

        supabase = get_supabase()
        response = supabase.rpc("match_identity", {
            "query_embedding": query_embedding.tolist(),
            "match_threshold": CONFIDENCE_THRESHOLD,
            "match_count": 1
        }).execute()

        if not response.data:
            return RecognitionResult(person_id=None, name=None, confidence=0.0, matched=False)

        top = response.data[0]
        matched = top["similarity"] >= CONFIDENCE_THRESHOLD

        if matched:
            supabase.table("attendance_logs").insert({
                "person_id": top["id"],
                "confidence": top["similarity"]
            }).execute()

        return RecognitionResult(
            person_id=top["id"],
            name=top["name"],
            confidence=top["similarity"],
            matched=matched
        )
```

> **Note for agent:** Replace `[supabase_client_import_path]` with the actual import path based on where you placed `supabase_client.py` in Phase 3.

---

## Phase 5 — Backend: API Endpoints

### 5A. Find the best location for the new router
Check how existing routers/routes are structured:
```bash
find . -name "*.py" | xargs grep -l "APIRouter" 2>/dev/null
```
Match the existing pattern — if routers live in `routers/`, place it there; if routes are inline in `main.py`, add to `main.py` directly. Tell the developer what you chose.

### 5B. Create the recognition router:
```python
import base64
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List
from pydantic import BaseModel

from [local_face_provider_import_path] import LocalFaceProvider  # use path you resolved

router = APIRouter(prefix="/api/v1", tags=["recognition"])
provider = LocalFaceProvider()   # Singleton — loads model once at startup

class RecognizeRequest(BaseModel):
    image_base64: str   # base64-encoded face chip from frontend

class RecognizeResponse(BaseModel):
    matched: bool
    name: str | None
    person_id: str | None
    confidence: float

@router.post("/recognize", response_model=RecognizeResponse)
async def recognize(request: RecognizeRequest):
    try:
        image_bytes = base64.b64decode(request.image_base64)
        result = await provider.identify(image_bytes)
        return RecognizeResponse(
            matched=result.matched,
            name=result.name,
            person_id=result.person_id,
            confidence=result.confidence
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enroll")
async def enroll(
    name: str = Form(...),
    images: List[UploadFile] = File(...)
):
    try:
        image_bytes_list = [await img.read() for img in images]
        person_id = await provider.enroll(name, image_bytes_list)
        return {"person_id": person_id, "name": name, "enrolled_images": len(image_bytes_list)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 5C. Register the router in `main.py`
Open the `main.py` you found in Step 0. Find where other routers are registered (look for `include_router` or `add_api_route`). Add the new router in the same style:
```python
from [recognition_router_import_path] import router as recognition_router
app.include_router(recognition_router)
```

---

## Phase 6 — Frontend Hook Update

### 6A. Find the face chip send location
From Step 0 you found the hook file. Open it and find where it currently sends the face chip (look for `fetch`, `axios`, `POST`, or any API call after face detection passes quality gates).

### 6B. Replace the endpoint URL only
Do not change any MediaPipe, webcam, or gating logic. Only change where the face chip is sent:
```typescript
const response = await fetch("http://localhost:8000/api/v1/recognize", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ image_base64: faceChipBase64 })
});

const result = await response.json();
// result shape: { matched: boolean, name: string | null, confidence: number, person_id: string | null }
```

### 6C. Find the best place for an enrollment UI
Check the existing frontend for:
```bash
find . -name "*.tsx" -o -name "*.jsx" | xargs grep -l "route\|Route\|page\|Page" 2>/dev/null
```
Add an enrollment component that fits the existing routing pattern. It should:
1. Accept a name (text input)
2. Capture 3–5 face chips from the existing webcam component (reuse, don't duplicate)
3. POST to `http://localhost:8000/api/v1/enroll` as `multipart/form-data` with `name` + `images[]`

---

## Phase 7 — Verification

After completing all phases, run through this checklist and report the result of each item to the developer:

- [ ] Supabase `identities` table exists with `embedding vector(512)` column
- [ ] Supabase `attendance_logs` table exists
- [ ] `match_identity` function visible under Database > Functions in Supabase dashboard
- [ ] `.env` has `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `DATABASE_URL` (values filled in by developer)
- [ ] `pip install` completed without errors
- [ ] FastAPI starts without import errors — run: `uvicorn [main_module]:app --reload`
- [ ] On first start, `buffalo_sc` model downloads to `~/.insightface/models/` (check terminal)
- [ ] `POST /api/v1/enroll` with name + 3 face images returns a UUID
- [ ] `POST /api/v1/recognize` with a face chip of an enrolled person returns `matched: true`
- [ ] A row appears in `attendance_logs` in Supabase after a successful recognition

---

## Hard Rules (Never Break These)

1. **Explore before creating** — always check if a file/folder exists before making a new one
2. **Do not modify MediaPipe or webcam logic** — face detection is already working
3. **Do not install `onnxruntime-gpu`** — this is a CPU-only deployment (i5, no GPU)
4. **buffalo_sc = 512-dim embeddings** — the SQL schema is `vector(512)`, never change this dimension
5. **LocalFaceProvider is a singleton** — instantiate once at module level, never per request
6. **CONFIDENCE_THRESHOLD = 0.45** — false negatives → lower to 0.40 | false positives → raise to 0.55
7. **When unsure about a path or approach** — make a decision, implement it, and tell the developer what you chose and why
