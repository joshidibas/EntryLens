# Repo Map

## First-Look Summary

- Repo type:
  early implementation repository with planning docs
- Current stack in the repo itself:
  FastAPI backend scaffold, React + Vite frontend scaffold, browser-side MediaPipe lab integration, PowerShell dev launcher, Markdown docs
- Planned implementation stack:
  React + Vite frontend, FastAPI backend, local recognition provider, Supabase/PostgreSQL + pgvector, MinIO, Docker Compose for local orchestration
- Intended product stack from docs:
  React + MediaPipe, FastAPI, local recognition, Supabase/PostgreSQL + pgvector, MinIO
- App shape today:
  docs plus sibling `entrylens-api/` and `entrylens-frontend/` app directories

## High-Value Files

- [`ENTRYLENS_ARCHITECTURE.md`](/d:/Testproject2/VisitorsTrackers/ENTRYLENS_ARCHITECTURE.md)
  Main architecture and runtime design source.
- [`ENTRYLENS_MASTER_PLAN.md`](/d:/Testproject2/VisitorsTrackers/ENTRYLENS_MASTER_PLAN.md)
  Execution backlog and intended file tree.
- [`package.json`](/d:/Testproject2/VisitorsTrackers/package.json)
  Repo-level dev entrypoint for the whole local app.
- [`scripts/dev.ps1`](/d:/Testproject2/VisitorsTrackers/scripts/dev.ps1)
  Starts backend and frontend together for local development.
- [`entrylens-api/app/main.py`](/d:/Testproject2/VisitorsTrackers/entrylens-api/app/main.py)
  FastAPI app bootstrap with CORS and route registration.
- [`entrylens-frontend/src/App.tsx`](/d:/Testproject2/VisitorsTrackers/entrylens-frontend/src/App.tsx)
  Frontend router shell for Live, Attendance, and Enroll pages.
- [`entrylens-frontend/src/pages/LabsPage.tsx`](/d:/Testproject2/VisitorsTrackers/entrylens-frontend/src/pages/LabsPage.tsx)
  In-app unified vision lab centered on MediaPipe live detection and a planned local-recognition path.
- [`entrylens-frontend/src/hooks/useMediaPipeLab.ts`](/d:/Testproject2\\VisitorsTrackers/entrylens-frontend/src/hooks/useMediaPipeLab.ts)
  Browser-side MediaPipe Face Landmarker hook used by the shared Vision Lab detect flow.
- [`entrylens-api/app/routes/labs.py`](/d:/Testproject2/VisitorsTrackers/entrylens-api/app/routes/labs.py)
  Backend routes for shared lab state, uploads, and command execution.
- [`docs/agents.md`](/d:/Testproject2/VisitorsTrackers/docs/agents.md)
  Fast bootstrap for future agents.

## Main Folders

- `docs/`
  LLM-oriented context and planning docs added from the context prompt.
- `docs/project-truth/`
  Current-reality docs and caution notes.
- `docs/Planning/`
  Rules for planning non-trivial work.
- `docs/tasks/`
  Active task tracking and lessons learned.
- `entrylens-api/`
  Local FastAPI scaffold with config, auth, provider contract, and placeholder routes.
- `entrylens-frontend/`
  Vite + React dashboard shell with routed page stubs and shared layout.
- `entrylens-api/app/services/labs.py`
  File and command orchestration for the in-app labs experience.
- `scripts/`
  Repo-level launcher scripts.
- `playgrounds/mediapipe-playground/`
  Dedicated input and output storage folder for the browser-side MediaPipe detect flow used by the shared Vision Lab.

## Runtime Flow Summary

There is now a minimal executable runtime in the repository:

1. Browser dashboard shell with a live MediaPipe camera panel.
2. FastAPI `/health` endpoint and a protected placeholder attendance endpoint.
3. React router shell for Live, Attendance, and Enroll pages.
4. Repo-level `npm run dev` launcher that starts both apps together.
5. In-app Labs page for MediaPipe detect workflows and the planned local-recognition slot.
6. In-app unified vision-lab selector that now supports one shared `detect` or `recognize` workflow with engine/provider and model-profile selection layered underneath.
7. The shared detect flow now has one real implementation: browser-side MediaPipe Face Landmarker.

Still planned from the architecture document:

1. Real recognition and enrollment endpoints.
2. Local recognition provider integration.
3. Supabase/PostgreSQL persistence plus MinIO image storage.
4. WebSocket dashboard updates.

## Important Data And Storage Surfaces

- Planned relational store:
  PostgreSQL with `identities`, `attendance_logs`, `review_queue`, `embeddings_mirror`
- Planned object store:
  MinIO in Phase 1, S3-compatible path later
- Planned identity surface:
  local embeddings plus Supabase-backed identity records

## Known Cautions

- The root docs still describe some legacy `sentinel-*` paths that do not match the implemented `entrylens-*` folders.
- The scaffold is intentionally lighter than the full master-plan tree.
- The repo is not a git repository in the current workspace snapshot, so git-based verification is unavailable here.
- Some character encoding is corrupted in the root Markdown files.

## Staying Memory-Efficient

- Read `docs/agents.md` first, not the full root docs.
- Use this repo map to decide whether you even need the long root documents.
- Only open the architecture sections relevant to the task.
- Do not load the entire master plan unless the task is specifically about roadmap or backlog structure.

