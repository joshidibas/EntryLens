# Supabase Local Recognition Plan

## Task Summary

Connect EntryLens to Supabase as the active persistence path for the next local-recognition milestone, while keeping MediaPipe in the browser as the existing face detect and gating layer.

The intended user-facing direction is:

1. keep live MediaPipe face detection running in `/live` and `/labs`
2. stop relying on Azure-era provider assumptions
3. add Supabase-backed identity storage and vector search preparation
4. introduce a local recognition backend path that can enroll identities and recognize face chips later

## Current Repo Truth

- the frontend already has live MediaPipe detection running in TypeScript
- the shared `/labs` page now exposes `MediaPipe` for detect and `Local Recognition` as the planned recognize target
- the backend FastAPI app is runnable and now uses a neutral `LocalProvider` stub
- Azure playground folders have been removed from the active workspace
- `.env` and `.env.example` now default to `SENTINEL_RECOGNITION_PROVIDER=local`
- no Supabase client exists in the backend yet
- no real `recognize` or `enroll` API routes exist yet
- the backend still uses a local SQLite URL as the placeholder database setting

## Assumptions

- Supabase should become the primary persistence path for the next milestone
- local recognition will be implemented in Python behind the existing provider boundary
- MediaPipe remains browser-only detection and gating, not the recognition engine
- the current `labs` and `live` surfaces should stay usable while backend recognition work is added

## File Paths Expected To Change

- `.env.example`
- `.env`
- `entrylens-api/requirements.txt`
- `entrylens-api/app/config.py`
- `entrylens-api/app/main.py`
- `entrylens-api/app/providers/base.py`
- `entrylens-api/app/providers/local_provider.py`
- `entrylens-api/app/routes/labs.py`
- `entrylens-api/app/routes/recognition.py`
- `entrylens-api/app/services/`
- `entrylens-api/app/supabase_client.py`
- `entrylens-frontend/src/api/`
- `entrylens-frontend/src/pages/LabsPage.tsx`
- `docs/project-truth/architecture-truth.md`
- `docs/project-truth/repo-map.md`
- `docs/project-truth/changelog.md`
- `docs/tasks/todo.md`

## Implementation Steps

### Phase A: Supabase Configuration

1. Add Supabase env placeholders for URL, service key, and database URL.
2. Extend backend settings so Supabase configuration is typed and loaded at startup.
3. Decide whether the placeholder SQLite URL remains for local fallback or is replaced entirely by Supabase-backed Postgres config.

### Phase B: Backend Supabase Client

1. Add the Python dependencies required for Supabase access.
2. Create a small backend Supabase client module.
3. Verify the backend can initialize the client from env without breaking app startup.

### Phase C: Local Recognition Backend Shape

1. Keep `LocalProvider` as the active provider slot.
2. Expand provider schemas if the local-recognition plan needs richer response fields.
3. Add route scaffolding for `POST /api/v1/recognize` and `POST /api/v1/enroll`.
4. Keep real local embedding and matching logic behind the provider boundary.

### Phase D: Frontend Integration Preparation

1. Decide where the frontend should submit face chips for recognition.
2. Keep the current live MediaPipe detect flow intact.
3. Add only the minimal API client changes needed to prepare for Supabase-backed local recognition.

### Phase E: Verification

1. Verify frontend still builds after config and route-shape updates.
2. Verify backend imports and syntax still pass.
3. Verify the backend can start with Supabase placeholders present.
4. Verify the repo no longer exposes Azure as an active runtime path.

## Verification Steps

1. Confirm `.env.example` includes Supabase placeholders.
2. Confirm backend settings load the new Supabase values.
3. Confirm frontend build passes.
4. Confirm backend syntax checks pass.
5. Confirm `/live` and `/labs` still render with MediaPipe detect.
6. Confirm active repo paths no longer include Azure runtime config or Azure playground folders.

## Docs Update Checklist

- update `docs/project-truth/architecture-truth.md`
- update `docs/project-truth/repo-map.md`
- append to `docs/project-truth/changelog.md`
- update `docs/tasks/todo.md`
