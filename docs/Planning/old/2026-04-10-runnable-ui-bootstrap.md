# Runnable UI Bootstrap Plan

## Task Summary

Create the initial EntryLens project structure and implementation sequence needed to reach a local runnable state where:

- the stack can be started locally without Docker
- the backend responds on `http://localhost:8000`
- the frontend opens on `http://localhost:5173`
- a real dashboard UI shell is visible in the browser
- the camera page and live-feed surface exist, even if full recognition is not complete yet

This plan is derived from:

- [`ENTRYLENS_ARCHITECTURE.md`](/d:/Testproject2/VisitorsTrackers/ENTRYLENS_ARCHITECTURE.md)
- [`ENTRYLENS_MASTER_PLAN.md`](/d:/Testproject2/VisitorsTrackers/ENTRYLENS_MASTER_PLAN.md)

Working product name for implementation:

- `EntryLens`

Legacy planning-doc name still present in source docs:

- `SentinelVision`

## Current Direction

The immediate implementation path is:

1. scaffold the backend and frontend as local apps
2. add a single repo-level dev entrypoint that starts the whole local app
3. let that entrypoint launch the backend and frontend together
4. defer Docker, Compose, MinIO container wiring, and container-first verification until later

This is a deliberate scope change. Containerization is not the active path for the current implementation pass.

Azure note on April 11, 2026:

- the separate Azure Face playground investigation is currently paused
- the blocker is Azure facial identification access requirements, including ACE recognition or similar approval gating
- that gating does not currently fit the intended project path, so bootstrap work should not depend on Azure playground success
- the active alternative exploration path is now a provider-specific CompreFace playground under `playgrounds/compreface-playground/`
- a narrower Azure detect-only playground is still a valid experiment under `playgrounds/azure-face-detect-playground/` if we want bbox detection research without identity features

## Target State

The first meaningful target is not "full product complete." It is:

1. one local repo-level dev command starts the project as a whole
2. FastAPI serves `/health` and protected API routes
3. React + Vite serves a routed dashboard shell
4. the browser can load the Live page and show:
   - header
   - sidebar navigation
   - camera panel
   - live event feed panel
   - API and WebSocket connection status
5. Attendance and Enroll pages render as real UI pages, even if some actions are still stubbed by incomplete backend stories

## Current Repo Truth

- The repository currently contains planning and documentation only.
- No `entrylens-api/` directory exists yet.
- No `entrylens-frontend/` directory exists yet.
- No `docker-compose.yml` exists yet.
- No migrations, runtime code, or tests exist yet.
- Product name is `EntryLens`; directory names will be `entrylens-api/` and `entrylens-frontend/`.

## Naming Convention

- Use `EntryLens` for product branding, UI labels, repo-facing docs, and app folder names.
- Use `sentinel` and `SENTINEL_*` for internal runtime identifiers that already exist in the architecture and master plan.
- Defer Docker and Compose work for now.
- Keep Docker service names and network names reserved for later container work:
  `sentinel-db`, `sentinel-api`, `sentinel-storage`, `sentinel-frontend`, and `sentinel-net`.
- Keep env vars on the existing runtime contract unless the canonical root docs are intentionally revised later.

## Source Mapping

This plan is mainly built from these stories and architecture steps:

### EP-01: Infrastructure & Provider Foundation
- US-002: PostgreSQL Schema & Migrations
- US-003: FaceProvider Abstract Interface
- US-004: AzureProvider Implementation
- US-005: FastAPI App Skeleton with Auth

### EP-02: Core Recognition Pipeline
- US-006: Enrollment Endpoint
- US-007: Recognition Endpoint
- US-008: Temporal Debounce Layer
- US-010: Attendance & Identity Read Endpoints

### EP-03: Frontend Camera & Quality Gate
- US-011: React Project Setup
- US-012: Camera Access & Video Stream
- US-013: MediaPipe Quality Gate Hook
- US-014: Recognition POST Loop

### EP-04: Dashboard & Real-Time Feed
- US-015: WebSocket Real-Time Feed (Backend)
- US-016: WebSocket Live Feed (Frontend)
- US-017: Enrollment Form UI
- US-018: Attendance History Table
- US-019: Dashboard Layout & Navigation

US-001 remains part of the broader roadmap, but it is explicitly deferred in this implementation pass.

## Assumptions

- Phase 1 is the correct starting point:
  local frontend + local FastAPI + Azure recognition
- Node and npm are available locally
- Python 3.11+ is acceptable for FastAPI work
- Azure credentials may not be available immediately
- Seeing the UI does not require finished Azure recognition on day 1
- Docker is explicitly out of scope for the current implementation pass

## Important Constraint

The architecture says not to skip foundational dependencies. That means we should not jump straight to a pretty dashboard before the repo has:

- API skeleton
- config loading
- provider interface
- database schema path

We can still sequence the work so the UI becomes visible early, but only after the foundation exists.

## Proposed Milestones

### Milestone 1: Repo Skeleton And Local Dev Startup

Goal:
the project can boot with one local dev command.

Includes:

- create root `.env.example`
- create `.gitignore`
- create `entrylens-api/`
- create `entrylens-frontend/`
- add a root-level dev entrypoint that starts both apps together
- keep storage and container orchestration deferred until after the runnable local shell exists

Mapped stories:

- US-011 partially

Exit check:

- one repo-level dev command starts the local app
- the API is reachable on port `8000`
- the frontend is reachable on port `5173`
- the user does not need to manually start backend and frontend in separate terminal steps

### Milestone 2: Backend Foundation

Goal:
the backend is real enough for the UI to talk to it safely.

Includes:

- FastAPI app entrypoint
- Pydantic settings
- API key auth dependency
- CORS for Vite
- `/health`
- provider contract in `app/providers/base.py`
- provider schemas
- Azure provider scaffold
- SQLAlchemy models
- Alembic setup
- initial migration for the four planned tables

Mapped stories:

- US-002
- US-003
- US-004
- US-005

Exit check:

- `/health` returns `200`
- protected routes reject missing or bad API key
- `alembic upgrade head` is prepared and ready once a local PostgreSQL instance is available
- the schema plan covers all four tables: `identities`, `attendance_logs`, `review_queue`, `embeddings_mirror`
- the migration path includes `pgvector` enablement
- the migration path includes the IVFFlat index on `embeddings_mirror.embedding`
- `provider_subject_id` is used on `identities` instead of provider-specific legacy names

Environment variables verified in `.env.example`:

- `SENTINEL_HIGH_CONFIDENCE_THRESHOLD=0.85`
- `SENTINEL_LOW_CONFIDENCE_THRESHOLD=0.60`
- `SENTINEL_DEBOUNCE_WINDOW_SECONDS=300`
- `SENTINEL_API_KEY`
- `SENTINEL_RECOGNITION_PROVIDER=azure`
- `AZURE_FACE_API_KEY`
- `AZURE_FACE_ENDPOINT`
- `AZURE_PERSON_GROUP_ID`

Azure-specific rule for this milestone:

- Azure provider code may be scaffolded here, but the first local bootstrap must not require valid Azure credentials just to start the API and render the frontend shell.

### Milestone 3: Frontend Shell You Can See

Goal:
open the app and see a usable operator interface.

Includes:

- Vite + React app
- React Router layout
- sidebar navigation
- pages:
  `LivePage`, `AttendancePage`, `EnrollPage`
- shared layout with connection status indicators
- API client wrapper with `X-API-Key` header injection
- WebSocket hook scaffold
- live feed component scaffold
- attendance table scaffold
- enrollment form scaffold

Mapped stories:

- US-011
- US-016 partial
- US-017 partial
- US-018 partial
- US-019

Exit check:

- `npm run dev` works locally
- browser loads dashboard shell
- nav works between pages
- header shows API and WebSocket status
- Live, Attendance, and Enroll pages render without crashing
- protected placeholder API route returns `401` when API key is missing
- protected placeholder API route responds successfully when `VITE_API_KEY` is provided

Important boundary:

- This milestone only proves shell-level behavior and API connectivity shape.
- It does not require real attendance data, enrollment writes, or Azure-backed recognition.

### Milestone 4: Live Camera And Browser Capture

Goal:
the Live page feels like a real surveillance dashboard, not just a shell.

Includes:

- `useCamera` hook
- `CameraView` component
- permission denied state
- MediaPipe package install
- model asset placement in `public/models/`
- initial `useMediaPipe` hook

Mapped stories:

- `US-012`
- `US-013`

Exit check:

- camera preview appears in browser
- denied permission shows a visible error state
- MediaPipe initializes without crashing the page

### Milestone 5: First End-To-End UI Integration

Goal:
the visible dashboard surfaces are connected to real backend behavior.

Includes:

- `POST /api/v1/enroll`
- `POST /api/v1/recognize`
- threshold routing using env vars rather than hardcoded values
- debounce using `SENTINEL_DEBOUNCE_WINDOW_SECONDS`
- `GET /api/v1/attendance`
- `WS /ws/live`
- frontend recognition loop
- frontend live WebSocket feed
- attendance page fetch
- enrollment submission flow

Mapped stories:

- US-006
- US-007
- US-008
- US-010
- US-014
- US-015
- US-016
- US-017
- US-018

Exit check:

- enrollment form submits successfully
- recognition events appear in the live feed
- attendance page loads real rows from API
- debounce suppresses duplicate logs within 5-minute window
- Azure-backed recognition succeeds when credentials are configured
- `POST /api/v1/recognize` returns a valid route-level response with:
  - `status`
  - `identity_id`
  - `similarity`
  - `log_id`
  - optional `review_id`
- threshold routing is correct:
  - similarity > 0.85 -> `status = "confirmed"`
  - similarity 0.60-0.84 -> `status = "pending_review"`
  - similarity < 0.60 -> `status = "visitor"`

## Recommended Build Order

This is the concrete order I recommend for implementation.

### Phase A: Bootstrap The Repository

1. Create the root project files:
   - `.env.example`
   - `.gitignore`
   - unified local dev launcher
2. Create `entrylens-api/` with:
   - `requirements.txt`
   - `app/main.py`
   - `app/config.py`
   - `app/auth.py`
   - `app/db.py`
3. Create `entrylens-frontend/` with:
   - `package.json`
   - `vite.config.*`
   - `src/App.jsx`
   - `src/main.jsx`
   - `.env.example`

### Phase B: Make The API Boot Cleanly

1. Implement config loading and fail-fast env validation.
2. Add `/health`.
3. Add protected placeholder routes under `/api/v1/`.
4. Add provider interface and provider schemas.
5. Add Azure provider scaffold and startup selection.

Reason:
the frontend should talk to a real API shape early, even before recognition is complete.

### Phase C: Add Database And Migrations

1. Add SQLAlchemy base and models.
2. Add Alembic config.
3. Add initial migration from the architecture schema.
4. Add DB session wiring.

Reason:
attendance, enrollment, and live feed become much easier to wire once the storage layer is real.

### Phase D: Build The Visible Dashboard Shell

1. Add React Router.
2. Add `Layout` and `Sidebar`.
3. Add:
   - `LivePage`
   - `AttendancePage`
   - `EnrollPage`
4. Add API client.
5. Add connection status widgets.

Reason:
this is the earliest point where you can reliably "run it and see the UI."

### Phase E: Add Camera And Live Feed Foundations

1. Add `useCamera` and `CameraView`.
2. Add `useWebSocket`.
3. Add `LiveFeed`.
4. Show connection states before real events are flowing.

Reason:
this makes the UI feel operational before recognition is fully wired.

### Phase F: Connect Real Workflows

1. Implement `enroll` backend and frontend.
2. Implement `recognize` backend and frontend recognition POST loop.
3. Implement attendance listing backend and frontend table.
4. Implement WebSocket broadcast after recognition writes.
5. Add MinIO storage after the core UI path works.

Reason:
MinIO is important, but it is not required for the very first "see the UI" goal.

### Phase G: Containerization Later

1. Add `docker-compose.yml`.
2. Add backend and frontend Dockerfiles.
3. Add PostgreSQL, pgvector, and MinIO container wiring.
4. Reintroduce container-based verification only after the direct local path is stable.

Reason:
containerization should package a working local app, not block the first scaffold.

## First Deliverable Definition

For this setup effort, I recommend defining success in two stages.

### Stage 1: Runnable UI

Success means:

- one local dev command starts the project
- frontend opens
- dashboard shell is visible
- camera panel renders
- connection status is visible
- pages navigate cleanly

This is the first checkpoint we should optimize for.

### Stage 2: Live End-To-End UI

Success means:

- enrollment form writes to backend
- camera captures and posts valid crops
- recognition result appears in live feed
- attendance page shows persisted results

This is the next checkpoint after the shell is working.

## Proposed Project Structure

This is the proposed initial repository layout for EntryLens. It is intentionally aligned with the architecture and master plan, but trimmed to the bootstrap path we actually want to build first.

```text
EntryLens/
|-- .env.example
|-- .gitignore
|-- scripts/
|   `-- dev.ps1
|-- llm-context-setup-prompt.md
|-- ENTRYLENS_ARCHITECTURE.md
|-- ENTRYLENS_MASTER_PLAN.md
|-- docs/
|   |-- README.md
|   |-- agents.md
|   |-- Planning/
|   |   |-- Plan.md
|   |   `-- 2026-04-10-runnable-ui-bootstrap.md
|   |-- project-truth/
|   |   |-- repo-map.md
|   |   |-- architecture-truth.md
|   |   |-- runtime-flows.md
|   |   |-- data-model.md
|   |   `-- changelog.md
|   `-- tasks/
|       |-- todo.md
|       `-- lessons.md
|-- entrylens-api/
|   |-- requirements.txt
|   |-- alembic.ini
|   |-- alembic/
|   |   |-- env.py
|   |   `-- versions/
|   |       `-- 001_initial_schema.py
|   `-- app/
|       |-- main.py
|       |-- config.py
|       |-- auth.py
|       |-- db.py
|       |-- models.py
|       |-- providers/
|       |   |-- __init__.py
|       |   |-- base.py
|       |   |-- schemas.py
|       |   `-- azure_provider.py
|       |-- routes/
|       |   |-- __init__.py
|       |   |-- enroll.py
|       |   |-- recognize.py
|       |   |-- attendance.py
|       |   |-- identities.py
|       |   |-- review.py
|       |   |-- export.py
|       |   `-- ws.py
|       |-- services/
|       |   |-- __init__.py
|       |   |-- enroll_service.py
|       |   |-- recognition_service.py
|       |   |-- review_service.py
|       |   |-- export_service.py
|       |   |-- storage_service.py
|       |   |-- debounce.py
|       |   `-- websocket_manager.py
|       `-- schemas/
|           |-- __init__.py
|           |-- enroll.py
|           |-- recognize.py
|           `-- review.py
`-- entrylens-frontend/
    |-- package.json
    |-- vite.config.js
    |-- .env.example
    |-- index.html
    |-- public/
    |   `-- models/
    |       `-- face_landmarker.task
    `-- src/
        |-- main.jsx
        |-- App.jsx
        |-- api/
        |   |-- client.js
        |   |-- enroll.js
        |   |-- recognize.js
        |   |-- attendance.js
        |   |-- review.js
        |   `-- export.js
        |-- hooks/
        |   |-- useCamera.js
        |   |-- useMediaPipe.js
        |   |-- useRecognitionLoop.js
        |   `-- useWebSocket.js
        |-- components/
        |   |-- Layout.jsx
        |   |-- Sidebar.jsx
        |   |-- CameraView.jsx
        |   |-- LiveFeed.jsx
        |   |-- EnrollmentForm.jsx
        |   |-- AttendanceTable.jsx
        |   `-- ReviewCard.jsx
        `-- pages/
            |-- LivePage.jsx
            |-- AttendancePage.jsx
            |-- EnrollPage.jsx
            `-- ReviewPage.jsx
```

## Structure Notes

- Keep `docs/` at repo root so project context stays easy for LLM bootstrap.
- Directory names are `entrylens-api/` and `entrylens-frontend/` to match the product name.
- Backend and frontend are sibling top-level apps for simple local development and later containerization.
- Keep `providers/`, `routes/`, `services/`, and `schemas/` separate in the backend to preserve the contract boundaries from the master plan.
- Add only the files needed for the bootstrap milestones first.
- The proposed structure includes the bootstrap path plus the connected EP-04 dashboard surfaces.
- Internal runtime naming still uses the established `sentinel-*` identifiers where the architecture already defines them.

## Directory Naming Decision

- Directories renamed from `sentinel-*` to `entrylens-*` before implementation.
- This avoids finding/replacing later after code exists.
- Runtime identifiers remain on `sentinel-*` and `SENTINEL_*` for compatibility with the canonical root docs.

## File Paths Expected To Change

### Root

- `.env.example`
- `.gitignore`
- `scripts/dev.ps1`

### Backend

- `entrylens-api/requirements.txt`
- `entrylens-api/alembic.ini`
- `entrylens-api/alembic/env.py`
- `entrylens-api/alembic/versions/001_initial_schema.py`
- `entrylens-api/app/main.py`
- `entrylens-api/app/config.py`
- `entrylens-api/app/auth.py`
- `entrylens-api/app/db.py`
- `entrylens-api/app/models.py`
- `entrylens-api/app/providers/__init__.py`
- `entrylens-api/app/providers/base.py`
- `entrylens-api/app/providers/schemas.py`
- `entrylens-api/app/providers/azure_provider.py`
- `entrylens-api/app/routes/enroll.py`
- `entrylens-api/app/routes/recognize.py`
- `entrylens-api/app/routes/attendance.py`
- `entrylens-api/app/routes/identities.py`
- `entrylens-api/app/routes/review.py`
- `entrylens-api/app/routes/export.py`
- `entrylens-api/app/routes/ws.py`
- `entrylens-api/app/services/enroll_service.py`
- `entrylens-api/app/services/recognition_service.py`
- `entrylens-api/app/services/review_service.py`
- `entrylens-api/app/services/export_service.py`
- `entrylens-api/app/services/storage_service.py`
- `entrylens-api/app/services/debounce.py`
- `entrylens-api/app/services/websocket_manager.py`
- `entrylens-api/app/schemas/enroll.py`
- `entrylens-api/app/schemas/recognize.py`
- `entrylens-api/app/schemas/review.py`

### Frontend

- `entrylens-frontend/.env.example`
- `entrylens-frontend/src/main.jsx`
- `entrylens-frontend/src/App.jsx`
- `entrylens-frontend/src/api/client.js`
- `entrylens-frontend/src/api/enroll.js`
- `entrylens-frontend/src/api/recognize.js`
- `entrylens-frontend/src/api/attendance.js`
- `entrylens-frontend/src/api/review.js`
- `entrylens-frontend/src/api/export.js`
- `entrylens-frontend/src/hooks/useCamera.js`
- `entrylens-frontend/src/hooks/useMediaPipe.js`
- `entrylens-frontend/src/hooks/useRecognitionLoop.js`
- `entrylens-frontend/src/hooks/useWebSocket.js`
- `entrylens-frontend/src/components/Layout.jsx`
- `entrylens-frontend/src/components/Sidebar.jsx`
- `entrylens-frontend/src/components/CameraView.jsx`
- `entrylens-frontend/src/components/LiveFeed.jsx`
- `entrylens-frontend/src/components/EnrollmentForm.jsx`
- `entrylens-frontend/src/components/AttendanceTable.jsx`
- `entrylens-frontend/src/components/ReviewCard.jsx`
- `entrylens-frontend/src/pages/LivePage.jsx`
- `entrylens-frontend/src/pages/AttendancePage.jsx`
- `entrylens-frontend/src/pages/EnrollPage.jsx`
- `entrylens-frontend/src/pages/ReviewPage.jsx`
- `entrylens-frontend/public/models/face_landmarker.task`

### Deferred Until Containerization

- `docker-compose.yml`
- `entrylens-api/Dockerfile`
- `entrylens-frontend/Dockerfile`

## Verification Steps

### Verification For Runnable UI

1. Start the project with the single repo-level dev command.
2. Confirm:
   - `http://localhost:8000/health` returns `{ "status": "ok" }`
   - `http://localhost:5173` loads the dashboard
3. Open the Live page.
4. Confirm the sidebar, header, and camera section render.
5. Confirm API status indicator goes green.
6. Confirm WebSocket status indicator becomes connected or at least retries cleanly if feed is not active yet.
7. Confirm a protected placeholder API route returns `401` without the API key.
8. Confirm the same protected placeholder API route succeeds when the frontend sends `VITE_API_KEY`.

### Verification For Live End-To-End UI

1. Submit the enrollment form with sample images.
2. Confirm an identity row is created.
3. Open camera page and present a face to the camera.
4. Confirm a recognition POST is emitted.
5. Confirm a WebSocket event appears in the live feed.
6. Confirm attendance history page shows the result.
7. With Azure credentials in `.env`, confirm recognition POST returns valid route data:
   - `status`
   - `identity_id` for recognized identities when applicable
   - `similarity` as a float
   - `log_id`
   - optional `review_id` for pending-review cases
8. Confirm the route response matches threshold routing behavior.

## Recommended Immediate Next Task

Start with Milestone 1 plus the minimum of Milestone 2 and 3 needed to show the dashboard shell:

1. create root env and ignore files
2. scaffold `entrylens-api/` with `/health`
3. scaffold `entrylens-frontend/` with router and layout
4. add the single local dev launcher
5. verify the Live, Attendance, and Enroll pages render

After that, move directly into backend schema and camera integration.

## Sprint Alignment

This bootstrap plan crosses sprint boundaries because it is organized around the fastest path to a runnable local UI, not around strict sprint completion. Use the master plan as the canonical sprint sequence and use the milestone mapping below only as a dependency guide.

| Sprint | Target | Bootstrap Contribution | Notes |
|---|---|---|---|
| **Sprint 1** | US-001 to US-003 | Milestone 1 + Milestone 2 partial | Local app skeleton now, Docker stack deferred, provider contract starts |
| **Sprint 2** | US-004 to US-005 | Milestone 2 completion | API protection and Azure scaffold |
| **Sprint 3** | US-006 to US-008 | Milestone 5 partial | Real enroll/recognize/debounce work starts |
| **Sprint 4** | US-009 to US-010 | Milestone 5 partial | Storage plus attendance read paths |
| **Sprint 5** | US-011 to US-013 | Milestone 3 + Milestone 4 | Frontend shell, camera, MediaPipe |
| **Sprint 6** | US-014 to US-016 | Milestone 5 partial | Recognition loop and live WebSocket feed |
| **Sprint 7** | US-017 to US-019 | Milestone 3 completion + Milestone 5 completion | Dashboard pages fully connected |

## Risks And Fallbacks

### Azure Unavailable
- Recognition endpoint returns `503` with clear error message.
- Frontend shows "Recognition service unavailable" status badge.
- Do not fall back to local storage; log and wait for Azure recovery.
- If Azure identification remains blocked by approval requirements, keep the bootstrap scope on runnable UI and non-Azure foundations rather than forcing the playground track forward.

### Database Connection Fails
- App fails fast on startup with connection error once database-backed paths are enabled.
- Health check can report degraded state if DB wiring is introduced before the database is reachable.
- No graceful degradation for database-backed features.

### MinIO Offline
- MinIO is deferred during the current non-Docker bootstrap path.
- When it is introduced later, recognition should still write to DB and emit WebSocket events even if object storage is temporarily unavailable.

### Frontend Camera Permission Denied
- Show clear error state in `CameraView`.
- Display instructions for enabling camera in browser settings.
- Do not auto-retry; require user action.

## Docs Update Checklist

- Update [`docs/tasks/todo.md`](/d:/Testproject2/VisitorsTrackers/docs/tasks/todo.md) when implementation starts.
- Update [`docs/project-truth/repo-map.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/repo-map.md) once `entrylens-api/` and `entrylens-frontend/` exist.
- Update [`docs/project-truth/architecture-truth.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/architecture-truth.md) once runtime code exists.
- Append meaningful milestones to [`docs/project-truth/changelog.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/changelog.md).
