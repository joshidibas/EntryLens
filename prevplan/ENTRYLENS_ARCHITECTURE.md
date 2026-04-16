# EntryLens — System Architecture Document

> **Purpose:** This document is the single source of truth for any LLM or developer
> working on this project. Read this before writing any code, asking any question,
> or making any architectural decision. Every section exists for a reason.

---

## 0. Project Summary

EntryLens is a **face-recognition-based attendance and visitor tracking system**.
A browser-based React frontend streams from a camera, performs quality gating using
MediaPipe, and sends only high-quality face crops to a FastAPI backend. The backend
uses a **Strategy Pattern** to route recognition requests to either a cloud-based
provider (Azure Face API) or a self-hosted engine (CompreFace). Results are persisted
in PostgreSQL, and a real-time WebSocket feed updates the dashboard.

**Design philosophy:** Pragmatic Staged Monolith. Clean internal boundaries today.
Hard service splits only when the data justifies them. Every component added is a
component that can fail.

**Current deployment posture (v1.1):** Hybrid — Local Frontend/Backend + Cloud
Recognition (Azure Face API). This is a deliberate hardware-driven pivot. The local
dev machine (i5 5th Gen, 8GB RAM, no GPU) cannot run the full ML stack. Azure offloads
the compute. CompreFace is the Phase 2 replacement when hardware is upgraded.

---

## 1. Constraints and Context

| Parameter | Value |
|---|---|
| Deployment (Phase 1) | **Hybrid:** Local Frontend + Local FastAPI + Cloud Recognition (Azure) |
| Development Hardware | i5 5th Gen, 8GB RAM — No GPU |
| Deployment (Phase 2) | Full On-Prem / Docker Compose (requires hardware upgrade) |
| Enrolled identities at launch | < 100 people |
| Cameras at launch | 1 camera, 1 entry point |
| Acceptable recognition latency | Near real-time (< 3s). Low-confidence matches deferred. |
| Admin interface | Browser-based dashboard (React) |
| External integrations | CSV export only |
| Team | Solo developer + AI assistants (Codex, Claude, Gemini) |
| Privacy / compliance | None enforced now. GDPR-like constraints expected in Phase 2. |
| Build philosophy | Simple now, clear migration path to scalable later |

---

## 2. Tech Stack

### Why each choice was made

**React + MediaPipe (Frontend)**
- MediaPipe Face Landmarker runs entirely in the browser via WASM.
- Performs head pose estimation (Yaw/Pitch angles) client-side before sending anything
  to the server. This reduces server load by ~90% by rejecting off-angle or blurry
  frames before they ever leave the browser.
- React is the natural choice for a real-time dashboard with WebSocket state updates.

**FastAPI (API Layer)**
- Python. Async-native. Fast to write and easy for AI assistants to read and extend.
- Clean decorator-based routing makes the codebase self-documenting.
- Pydantic models enforce strict input validation at the boundary.
- Strategy Pattern implementation lives here — provider is injected at startup via
  environment variable (`SENTINEL_RECOGNITION_PROVIDER=azure|compreface`).

**Azure Face API (Recognition — Phase 1 / Current)**
- Offloads all ML compute to the cloud. Zero local GPU requirement.
- Enables development and testing on constrained hardware (i5, 8GB RAM).
- Per-call cost is acceptable at < 100 enrolled identities and low camera volume.
- **Exit condition:** Replaced by CompreFace when hardware is upgraded (Phase 2).

**CompreFace (Recognition — Phase 2 / Future)**
- Open source. Self-hosted via Docker. No vendor lock-in, no per-call cost.
- Ships with InsightFace + ArcFace model — best-in-class accuracy for a free,
  self-hostable option.
- Exposes a clean REST API. Zero ML code required on our side.
- Native support for subject management (enrollment, deletion, re-enrollment).
- Manual review confirmations feed back as re-enrollments → model self-improves.
- **Swap mechanism:** Implement the same `FaceProvider` interface. One env var change.

**PostgreSQL + pgvector (Persistence)**
- pgvector adds a native vector column type and cosine similarity search.
- At < 100 people × 10 photos = ~1,000 vectors, pgvector handles this with zero
  performance concern. Migration to Milvus happens at the 10,000+ vector threshold.
- Attendance logs, identity metadata, and deferred review queue all live in the same
  Postgres instance. One database to operate.

**MinIO (Object Storage — Phase 1) / S3 (Phase 2)**
- Raw face chip images are stored with a short TTL (7 days) for audit purposes,
  then purged. This keeps the system GDPR-friendly.
- Mathematical embeddings are stored permanently in PostgreSQL.
- MinIO is S3-compatible and runs in Docker locally. Swap to S3 in Phase 2 with a
  one-line config change.

**No Redis (Phase 1)**
- Temporal debouncing (suppress duplicate logs within 5 minutes) is implemented as a
  plain Python `dict` with timestamps in FastAPI process memory.
- Redis is added when the system goes multi-instance or multi-camera. Not before.

---

## 3. Implementation Strategy: The Strategy Pattern

To ensure the system is **hardware-agnostic and provider-portable**, the backend uses
a decoupled provider structure. The active provider is selected at startup via
environment variable. No code changes are required to switch between Azure and CompreFace.

```python
# app/providers/base.py
class FaceProvider(ABC):
    @abstractmethod
    async def identify(self, image_bytes: bytes): pass

    @abstractmethod
    async def enroll(self, user_id: str, images: list): pass
```

```python
# app/providers/azure_provider.py
class AzureProvider(FaceProvider):
    async def identify(self, image_bytes): ...  # Calls Azure Face API
    async def enroll(self, user_id, images): ...

# app/providers/compreface_provider.py
class CompreFaceProvider(FaceProvider):
    async def identify(self, image_bytes): ...  # Calls local CompreFace REST
    async def enroll(self, user_id, images): ...
```

```python
# app/main.py — provider injected at startup
provider = AzureProvider() if os.getenv("SENTINEL_RECOGNITION_PROVIDER") == "azure" \
           else CompreFaceProvider()
```

> **LLM instruction:** When writing any recognition or enrollment logic, always call
> `provider.identify()` or `provider.enroll()`. Never call Azure or CompreFace
> directly from a route handler.

---

## 4. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1 — Edge (Browser)                                   │
│                                                             │
│  [React UI] ──► [MediaPipe Hook] ──► [Face Chip Capture]   │
│   Dashboard        Quality gate          224×224 crop       │
│   WebSocket rx     Yaw/Pitch < 15°       HTTPS POST ──────────────►
│                    Stable 800ms                             │
└─────────────────────────────────────────────────────────────┘
                                                    │
                                                    ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2 — API Synapse (FastAPI)                            │
│                                                             │
│  [Auth + Router] ──► [Mode Router] ──► [Debounce Layer]    │
│   JWT / API key      Enroll vs           In-memory TTL dict │
│                      Recognise           5-min window       │
│                           │                                 │
│                           ▼                                 │
│                  [Strategy: FaceProvider]                   │
│                   Azure (Phase 1) /                         │
│                   CompreFace (Phase 2)                      │
│                           │                                 │
│                           ▼                                 │
│                  [Deferred Review Queue]                    │
│                   0.60–0.84 confidence                      │
│                   flagged for manual review                 │
└─────────────────────────────────────────────────────────────┘
         │                                    │
         ▼                                    ▼ (WebSocket push)
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3 — Persistence                                      │
│                                                             │
│  [PostgreSQL + pgvector] ──────────────► [MinIO/S3]        │
│   Embeddings, logs,                       Face chips        │
│   review queue, attendance history        Short TTL         │
└─────────────────────────────────────────────────────────────┘
```

### Hybrid Data Flow (Phase 1 — Current)

```
Local Edge (Browser)     →   Local API (FastAPI)   →   Cloud Brain (Azure)
MediaPipe quality gate       Strategy router            Biometric matching
Yaw/Pitch gating             Auth, debounce,            Returns subject_id
224×224 crop                 threshold routing          + similarity score
                                    │
                                    ▼
                         Local Memory (PostgreSQL)
                         All logs and metadata stay
                         on-premises. No PII in cloud
                         beyond the face chip per call.
```

---

## 5. Data Flow

### 5a. Recognition Flow (steady state)

```
1.  Browser opens camera stream
2.  MediaPipe processes every frame (~30fps), extracts face landmarks
3.  Head pose estimated from landmarks (Yaw, Pitch, Roll)
4.  GATE CHECK: if Yaw > 15° or Pitch > 15° → discard frame, loop
5.  STABILITY CHECK: face must be stable for 800ms → start timer on first
    valid frame, reset on movement, fire on completion
6.  On stable valid frame: crop 224×224 face chip from video frame
7.  POST /api/v1/recognize { image: base64_chip }
8.  FastAPI auth middleware validates JWT or API key
9.  Debounce Layer checks in-memory dict:
    - If identity seen in last 5 minutes → update "active" status, do NOT log
    - If not seen → continue
10. FaceProvider.identify(image_bytes) called → Azure or CompreFace
    returns { subject_id, similarity, bbox }
11. Threshold routing:
    - similarity > 0.85  → AttendanceLog (status: confirmed)
    - 0.60–0.84          → ReviewItem (status: pending_review)
    - < 0.60             → AttendanceLog (status: visitor)
12. Result written to PostgreSQL
13. Image chip written to MinIO with TTL tag
14. FastAPI emits WebSocket event to all connected dashboard clients
15. React dashboard receives event, updates live feed
```

### 5b. Enrollment Flow

```
1. Operator uploads 10 photos via dashboard enrollment form
2. POST /api/v1/enroll { subject_id, name, role, images: [base64 × 10] }
3. FaceProvider.enroll(subject_id, images) called
   - Azure: registers faces under PersonGroup
   - CompreFace: POSTs to /api/v1/recognition/faces
4. FastAPI stores identity metadata in PostgreSQL identities table
5. Response: { enrolled: true, subject_id, face_count: 10 }
```

### 5c. Self-Improvement Loop (manual review → re-enrollment)

```
1. Operator opens Review Queue in dashboard
2. Sees flagged detections (0.60–0.84 confidence) with face chip image
3. Operator confirms or rejects match
4. On confirm: face chip sent to FaceProvider.enroll() as additional sample
   → subject now has 11+ samples → better future accuracy
5. ReviewItem updated to status: resolved in PostgreSQL
6. Image TTL extended (or removed) for confirmed identities
```

---

## 6. Database Schema

```sql
-- Core identity record
CREATE TABLE identities (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name                    TEXT NOT NULL,
  role                    TEXT NOT NULL DEFAULT 'staff',   -- 'staff' | 'visitor'
  provider_subject_id     TEXT UNIQUE NOT NULL,            -- Azure PersonId or CompreFace subject
  enrolled_at             TIMESTAMPTZ DEFAULT now(),
  metadata                JSONB DEFAULT '{}'
);

-- Every recognition event
CREATE TABLE attendance_logs (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  identity_id  UUID REFERENCES identities(id) ON DELETE SET NULL,
  status       TEXT NOT NULL,   -- 'confirmed' | 'visitor' | 'pending_review'
  similarity   FLOAT,
  image_key    TEXT,            -- MinIO object key, nullable after TTL purge
  detected_at  TIMESTAMPTZ DEFAULT now(),
  camera_id    TEXT DEFAULT 'cam-01'
);

-- Items awaiting operator decision (similarity 0.60–0.84)
CREATE TABLE review_queue (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  attendance_log_id     UUID REFERENCES attendance_logs(id),
  candidate_identity_id UUID REFERENCES identities(id) ON DELETE SET NULL,
  similarity            FLOAT,
  image_key             TEXT,
  status                TEXT DEFAULT 'pending',  -- 'pending' | 'confirmed' | 'rejected'
  reviewed_at           TIMESTAMPTZ,
  created_at            TIMESTAMPTZ DEFAULT now()
);

-- pgvector: local mirror of embeddings for custom queries
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE embeddings_mirror (
  identity_id UUID REFERENCES identities(id) ON DELETE CASCADE,
  embedding   VECTOR(128),   -- ArcFace 128-d float vectors
  created_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON embeddings_mirror USING ivfflat (embedding vector_cosine_ops);
```

> **Schema note (v1.1):** `compreface_subject_id` renamed to `provider_subject_id`
> to be provider-agnostic. Stores Azure `PersonId` in Phase 1, CompreFace `subject`
> in Phase 2. No schema migration needed between phases.

---

## 7. Recognition Thresholds

| Similarity Score | Decision | Action |
|---|---|---|
| > 0.85 | High-confidence match | `attendance_logs` entry, status `confirmed` |
| 0.60 – 0.84 | Possible match | `review_queue` entry, operator must confirm |
| < 0.60 | Unknown / new visitor | `attendance_logs` entry, status `visitor` |

These values are configurable via environment variable. **Never hardcode them.**

```env
SENTINEL_RECOGNITION_PROVIDER=azure           # or: compreface
SENTINEL_HIGH_CONFIDENCE_THRESHOLD=0.85
SENTINEL_LOW_CONFIDENCE_THRESHOLD=0.60
SENTINEL_DEBOUNCE_WINDOW_SECONDS=300

# Azure (Phase 1)
AZURE_FACE_API_KEY=<key>
AZURE_FACE_ENDPOINT=<endpoint>
AZURE_PERSON_GROUP_ID=sentinel-v1

# CompreFace (Phase 2)
COMPREFACE_URL=http://compreface-api:8080
COMPREFACE_API_KEY=<key>
```

---

## 8. API Endpoints (FastAPI)

```
POST   /api/v1/recognize              Receive face chip, run recognition via provider
POST   /api/v1/enroll                 Enroll new identity (10 images) via provider
GET    /api/v1/attendance             List attendance logs (filterable by date, status)
GET    /api/v1/review                 List pending review queue items
POST   /api/v1/review/{id}/confirm    Confirm match → re-enroll via provider
POST   /api/v1/review/{id}/reject     Reject match → mark as visitor
GET    /api/v1/identities             List all enrolled identities
DELETE /api/v1/identities/{id}        Remove identity from provider + PostgreSQL + MinIO
GET    /api/v1/export/csv             Export attendance as CSV

WS     /ws/live                       WebSocket — pushes recognition events to dashboard
```

---

## 9. Docker Compose Layout

### Phase 1 (Current — Hybrid, Azure)

```yaml
services:
  sentinel-db:        # PostgreSQL + pgvector (port 5432)
  sentinel-api:       # FastAPI app (port 8000) — connects to Azure over internet
  sentinel-storage:   # MinIO object store (port 9000 / 9001 console)
  sentinel-frontend:  # React app via Vite dev server (port 5173)
```

> CompreFace services are **not included** in Phase 1. Azure is the recognition
> brain. The Docker stack is significantly lighter as a result.

### Phase 2 (Full On-Prem, CompreFace)

```yaml
services:
  compreface-postgres:   # CompreFace internal DB (do not touch)
  compreface-admin:      # CompreFace management UI (port 8081)
  compreface-api:        # CompreFace REST API (port 8080)

  sentinel-db:           # Our PostgreSQL + pgvector (port 5432)
  sentinel-api:          # FastAPI — SENTINEL_RECOGNITION_PROVIDER=compreface
  sentinel-storage:      # MinIO (port 9000 / 9001)
  sentinel-frontend:     # React app (port 5173)
```

All services on a single Docker network: `sentinel-net`.

---

## 10. Implementation Order (Revised v1.1)

This is the sequence to follow. Do not skip ahead.

```
Phase 1 — Hybrid Foundation (Azure + Local Stack)

  Step 1:  Define FaceProvider ABC + AzureProvider implementation
  Step 2:  FastAPI skeleton — /enroll and /recognize wired to AzureProvider
  Step 3:  JWT / API Key auth middleware added to all routes
  Step 4:  PostgreSQL schema applied (Alembic migrations)
  Step 5:  Threshold routing + PostgreSQL writes
  Step 6:  React Sentry hook — MediaPipe quality gate (Yaw/Pitch < 15°, 800ms stable)
  Step 7:  MinIO image storage with TTL tag
  Step 8:  WebSocket real-time feed
  Step 9:  Dashboard — live feed, attendance table, enrollment form
  Step 10: Review queue UI + confirm/reject flow (re-enrolls via AzureProvider)
  Step 11: CSV export endpoint + download button

Phase 2 — Full On-Prem Migration (CompreFace)

  - Implement CompreFaceProvider (same FaceProvider interface)
  - Set SENTINEL_RECOGNITION_PROVIDER=compreface
  - Add CompreFace services to docker-compose.yml
  - Swap MinIO → S3 (one config line)
  - Add Redis for debounce (multi-camera)
  - Add HTTPS termination (nginx reverse proxy)
  - Add consent capture to enrollment form (GDPR)
```

---

## 11. Scalability — Migration Triggers

Do not upgrade pre-emptively. Upgrade only when the trigger is hit.

| Current Component | Migration Trigger | Upgraded Component |
|---|---|---|
| Azure Face API | Hardware upgraded (GPU available) | CompreFace (self-hosted) |
| In-memory TTL dict | 2+ instances OR 2+ cameras | Redis |
| pgvector | Enrolled identities exceed 10,000 | Milvus |
| FastAPI monolith | A single route becomes a bottleneck | Extract as microservice |
| MinIO (local) | Moving to cloud deployment | AWS S3 (one config line) |
| Single PostgreSQL | Read queries slow dashboard under load | Add read replica |

---

## 12. Privacy and Compliance Path

**Phase 1 (current):** No formal requirements. Images stored with 7-day TTL.

**Phase 2 preparation (built in now):**
- Raw footage never leaves the device running the browser. Only a 224×224 crop is
  sent over HTTPS.
- In Phase 1, the face chip is sent to Azure per-call. Azure does not retain images
  beyond the API call (verify with active Azure Data Privacy settings).
- Face chip images stored in MinIO have a short TTL and are purged automatically.
- Mathematical embeddings contain no pixel data. They are retained permanently but
  cannot reconstruct the original image.
- Identity deletion (`DELETE /api/v1/identities/{id}`) removes the identity from
  the active provider (Azure or CompreFace), cascades in PostgreSQL, and queues
  MinIO images for deletion.
- This architecture is GDPR-ready. When compliance is required, add consent capture
  to the enrollment form and enable the deletion endpoint for data subject requests.

---

## 13. Key Terms (Glossary)

| Term | Definition |
|---|---|
| Face chip | A 224×224 pixel crop of just the face region, extracted from the video frame |
| Embedding | A 128-dimensional floating-point vector representing a face mathematically |
| Centroid | The mean of multiple embeddings for one person — their "master profile" |
| Cosine similarity | The angle between two vectors. 1.0 = identical, 0.0 = unrelated |
| Temporal debounce | Suppression of duplicate log entries for the same person within a time window |
| Yaw / Pitch | Head rotation angles. Yaw = left/right, Pitch = up/down. Gate threshold: 15° |
| Subject / PersonId | Provider term for a named identity. Azure uses PersonId; CompreFace uses subject |
| Review queue | Items with similarity 0.60–0.84 that require operator confirmation |
| TTL | Time-to-live — automatic expiry applied to stored images |
| Strategy Pattern | Design pattern that swaps the recognition provider without changing route logic |
| FaceProvider | The abstract base class all recognition providers must implement |
| Hybrid mode | Phase 1 posture — local frontend/backend, cloud recognition (Azure) |

---

*Document version: 1.1 — Integrated Strategy Pattern & Azure Hybrid Pivot.*
*Updated: reflects provider-agnostic schema, revised Docker layout, and corrected implementation order.*
*Update this document whenever an architectural decision changes. Keep it in the repo root.*









<!-- graphify-links:start -->
## Graph Links

- [[graphify-out/wiki/index|Graphify Wiki]]
- [[graphify-out/GRAPH_REPORT|Graph Report]]
<!-- graphify-links:end -->
