# EntryLens — Master Build Plan

> **Purpose:** This is the execution document. It translates the architecture
> (ENTRYLENS_ARCHITECTURE.md) into concrete user stories, acceptance criteria,
> and a sprint-by-sprint build plan. Any LLM or developer picking up this project
> must read the architecture document first, then use this document to know exactly
> what to build next, in what order, and how to verify it is done.
>
> **Rule:** Never start a story without reading its acceptance criteria.
> Never mark a story done unless every criterion is met.

---

## 0. How to Read This Document

Each story follows this format:

```
### US-XXX — Story Title
**As a** [persona]
**I want to** [action]
**So that** [outcome]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2

**LLM Build Notes:**
- Specific implementation instructions for the AI assistant doing the work.

**Files Affected:**
- List of files to create or modify.

**Definition of Done:** One-line summary of what "complete" looks like.
```

Stories are grouped into Epics. Epics map directly to the Implementation Order
in the architecture document. Work through them in sequence. Do not skip epics.

---

## 1. Personas

| Persona | Who They Are |
|---|---|
| **Operator** | The admin user who manages the system — enrolls staff, reviews detections, exports reports |
| **Staff Member** | An enrolled person who walks past the camera and gets their attendance logged |
| **Visitor** | An unknown person detected by the camera — not enrolled |
| **Developer / LLM** | The builder implementing the system |
| **System** | The automated processes — debounce, TTL purge, WebSocket push |

---

## 2. Epic Overview

| Epic | Name | Phase | Stories |
|---|---|---|---|
| EP-01 | Infrastructure & Provider Foundation | 1 | US-001 – US-005 |
| EP-02 | Core Recognition Pipeline | 1 | US-006 – US-010 |
| EP-03 | Frontend Camera & Quality Gate | 1 | US-011 – US-014 |
| EP-04 | Dashboard & Real-Time Feed | 1 | US-015 – US-019 |
| EP-05 | Review Queue & Self-Improvement | 1 | US-020 – US-023 |
| EP-06 | Reporting & Export | 1 | US-024 – US-025 |
| EP-07 | Phase 2 Migration | 2 | US-026 – US-031 |

---

---

# EP-01 — Infrastructure & Provider Foundation

> **Goal:** Get the skeleton running. Docker stack up. Database migrated.
> Provider interface defined. No recognition logic yet — just plumbing.

---

### US-001 — Docker Compose Stack (Phase 1)

**As a** developer
**I want to** run a single `docker-compose up` command
**So that** all required services start together with correct networking

**Acceptance Criteria:**
- [ ] `docker-compose.yml` defines: `sentinel-db`, `sentinel-api`, `sentinel-storage`, `sentinel-frontend`
- [ ] All services share the `sentinel-net` Docker network
- [ ] `sentinel-db` runs PostgreSQL 15 with the `pgvector` extension available
- [ ] `sentinel-storage` runs MinIO, accessible on port 9000 (API) and 9001 (console)
- [ ] `sentinel-api` starts without error (can be a stub at this stage)
- [ ] `sentinel-frontend` serves the Vite dev server on port 5173
- [ ] Health checks defined for `sentinel-db` and `sentinel-api`
- [ ] `.env.example` file exists with all required environment variable keys documented

**LLM Build Notes:**
- CompreFace services are NOT included in Phase 1. Do not add them.
- Use `pgvector/pgvector:pg15` as the base image for `sentinel-db`.
- MinIO environment: set `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD` from `.env`.
- `sentinel-api` should depend_on `sentinel-db` with a health check condition.
- All secrets come from environment variables. No hardcoded credentials anywhere.

**Files Affected:**
- `docker-compose.yml` (create)
- `.env.example` (create)
- `.env` (create locally, never commit)
- `docker-compose.override.yml` (optional, for local dev overrides)

**Definition of Done:** `docker-compose up` brings all four services online with no errors.

---

### US-002 — PostgreSQL Schema & Migrations

**As a** developer
**I want to** apply the database schema via Alembic migrations
**So that** the database structure is version-controlled and reproducible

**Acceptance Criteria:**
- [ ] Alembic is configured with `alembic.ini` and `env.py` pointing to `sentinel-db`
- [ ] Initial migration creates all four tables: `identities`, `attendance_logs`, `review_queue`, `embeddings_mirror`
- [ ] `pgvector` extension is enabled via migration (`CREATE EXTENSION IF NOT EXISTS vector`)
- [ ] `embeddings_mirror` has the IVFFlat index on the `embedding` column
- [ ] `provider_subject_id` column exists on `identities` (not `compreface_subject_id`)
- [ ] Running `alembic upgrade head` completes without errors on a fresh database
- [ ] Running it twice is idempotent (no errors on re-run)

**LLM Build Notes:**
- Schema is fully specified in Section 6 of the architecture document. Use it verbatim.
- Use `gen_random_uuid()` for UUID primary keys (requires `pgcrypto` — enable it).
- The `embeddings_mirror` table is a local mirror. CompreFace/Azure manage the actual
  vectors internally. This table exists for custom local queries only.
- Column name is `provider_subject_id` — this is intentional and provider-agnostic.

**Files Affected:**
- `sentinel-api/alembic.ini` (create)
- `sentinel-api/alembic/env.py` (create)
- `sentinel-api/alembic/versions/001_initial_schema.py` (create)
- `sentinel-api/app/models.py` (create SQLAlchemy models matching schema)

**Definition of Done:** Fresh `docker-compose up` + `alembic upgrade head` produces all tables with correct columns and indexes.

---

### US-003 — FaceProvider Abstract Interface

**As a** developer
**I want to** define the `FaceProvider` abstract base class
**So that** all recognition logic is written against the interface, not a specific provider

**Acceptance Criteria:**
- [ ] `app/providers/base.py` defines `FaceProvider(ABC)` with two abstract async methods: `identify()` and `enroll()`
- [ ] `identify(image_bytes: bytes)` returns a typed response: `{ subject_id, similarity, bbox }`
- [ ] `enroll(user_id: str, images: list[bytes])` returns `{ enrolled: bool, face_count: int }`
- [ ] Both methods raise `NotImplementedError` if called on the base class directly
- [ ] Pydantic response models are defined for both return types
- [ ] A `ProviderResponse` and `EnrollResponse` dataclass/model exists in `app/providers/schemas.py`

**LLM Build Notes:**
- This file is the contract. Every other piece of recognition code depends on it.
- Do not implement any real API calls in this file. Abstract only.
- Use Python `abc.ABC` and `abc.abstractmethod`.
- Type hints are mandatory on all methods.

**Files Affected:**
- `sentinel-api/app/providers/__init__.py` (create)
- `sentinel-api/app/providers/base.py` (create)
- `sentinel-api/app/providers/schemas.py` (create)

**Definition of Done:** `from app.providers.base import FaceProvider` imports cleanly. Both abstract methods are present and typed.

---

### US-004 — AzureProvider Implementation

**As a** developer
**I want to** implement `AzureProvider` using the Azure Face API
**So that** the system can perform face recognition without a local GPU

**Acceptance Criteria:**
- [ ] `app/providers/azure_provider.py` implements `FaceProvider`
- [ ] `enroll()` creates a Person in the Azure PersonGroup, uploads each image, and calls `train`
- [ ] `identify()` detects the face in the image, then calls `identify` against the PersonGroup
- [ ] Returns similarity (confidence) and subject_id matching the `ProviderResponse` schema
- [ ] Azure credentials loaded from environment variables: `AZURE_FACE_API_KEY`, `AZURE_FACE_ENDPOINT`, `AZURE_PERSON_GROUP_ID`
- [ ] If Azure returns no face detected, `identify()` returns `{ subject_id: None, similarity: 0.0 }`
- [ ] HTTP errors from Azure are caught and re-raised as application-level exceptions with clear messages
- [ ] Provider is selected at app startup via `SENTINEL_RECOGNITION_PROVIDER=azure`

**LLM Build Notes:**
- Use `azure-ai-vision-face` SDK or direct HTTP calls with `httpx` (async).
- PersonGroup must be created before enrolling. Add a startup check: if PersonGroup
  does not exist, create it automatically.
- The `train` call after enrollment is async on Azure's side — poll until training
  is complete before returning `enrolled: true`.
- Never log the API key. Log the endpoint only.

**Files Affected:**
- `sentinel-api/app/providers/azure_provider.py` (create)
- `sentinel-api/requirements.txt` (add `azure-ai-vision-face` or `httpx`)
- `sentinel-api/app/main.py` (wire provider selection)

**Definition of Done:** With valid Azure credentials in `.env`, `AzureProvider().identify(image_bytes)` returns a valid `ProviderResponse`.

---

### US-005 — FastAPI App Skeleton with Auth

**As a** developer
**I want to** have a running FastAPI app with authentication middleware
**So that** all subsequent routes are protected from unauthorized access

**Acceptance Criteria:**
- [ ] FastAPI app starts and serves docs at `/docs`
- [ ] API key auth middleware reads `X-API-Key` header and validates against `SENTINEL_API_KEY` env var
- [ ] Unauthenticated requests to any `/api/v1/*` route return `401 Unauthorized`
- [ ] A `/health` endpoint exists and returns `{ status: "ok" }` without auth
- [ ] Pydantic settings class loads all env vars with type validation at startup
- [ ] App fails fast with a clear error if required env vars are missing

**LLM Build Notes:**
- Use FastAPI's dependency injection for auth: `Depends(verify_api_key)`.
- JWT is listed as Phase 2. For Phase 1, API key is sufficient.
- The health endpoint must be excluded from auth middleware.
- Use `pydantic-settings` for environment variable loading.
- CORS must be configured to allow requests from `http://localhost:5173` (Vite).

**Files Affected:**
- `sentinel-api/app/main.py` (create/update)
- `sentinel-api/app/auth.py` (create)
- `sentinel-api/app/config.py` (create — pydantic settings)
- `sentinel-api/requirements.txt` (update)

**Definition of Done:** `curl -H "X-API-Key: wrong" http://localhost:8000/api/v1/attendance` returns 401. `/health` returns 200.

---

---

# EP-02 — Core Recognition Pipeline

> **Goal:** The backend can receive a face image, route it through the provider,
> apply threshold logic, and write the result to PostgreSQL. No frontend yet.
> Test everything via curl or the `/docs` UI.

---

### US-006 — Enrollment Endpoint

**As an** operator
**I want to** enroll a new person by submitting their name, role, and photos
**So that** the system can recognize them when they appear on camera

**Acceptance Criteria:**
- [ ] `POST /api/v1/enroll` accepts `{ name, role, images: [base64 × up to 10] }`
- [ ] Request validated by Pydantic: name required, role must be `staff` or `visitor`, minimum 1 image
- [ ] `provider.enroll()` is called with the image bytes
- [ ] On success, a new row is inserted into the `identities` table
- [ ] Response: `{ enrolled: true, subject_id: <uuid>, provider_subject_id: <str>, face_count: <int> }`
- [ ] Enrolling the same `name` twice returns a meaningful error (not a DB crash)
- [ ] Endpoint requires API key auth

**LLM Build Notes:**
- Generate a UUID for `id` in the application layer before writing to DB.
- `provider_subject_id` is what comes back from Azure (their PersonId). Store it.
- Base64 images must be decoded to bytes before passing to `provider.enroll()`.
- Validate that each base64 string decodes to a valid image (check magic bytes or use Pillow).
- Maximum 10 images enforced at the Pydantic layer.

**Files Affected:**
- `sentinel-api/app/routes/enroll.py` (create)
- `sentinel-api/app/schemas/enroll.py` (create — request/response models)
- `sentinel-api/app/services/enroll_service.py` (create — business logic)
- `sentinel-api/app/main.py` (register router)

**Definition of Done:** `POST /api/v1/enroll` with 3 valid base64 face images creates an identity row in the DB and returns 200 with the subject_id.

---

### US-007 — Recognition Endpoint

**As a** system
**I want to** receive a face chip and return a recognition result
**So that** attendance can be logged in real time

**Acceptance Criteria:**
- [ ] `POST /api/v1/recognize` accepts `{ image: base64_string, camera_id?: string }`
- [ ] Image decoded, passed to `provider.identify()`
- [ ] Threshold routing applied per architecture Section 7:
  - `similarity > 0.85` → `AttendanceLog` with `status: confirmed`
  - `0.60–0.84` → `ReviewItem` with `status: pending_review`
  - `< 0.60` → `AttendanceLog` with `status: visitor`
- [ ] Thresholds read from environment variables, not hardcoded
- [ ] Result written to `attendance_logs` table
- [ ] Pending-review items also written to `review_queue` table
- [ ] Response returns the routing decision and log ID
- [ ] Endpoint requires API key auth

**LLM Build Notes:**
- Threshold values must come from `settings.HIGH_CONFIDENCE_THRESHOLD` and
  `settings.LOW_CONFIDENCE_THRESHOLD`. Never use literal numbers in this function.
- `camera_id` defaults to `"cam-01"` if not provided.
- The response shape: `{ status, identity_id, similarity, log_id, review_id? }`.
- Write to DB inside a transaction so both `attendance_logs` and `review_queue`
  succeed or fail together.

**Files Affected:**
- `sentinel-api/app/routes/recognize.py` (create)
- `sentinel-api/app/schemas/recognize.py` (create)
- `sentinel-api/app/services/recognition_service.py` (create)

**Definition of Done:** Posting a face image returns the correct routing status. A confirmed match creates an `attendance_logs` row. A mid-confidence match creates both an `attendance_logs` row and a `review_queue` row.

---

### US-008 — Temporal Debounce Layer

**As a** system
**I want to** suppress duplicate attendance logs for the same person within 5 minutes
**So that** a person standing in front of the camera doesn't generate hundreds of log entries

**Acceptance Criteria:**
- [ ] An in-memory `dict` stores `{ identity_id: last_seen_timestamp }` in FastAPI process memory
- [ ] Before writing a new `AttendanceLog`, check if `identity_id` was seen within `SENTINEL_DEBOUNCE_WINDOW_SECONDS`
- [ ] If within window: update the "active" timestamp but do NOT create a new log entry
- [ ] If outside window: create a new log entry and update the timestamp
- [ ] Debounce only applies to `confirmed` matches. `visitor` and `pending_review` always log.
- [ ] Window duration read from `SENTINEL_DEBOUNCE_WINDOW_SECONDS` env var (default 300)

**LLM Build Notes:**
- Store the debounce dict as a module-level singleton in `app/services/debounce.py`.
- This is intentionally simple. Do not use Redis, do not use a database table.
  Redis is added in Phase 2 when multi-instance is required.
- Thread safety: FastAPI with async is single-threaded per worker. A plain dict is safe.
- The dict key is `identity_id` (UUID string). Value is a `datetime` object.

**Files Affected:**
- `sentinel-api/app/services/debounce.py` (create)
- `sentinel-api/app/services/recognition_service.py` (update — integrate debounce check)

**Definition of Done:** Sending the same face twice within 5 minutes produces only one `attendance_logs` entry. Sending it 6 minutes apart produces two entries.

---

### US-009 — MinIO Image Storage with TTL

**As a** system
**I want to** store each face chip image in MinIO with a 7-day expiry tag
**So that** raw biometric images are automatically purged for privacy compliance

**Acceptance Criteria:**
- [ ] After each recognition event, the face chip is uploaded to MinIO
- [ ] Object key format: `face-chips/{date}/{log_id}.jpg`
- [ ] MinIO lifecycle policy configured to delete objects tagged `ttl=7d` after 7 days
- [ ] `image_key` column in `attendance_logs` is populated with the MinIO object key
- [ ] If MinIO upload fails, the recognition result is still written to DB (non-blocking failure)
- [ ] MinIO bucket name configurable via `MINIO_BUCKET_NAME` env var
- [ ] MinIO connection configured from `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`

**LLM Build Notes:**
- Use `miniopy-async` or `boto3` (S3-compatible) for MinIO client.
- The bucket must be created on first startup if it doesn't exist. Add a startup check.
- TTL is implemented via MinIO object lifecycle rules, not a cron job.
  Set the rule once at bucket creation.
- Wrap the MinIO upload in a `try/except`. Log the error but do not raise it.
  The face chip is not critical path — the DB write is.
- For confirmed identities in the review flow, TTL can be extended or removed.

**Files Affected:**
- `sentinel-api/app/services/storage_service.py` (create)
- `sentinel-api/app/services/recognition_service.py` (update — call storage after DB write)
- `sentinel-api/app/main.py` (add bucket init on startup)

**Definition of Done:** After a recognition event, the face chip appears in MinIO under the correct key, and the `image_key` column in `attendance_logs` is populated.

---

### US-010 — Attendance & Identity Read Endpoints

**As an** operator
**I want to** query attendance logs and enrolled identities via the API
**So that** the dashboard and export features have data to display

**Acceptance Criteria:**
- [ ] `GET /api/v1/attendance` returns paginated list of attendance logs
- [ ] Supports query params: `?date=YYYY-MM-DD`, `?status=confirmed|visitor|pending_review`, `?limit=50&offset=0`
- [ ] `GET /api/v1/identities` returns list of all enrolled identities
- [ ] `DELETE /api/v1/identities/{id}` removes identity from: provider (Azure/CompreFace), `identities` table (cascades to logs), MinIO images queued for deletion
- [ ] All endpoints require API key auth
- [ ] Responses are Pydantic-serialized (no raw SQLAlchemy objects returned)

**LLM Build Notes:**
- Use SQLAlchemy async session for all DB queries.
- `DELETE /api/v1/identities/{id}` must call `provider.delete_subject(provider_subject_id)`
  before the DB delete. Add `delete_subject()` to the `FaceProvider` interface.
- If provider deletion fails, do not proceed with DB deletion. Return 500 with explanation.
- Paginate all list endpoints. Default limit is 50. Maximum is 200.

**Files Affected:**
- `sentinel-api/app/routes/attendance.py` (create)
- `sentinel-api/app/routes/identities.py` (create)
- `sentinel-api/app/providers/base.py` (add `delete_subject` abstract method)
- `sentinel-api/app/providers/azure_provider.py` (implement `delete_subject`)

**Definition of Done:** `GET /api/v1/attendance` returns logs. `DELETE /api/v1/identities/{id}` removes the identity from both Azure and the local DB.

---

---

# EP-03 — Frontend Camera & Quality Gate

> **Goal:** The browser opens the camera, MediaPipe evaluates every frame,
> and only clean forward-facing stable frames are sent to the API.
> No dashboard UI yet — just the capture and POST loop.

---

### US-011 — React Project Setup

**As a** developer
**I want to** have a React + Vite project configured and running
**So that** all frontend stories have a working base to build on

**Acceptance Criteria:**
- [ ] Vite + React project initialized in `sentinel-frontend/`
- [ ] `@mediapipe/tasks-vision` package installed
- [ ] Axios or `fetch` configured with base URL pointing to `http://localhost:8000`
- [ ] API key injected from `VITE_API_KEY` environment variable (`.env.local`)
- [ ] App renders a placeholder page at `http://localhost:5173`
- [ ] Dockerfile builds the frontend for production (Vite build + nginx serve)

**LLM Build Notes:**
- Use Vite with the React template: `npm create vite@latest sentinel-frontend -- --template react`
- Do not use Create React App.
- All API calls must include the `X-API-Key` header automatically via an Axios instance
  or a custom fetch wrapper. Set this up once in `src/api/client.js`.
- `.env.local` is gitignored. `.env.example` is committed.

**Files Affected:**
- `sentinel-frontend/` (create entire directory)
- `sentinel-frontend/src/api/client.js` (create — configured API client)
- `sentinel-frontend/.env.example` (create)
- `sentinel-frontend/Dockerfile` (create)

**Definition of Done:** `npm run dev` starts Vite on port 5173 with no errors. API client is importable.

---

### US-012 — Camera Access & Video Stream

**As a** system
**I want to** open the device camera and display the live feed in the browser
**So that** subsequent hooks can process video frames

**Acceptance Criteria:**
- [ ] Browser requests camera permission on page load
- [ ] Live camera feed displays in a `<video>` element
- [ ] If camera permission is denied, a clear error message is shown (not a blank screen)
- [ ] Camera selection defaults to the environment-facing (front) camera
- [ ] Video stream is accessible to downstream canvas operations
- [ ] A `useCamera` hook encapsulates all camera logic

**LLM Build Notes:**
- Use `navigator.mediaDevices.getUserMedia({ video: true })`.
- Attach the stream to a `videoRef` via `video.srcObject = stream`.
- The `useCamera` hook returns `{ videoRef, isReady, error }`.
- `isReady` is true only after the video's `loadeddata` event fires.
- Expose `videoRef` to parent components — MediaPipe will read from it.

**Files Affected:**
- `sentinel-frontend/src/hooks/useCamera.js` (create)
- `sentinel-frontend/src/components/CameraView.jsx` (create)

**Definition of Done:** Opening the app in Chrome shows the live camera feed. Denying permission shows an error message.

---

### US-013 — MediaPipe Quality Gate Hook

**As a** system
**I want to** evaluate every camera frame using MediaPipe Face Landmarker
**So that** only high-quality, forward-facing, stable frames are sent to the API

**Acceptance Criteria:**
- [ ] MediaPipe `FaceLandmarker` initialized with WASM backend in the browser
- [ ] Every frame evaluated for: face presence, Yaw angle, Pitch angle
- [ ] Frame is rejected (not sent) if: no face detected, `|Yaw| > 15°`, or `|Pitch| > 15°`
- [ ] Stability timer: face must pass the gate for 800ms continuously before triggering
- [ ] Timer resets if face moves out of gate range during the 800ms window
- [ ] On stable valid frame: 224×224 face crop extracted from the video frame to a canvas
- [ ] Cropped image exported as base64 JPEG
- [ ] Hook exposes: `{ isGateOpen, headPose, faceDetected, lastCrop }`

**LLM Build Notes:**
- MediaPipe model file (`face_landmarker.task`) must be served as a static asset.
  Download it once and place it in `public/models/`.
- Use `FaceLandmarker.FACE_LANDMARKS_TESSELATION` for head pose estimation.
- Yaw/Pitch can be computed from the facial landmark geometry — use the nose tip and
  eye corners as reference points. Alternatively use MediaPipe's built-in
  `FaceLandmarkerResult.facialTransformationMatrixes` if available.
- The 800ms timer is a `useRef` holding a `setTimeout` ID. Reset it on every failed frame.
- Crop: use the detected face bounding box, expand by 20% padding, draw to a 224×224 canvas.
- This is the most complex hook in the frontend. Write it carefully and test it visually.

**Files Affected:**
- `sentinel-frontend/src/hooks/useMediaPipe.js` (create)
- `sentinel-frontend/public/models/face_landmarker.task` (download and place here)

**Definition of Done:** Holding a face straight at the camera for 800ms causes `lastCrop` to be populated with a 224×224 base64 JPEG. Turning the head away resets the timer.

---

### US-014 — Recognition POST Loop

**As a** system
**I want to** automatically POST valid face crops to the recognition API
**So that** attendance is logged without operator intervention

**Acceptance Criteria:**
- [ ] When `useMediaPipe` fires a stable crop, it is immediately POSTed to `POST /api/v1/recognize`
- [ ] The POST includes `{ image: base64_jpeg, camera_id: "cam-01" }`
- [ ] API response is stored in component state
- [ ] If the API returns an error, it is logged to console (not shown to the user)
- [ ] No UI interaction required — the loop runs automatically
- [ ] A `useRecognitionLoop` hook encapsulates this behavior
- [ ] Hook exposes `{ lastResult, isPosting, error }`

**LLM Build Notes:**
- The loop is triggered by `lastCrop` changing (useEffect dependency).
- Prevent concurrent POSTs: if `isPosting` is true, skip the new crop.
- This is the integration point between the MediaPipe hook and the API.
- `camera_id` should come from a config constant, not be hardcoded inline.

**Files Affected:**
- `sentinel-frontend/src/hooks/useRecognitionLoop.js` (create)
- `sentinel-frontend/src/api/recognize.js` (create — API call wrapper)

**Definition of Done:** Walking in front of the camera results in a network POST to the API visible in browser DevTools, and the response appears in `lastResult`.

---

---

# EP-04 — Dashboard & Real-Time Feed

> **Goal:** The operator has a working dashboard: live recognition feed,
> enrollment form, and attendance history table.

---

### US-015 — WebSocket Real-Time Feed (Backend)

**As a** system
**I want to** push recognition events to all connected dashboard clients via WebSocket
**So that** the dashboard updates instantly without polling

**Acceptance Criteria:**
- [ ] `WS /ws/live` endpoint accepts WebSocket connections
- [ ] After every recognition event (confirmed, visitor, pending_review), a JSON event is broadcast to all connected clients
- [ ] Event shape: `{ type: "recognition", status, identity_name?, similarity, detected_at, log_id }`
- [ ] Clients that disconnect are removed from the connection pool cleanly
- [ ] Multiple simultaneous clients are supported
- [ ] WebSocket endpoint does NOT require auth (dashboard connects before login context is available)

**LLM Build Notes:**
- Use FastAPI's built-in `WebSocket` support.
- Maintain a `Set` of active `WebSocket` connections as a module-level singleton
  in `app/services/websocket_manager.py`.
- The `recognition_service` calls `websocket_manager.broadcast(event)` after
  writing to the DB.
- Broadcast is fire-and-forget (`asyncio.create_task`). Do not await it in the
  recognition hot path.
- Handle `WebSocketDisconnect` exception to remove stale connections.

**Files Affected:**
- `sentinel-api/app/services/websocket_manager.py` (create)
- `sentinel-api/app/routes/ws.py` (create)
- `sentinel-api/app/services/recognition_service.py` (update — call broadcast)
- `sentinel-api/app/main.py` (register WebSocket router)

**Definition of Done:** Open two browser tabs pointing to `/docs`. Connect to the WebSocket. POST a recognition event via curl. Both tabs receive the event within 1 second.

---

### US-016 — WebSocket Live Feed (Frontend)

**As an** operator
**I want to** see recognition events appear on the dashboard in real time
**So that** I can monitor who is entering without refreshing the page

**Acceptance Criteria:**
- [ ] Dashboard subscribes to `ws://localhost:8000/ws/live` on mount
- [ ] Incoming events are prepended to a live feed list (newest at top)
- [ ] Each event shows: name (or "Visitor"), status badge, similarity score, timestamp
- [ ] Status badges are color-coded: green (confirmed), orange (pending_review), gray (visitor)
- [ ] Feed is capped at the last 50 events in memory
- [ ] WebSocket reconnects automatically if disconnected (with exponential backoff)
- [ ] A `useWebSocket` hook encapsulates connection management

**LLM Build Notes:**
- Use the native browser `WebSocket` API, not a library.
- Reconnect logic: attempt reconnect after 1s, 2s, 4s, 8s, cap at 30s.
- Display a connection status indicator (green dot = connected, red = disconnected).
- `useWebSocket` returns `{ events, connectionStatus }`.

**Files Affected:**
- `sentinel-frontend/src/hooks/useWebSocket.js` (create)
- `sentinel-frontend/src/components/LiveFeed.jsx` (create)

**Definition of Done:** Recognition events appear on the dashboard within 1 second of the camera detecting a face, with no manual refresh.

---

### US-017 — Enrollment Form UI

**As an** operator
**I want to** enroll a new staff member through the dashboard
**So that** I don't need to use curl or the API docs to add people

**Acceptance Criteria:**
- [ ] Enrollment form accepts: Name (text), Role (dropdown: staff/visitor), Photos (file upload, multiple, max 10)
- [ ] Photo previews displayed before submission
- [ ] Submit button disabled until at least 1 photo and a name are provided
- [ ] On success: form resets, success message shown, identity list refreshes
- [ ] On error: error message shown with the API error detail
- [ ] Image files are converted to base64 before POSTing
- [ ] Loading state shown during submission

**LLM Build Notes:**
- File input: `<input type="file" accept="image/*" multiple />`.
- Convert files to base64 using `FileReader` API.
- The form submits to `POST /api/v1/enroll`.
- Do not use a `<form>` element with `action`. Use a button `onClick` handler with
  controlled state.

**Files Affected:**
- `sentinel-frontend/src/components/EnrollmentForm.jsx` (create)
- `sentinel-frontend/src/api/enroll.js` (create)

**Definition of Done:** Filling the form and clicking Submit creates a new identity visible in the identity list. Submitting without a name shows a validation error before the API is called.

---

### US-018 — Attendance History Table

**As an** operator
**I want to** view a filterable table of all attendance events
**So that** I can audit who entered on a given day

**Acceptance Criteria:**
- [ ] Table shows: Name, Role, Status, Similarity, Camera, Timestamp
- [ ] Filterable by: date (date picker), status (dropdown)
- [ ] Paginated: 50 rows per page with next/previous controls
- [ ] Status column uses color-coded badges (same as live feed)
- [ ] Rows with `status: pending_review` have a "Review" button that links to the review queue
- [ ] Table refreshes when filters change
- [ ] Empty state shown when no records match filters

**LLM Build Notes:**
- Data fetched from `GET /api/v1/attendance?date=&status=&limit=50&offset=0`.
- Use `useEffect` with filter values as dependencies to re-fetch on change.
- Timestamps displayed in local timezone using `Intl.DateTimeFormat`.

**Files Affected:**
- `sentinel-frontend/src/components/AttendanceTable.jsx` (create)
- `sentinel-frontend/src/api/attendance.js` (create)

**Definition of Done:** The table shows historical records. Changing the date filter updates the table. Pagination works.

---

### US-019 — Dashboard Layout & Navigation

**As an** operator
**I want to** navigate between the live feed, attendance history, and enrollment form
**So that** I can use all features from a single interface

**Acceptance Criteria:**
- [ ] Sidebar or top navigation with links: Live Feed, Attendance, Enroll, Review Queue
- [ ] Active route highlighted in navigation
- [ ] Camera feed and live event list visible simultaneously on the Live Feed page
- [ ] Responsive layout (works on 1080p desktop — mobile not required for Phase 1)
- [ ] System connection status (API + WebSocket) shown in the header

**LLM Build Notes:**
- Use React Router v6 for navigation.
- Layout: fixed sidebar (240px) + main content area.
- No external CSS framework required — use plain CSS modules or inline styles.
  Keep it functional, not pretty. Aesthetics are Phase 2.

**Files Affected:**
- `sentinel-frontend/src/App.jsx` (update — add router)
- `sentinel-frontend/src/components/Layout.jsx` (create)
- `sentinel-frontend/src/components/Sidebar.jsx` (create)
- `sentinel-frontend/src/pages/LivePage.jsx` (create)
- `sentinel-frontend/src/pages/AttendancePage.jsx` (create)
- `sentinel-frontend/src/pages/EnrollPage.jsx` (create)

**Definition of Done:** Clicking each nav item loads the correct page. Browser back/forward works. Camera feed is running on the Live Feed page.

---

---

# EP-05 — Review Queue & Self-Improvement Loop

> **Goal:** Operators can review uncertain detections, confirm or reject them,
> and confirmed detections automatically improve the recognition model.

---

### US-020 — Review Queue API Endpoints

**As an** operator
**I want to** fetch pending review items and act on them via the API
**So that** the review UI has data to display and actions to call

**Acceptance Criteria:**
- [ ] `GET /api/v1/review` returns all items with `status: pending`, sorted by `created_at` DESC
- [ ] Each item includes: similarity, face chip image URL (MinIO pre-signed), candidate identity name, timestamp
- [ ] `POST /api/v1/review/{id}/confirm` marks item as confirmed and re-enrolls the face chip via `provider.enroll()`
- [ ] `POST /api/v1/review/{id}/reject` marks item as rejected and creates a `visitor` attendance log
- [ ] Both actions update `review_queue.status` and `reviewed_at`
- [ ] Acting on an already-resolved item returns `409 Conflict`
- [ ] All endpoints require API key auth

**LLM Build Notes:**
- MinIO image URLs must be pre-signed with a short expiry (e.g. 1 hour) so the
  dashboard can display them without exposing credentials.
- The confirm flow: fetch the image from MinIO, decode it, call `provider.enroll()`.
  This adds a new sample for that subject — improving future accuracy.
- Wrap confirm/reject in a transaction: update `review_queue` and `attendance_logs`
  atomically.

**Files Affected:**
- `sentinel-api/app/routes/review.py` (create)
- `sentinel-api/app/services/review_service.py` (create)
- `sentinel-api/app/schemas/review.py` (create)

**Definition of Done:** `GET /api/v1/review` returns pending items with pre-signed image URLs. Confirming an item calls `provider.enroll()` and marks the item resolved.

---

### US-021 — Review Queue UI

**As an** operator
**I want to** see uncertain detections and confirm or reject them from the dashboard
**So that** ambiguous matches are resolved and the system improves over time

**Acceptance Criteria:**
- [ ] Review Queue page lists all pending items
- [ ] Each card shows: face chip image, candidate name, similarity score, timestamp
- [ ] "Confirm Match" and "Reject" buttons on each card
- [ ] Confirming removes the card from the list and shows a success toast
- [ ] Rejecting removes the card and shows a success toast
- [ ] Empty state shown when queue is empty: "No pending reviews"
- [ ] Queue count shown in the sidebar nav badge

**LLM Build Notes:**
- Face chip image rendered from the pre-signed MinIO URL returned by the API.
- Optimistic UI: remove the card immediately on button click, then call the API.
  On API error, restore the card and show an error.
- Nav badge: fetch `GET /api/v1/review` count on mount and after each action.

**Files Affected:**
- `sentinel-frontend/src/pages/ReviewPage.jsx` (create)
- `sentinel-frontend/src/components/ReviewCard.jsx` (create)
- `sentinel-frontend/src/api/review.js` (create)

**Definition of Done:** Pending items appear with their face chip image. Clicking Confirm calls the API and removes the card. The sidebar badge reflects the correct pending count.

---

### US-022 — Self-Improvement Re-Enrollment

**As a** system
**I want to** automatically re-enroll confirmed review items as new training samples
**So that** the recognition model improves with each operator correction

**Acceptance Criteria:**
- [ ] On `POST /api/v1/review/{id}/confirm`, the face chip is retrieved from MinIO
- [ ] `provider.enroll()` is called with the existing `provider_subject_id` and the single image
- [ ] The `embeddings_mirror` table is updated with the new embedding (if CompreFace returns it)
- [ ] After re-enrollment, `review_queue.status` set to `confirmed` and `reviewed_at` populated
- [ ] The associated `attendance_logs` entry updated from `pending_review` to `confirmed`
- [ ] If re-enrollment fails, the review item remains `pending` and the error is returned to the caller

**LLM Build Notes:**
- Azure re-enrollment: call `AddPersonFace` with the additional image, then retrain the PersonGroup.
- CompreFace re-enrollment: POST the image to the existing subject endpoint.
- This is the self-improvement loop described in architecture Section 5c.
- Do not re-enroll if the image has already been purged from MinIO (TTL expired).
  Check `image_key` is not null before proceeding.

**Files Affected:**
- `sentinel-api/app/services/review_service.py` (update — add re-enroll logic)
- `sentinel-api/app/providers/azure_provider.py` (update — handle re-enrollment to existing subject)

**Definition of Done:** After confirming a review item, the subject in Azure has one additional face sample. Future detections of that person at the same angle score higher.

---

### US-023 — Image TTL Extension on Confirm

**As a** system
**I want to** extend the TTL on face chips that have been confirmed by an operator
**So that** images of known staff are retained longer for audit while visitor images are purged quickly

**Acceptance Criteria:**
- [ ] On confirm: MinIO object tag updated from `ttl=7d` to `ttl=permanent` (or TTL tag removed)
- [ ] On reject: object TTL remains at 7 days (no change)
- [ ] If MinIO tag update fails, the confirm action still succeeds (non-blocking)

**LLM Build Notes:**
- MinIO object tagging: use `put_object_tags()` from the boto3/miniopy client.
- "Permanent" means removing the lifecycle rule tag. The object will not be purged.
- This is a background operation. Wrap in `asyncio.create_task()` — do not block the response.

**Files Affected:**
- `sentinel-api/app/services/storage_service.py` (update — add `update_ttl` method)
- `sentinel-api/app/services/review_service.py` (update — call `update_ttl` on confirm)

**Definition of Done:** After confirming a review item, the MinIO object no longer has the 7-day TTL tag.

---

---

# EP-06 — Reporting & Export

> **Goal:** Operators can export attendance data as CSV for external use.

---

### US-024 — CSV Export Endpoint

**As an** operator
**I want to** export attendance logs as a CSV file
**So that** I can import the data into spreadsheets or HR systems

**Acceptance Criteria:**
- [ ] `GET /api/v1/export/csv` returns a downloadable CSV file
- [ ] Supports optional query params: `?date_from=`, `?date_to=`, `?status=`
- [ ] CSV columns: `id, name, role, status, similarity, camera_id, detected_at`
- [ ] Response headers set correctly: `Content-Type: text/csv`, `Content-Disposition: attachment; filename=attendance_YYYY-MM-DD.csv`
- [ ] Empty export (no records) returns a valid CSV with headers only
- [ ] Requires API key auth

**LLM Build Notes:**
- Use Python's built-in `csv` module and return a `StreamingResponse` from FastAPI.
- Do not load all records into memory if the date range is large. Use a DB cursor/stream.
- `detected_at` exported in ISO 8601 format (UTC).

**Files Affected:**
- `sentinel-api/app/routes/export.py` (create)
- `sentinel-api/app/services/export_service.py` (create)

**Definition of Done:** `GET /api/v1/export/csv` returns a valid `.csv` file that opens correctly in Excel.

---

### US-025 — CSV Download Button (Frontend)

**As an** operator
**I want to** download the attendance CSV from the dashboard with one click
**So that** I don't need to use the API directly

**Acceptance Criteria:**
- [ ] "Export CSV" button on the Attendance page
- [ ] Clicking it triggers a file download of the CSV
- [ ] Date filters from the attendance table are passed to the export request
- [ ] Loading state shown during download
- [ ] Button disabled while download is in progress

**LLM Build Notes:**
- Implement the download by fetching the CSV as a `blob` and creating a temporary `<a>` element with `href=URL.createObjectURL(blob)` and triggering `.click()`.
- Pass the currently active date filters to the export endpoint as query params.

**Files Affected:**
- `sentinel-frontend/src/components/AttendanceTable.jsx` (update — add export button)
- `sentinel-frontend/src/api/export.js` (create)

**Definition of Done:** Clicking "Export CSV" on the Attendance page downloads a `.csv` file with the filtered records.

---

---

# EP-07 — Phase 2 Migration

> **Goal:** When hardware is upgraded, switch from Azure to CompreFace with
> minimal disruption. All stories below are deferred until Phase 2 is triggered.
> Do not implement these in Phase 1.

---

### US-026 — CompreFaceProvider Implementation

**As a** developer
**I want to** implement `CompreFaceProvider` using the same `FaceProvider` interface
**So that** switching from Azure to CompreFace requires only an environment variable change

**Acceptance Criteria:**
- [ ] `app/providers/compreface_provider.py` implements all methods of `FaceProvider`
- [ ] `enroll()` POSTs images to CompreFace `/api/v1/recognition/faces`
- [ ] `identify()` POSTs image to CompreFace `/api/v1/recognition/recognize`
- [ ] `delete_subject()` calls CompreFace subject deletion endpoint
- [ ] `SENTINEL_RECOGNITION_PROVIDER=compreface` activates this provider at startup
- [ ] No changes required to any route handler or service when switching providers

**Files Affected:**
- `sentinel-api/app/providers/compreface_provider.py` (create)

**Definition of Done:** Setting `SENTINEL_RECOGNITION_PROVIDER=compreface` and restarting the API switches all recognition to CompreFace with no code changes.

---

### US-027 — CompreFace Docker Services

**As a** developer
**I want to** add CompreFace to the Docker Compose stack
**So that** recognition runs fully on-premises

**Acceptance Criteria:**
- [ ] `docker-compose.yml` updated with: `compreface-postgres`, `compreface-admin`, `compreface-api`
- [ ] CompreFace services on the same `sentinel-net` network
- [ ] `sentinel-api` can reach CompreFace at `http://compreface-api:8080`
- [ ] Phase 1 services continue to work unchanged

**Files Affected:**
- `docker-compose.yml` (update)

**Definition of Done:** `docker-compose up` starts all services including CompreFace. The CompreFace admin UI is accessible at `http://localhost:8081`.

---

### US-028 — JWT Authentication

**As a** developer
**I want to** replace API key auth with JWT
**So that** the system supports user sessions and per-user audit logging

**Acceptance Criteria:**
- [ ] `POST /api/v1/auth/login` accepts username/password, returns JWT access token
- [ ] JWT validated on all protected endpoints
- [ ] Token expiry configurable via `JWT_EXPIRY_MINUTES` env var
- [ ] API key auth deprecated (removed or kept as fallback for machine clients)

**Files Affected:**
- `sentinel-api/app/auth.py` (update)
- `sentinel-api/app/routes/auth.py` (create)

**Definition of Done:** Dashboard login form issues a JWT. Expired tokens return 401.

---

### US-029 — Redis Debounce (Multi-Camera)

**As a** system
**I want to** move the debounce state from in-memory to Redis
**So that** multiple API instances or cameras share a consistent debounce window

**Acceptance Criteria:**
- [ ] Redis service added to Docker Compose
- [ ] `debounce.py` updated to use Redis `SET identity_id timestamp EX window_seconds`
- [ ] Behavior identical to in-memory version from the outside
- [ ] `REDIS_URL` env var configures the connection

**Files Affected:**
- `docker-compose.yml` (add Redis)
- `sentinel-api/app/services/debounce.py` (update)

**Definition of Done:** Two instances of `sentinel-api` running simultaneously share the same debounce state via Redis.

---

### US-030 — HTTPS & Nginx Reverse Proxy

**As a** developer
**I want to** add an nginx reverse proxy with TLS termination
**So that** the system is production-ready for on-prem deployment

**Acceptance Criteria:**
- [ ] nginx service added to Docker Compose
- [ ] HTTPS on port 443, HTTP redirects to HTTPS
- [ ] nginx proxies `/api/` to `sentinel-api:8000` and `/` to `sentinel-frontend:5173`
- [ ] TLS certificate configurable (self-signed for on-prem, Let's Encrypt path documented)

**Files Affected:**
- `docker-compose.yml` (add nginx)
- `nginx/nginx.conf` (create)
- `nginx/certs/` (gitignored — certs go here)

**Definition of Done:** All traffic goes through HTTPS. HTTP requests redirect automatically.

---

### US-031 — GDPR Consent Capture

**As an** operator
**I want to** capture consent during enrollment
**So that** the system is compliant with GDPR when required

**Acceptance Criteria:**
- [ ] Enrollment form includes a consent checkbox with the biometric data usage statement
- [ ] Consent cannot be bypassed — Submit button disabled until checked
- [ ] `consent_given_at` timestamp stored on the `identities` table
- [ ] `DELETE /api/v1/identities/{id}` documented as the right-to-erasure endpoint

**Files Affected:**
- `sentinel-api/alembic/versions/002_add_consent.py` (create)
- `sentinel-api/app/models.py` (update — add `consent_given_at`)
- `sentinel-frontend/src/components/EnrollmentForm.jsx` (update — add consent checkbox)

**Definition of Done:** No identity can be enrolled without the consent checkbox checked. The timestamp is stored in the database.

---

---

## 3. Sprint Plan

> Each sprint is approximately 1 week of focused solo development with AI assistance.
> Stories marked ⚠️ are blockers — the next sprint cannot start until they are done.

| Sprint | Stories | Goal |
|---|---|---|
| **Sprint 1** | US-001 ⚠️, US-002 ⚠️, US-003 ⚠️ | Docker up, DB migrated, provider interface defined |
| **Sprint 2** | US-004 ⚠️, US-005 ⚠️ | Azure wired, FastAPI protected, health check green |
| **Sprint 3** | US-006, US-007, US-008 | Enroll and recognize endpoints working end-to-end |
| **Sprint 4** | US-009, US-010 | MinIO storage, attendance and identity read endpoints |
| **Sprint 5** | US-011, US-012, US-013 ⚠️ | React up, camera live, MediaPipe gate working |
| **Sprint 6** | US-014, US-015, US-016 | Recognition loop posting, WebSocket live feed connected |
| **Sprint 7** | US-017, US-018, US-019 | Full dashboard: enrollment form, attendance table, navigation |
| **Sprint 8** | US-020, US-021, US-022, US-023 | Review queue end-to-end |
| **Sprint 9** | US-024, US-025 | CSV export |
| **Phase 2** | US-026 – US-031 | CompreFace migration, JWT, Redis, HTTPS, GDPR |

---

## 4. File Structure

```
sentinel-vision/
├── docker-compose.yml
├── .env.example
├── ENTRYLENS_ARCHITECTURE.md     ← Architecture source of truth
├── ENTRYLENS_MASTER_PLAN.md      ← This document
│
├── sentinel-api/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   └── app/
│       ├── main.py                     ← FastAPI app + provider injection
│       ├── config.py                   ← Pydantic settings
│       ├── auth.py                     ← API key / JWT middleware
│       ├── models.py                   ← SQLAlchemy models
│       ├── providers/
│       │   ├── __init__.py
│       │   ├── base.py                 ← FaceProvider ABC
│       │   ├── schemas.py              ← ProviderResponse, EnrollResponse
│       │   ├── azure_provider.py       ← Phase 1
│       │   └── compreface_provider.py  ← Phase 2
│       ├── routes/
│       │   ├── enroll.py
│       │   ├── recognize.py
│       │   ├── attendance.py
│       │   ├── identities.py
│       │   ├── review.py
│       │   ├── export.py
│       │   └── ws.py
│       ├── services/
│       │   ├── enroll_service.py
│       │   ├── recognition_service.py
│       │   ├── review_service.py
│       │   ├── export_service.py
│       │   ├── storage_service.py
│       │   ├── debounce.py
│       │   └── websocket_manager.py
│       └── schemas/
│           ├── enroll.py
│           ├── recognize.py
│           └── review.py
│
└── sentinel-frontend/
    ├── Dockerfile
    ├── .env.example
    ├── public/
    │   └── models/
    │       └── face_landmarker.task
    └── src/
        ├── App.jsx
        ├── api/
        │   ├── client.js               ← Axios instance with API key
        │   ├── enroll.js
        │   ├── recognize.js
        │   ├── attendance.js
        │   ├── review.js
        │   └── export.js
        ├── hooks/
        │   ├── useCamera.js
        │   ├── useMediaPipe.js
        │   ├── useRecognitionLoop.js
        │   └── useWebSocket.js
        ├── components/
        │   ├── Layout.jsx
        │   ├── Sidebar.jsx
        │   ├── CameraView.jsx
        │   ├── LiveFeed.jsx
        │   ├── AttendanceTable.jsx
        │   ├── EnrollmentForm.jsx
        │   └── ReviewCard.jsx
        └── pages/
            ├── LivePage.jsx
            ├── AttendancePage.jsx
            ├── EnrollPage.jsx
            └── ReviewPage.jsx
```

---

## 5. LLM Working Rules

> Any AI assistant working on this project must follow these rules without exception.

1. **Read the architecture document first.** Before writing any code, read `ENTRYLENS_ARCHITECTURE.md` in full.

2. **Follow the sprint order.** Do not implement stories from Sprint 4 if Sprint 2 is incomplete. Skipping ahead creates broken dependencies.

3. **Never call a provider directly from a route.** All recognition and enrollment calls go through `provider.identify()` or `provider.enroll()`. The route handler does not know which provider is active.

4. **Never hardcode threshold values.** `0.85`, `0.60`, `300` — these must always come from `settings.*`. If you see a magic number in recognition logic, it is a bug.

5. **One file = one responsibility.** Routes handle HTTP. Services handle business logic. Providers handle external APIs. Do not mix these layers.

6. **Handle failures gracefully.** MinIO failures must not crash recognition. Provider failures must return a clear HTTP error. DB failures must roll back the transaction.

7. **Update this document when things change.** If a story's acceptance criteria change during implementation, update the story here before changing the code.

8. **Mark stories done only when all criteria are met.** "Mostly works" is not done. A checkbox is either ticked or it isn't.

---

*Document version: 1.0*
*Companion to: ENTRYLENS_ARCHITECTURE.md v1.1*
*Keep both documents in the repo root. Update together.*

