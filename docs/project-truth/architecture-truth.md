# Architecture Truth

## Current Product Surface

EntryLens now has a runnable bootstrap scaffold in this repository, alongside the architecture and implementation planning documents.

Legacy naming note:

- the project was previously named `SentinelVision`
- `EntryLens` is now the active project name
- internal runtime identifiers may still use `sentinel` and `SENTINEL_*` by design

The intended product surface described by the root docs is still:

- browser-based camera capture and dashboard
- MediaPipe-based quality gating in the browser
- FastAPI backend for enrollment, recognition, review, and export
- local recognition provider abstraction for future backend identity matching
- PostgreSQL + pgvector persistence
- MinIO-backed face chip storage
- live dashboard updates over WebSocket

## Route Truth

Current repo truth:

- `GET /health` exists in the FastAPI scaffold without auth
- `GET /api/v1/attendance` exists as a protected placeholder route
- `GET /api/v1/labs` exists as a protected lab state route
- upload and command routes exist under `/api/v1/labs/*`
- a protected lab file route now exists for fetching uploaded playground assets back into the frontend
- frontend routes exist for `/live`, `/attendance`, and `/enroll`
- frontend route exists for `/labs`
- frontend route exists for `/identities/:identityId/add-data` for identity-specific live verification and sample enrichment
- the `/labs` UI now acts as a shared vision playground with `detect` or `recognize` task selection plus engine/provider and model-profile selection underneath
- MediaPipe is now a real local detect implementation in that shared lab, not just a placeholder target
- the active recognition direction is now local recognition plus planned Supabase-backed storage, not Azure
- `GET /api/v1/identities/sample-image` now serves locally stored sample images from the project runtime folder
- identity CRUD and sample-management routes are implemented under `/api/v1/identities`
- local enroll/add-sample flows can now store a captured reference image on disk and surface it in the identities UI
- frontend live recognition state is now shared through a reusable helper hook rather than duplicated page-specific logic
- frontend recognition now clears stale labels and re-runs identification when a different person replaces the current face in frame
- no Docker Compose file exists in the repository

Planned route truth from the architecture document:

- `POST /api/v1/recognize`
- `POST /api/v1/enroll`
- `GET /api/v1/review`
- `POST /api/v1/review/{id}/confirm`
- `POST /api/v1/review/{id}/reject`
- `GET /api/v1/identities`
- `DELETE /api/v1/identities/{id}`
- `GET /api/v1/export/csv`
- `WS /ws/live`

## Primary Vs Legacy

Implemented primary app surface in this checkout:

- `entrylens-api/` local FastAPI bootstrap
- `entrylens-frontend/` local React + Vite dashboard shell
- `scripts/dev.ps1` single-command local launcher
- `playgrounds/mediapipe-playground/` MediaPipe lab data folder used by the shared detect flow
- Playground lab routes and page for creating inputs directly from the UI and switching between playground targets

Within the design docs:

- Primary planned recognition surface:
  local recognition plus Supabase-backed storage
- Planned replacement surface:
  still to be decided after the local-recognition baseline is working
- Primary planned architectural style:
  staged monolith with internal boundaries

## What This Means In Practice

- If you are asked to build features, start by creating the missing repo structure.
- Do not treat the root docs as evidence that later sprint functionality already exists.
- Architecture decisions can be followed, but file paths must be created before they can be modified.
- Any future code PR should update this document once implementation becomes real.

## Current Friction To Remember

- The architecture doc is still ahead of the codebase.
- The root architecture describes an older Azure-first direction (superseded).
- Supabase and local recognition are now the active implementation path.
- Current build instructions are in `ENTRYLENS_BUILD_PLAN.md` at root.
- Original master plan archived at `docs/Planning/archive/ENTRYLENS_MASTER_PLAN_reference.md`.
- Supabase client module and LocalProvider scaffold have been added to the codebase.
- sample images are currently stored locally under `runtime-data/identity-samples/` rather than MinIO.
- The master plan contains many later-story routes and services that are not implemented yet.
- Encoding artifacts may make some sections look noisy; use meaning, not typography, as the source of truth.

