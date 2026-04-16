# Repo Map

## First-Look Summary

- Repo type:
  active application workspace with planning docs
- Current stack in the repo itself:
  FastAPI backend, React + Vite frontend, browser-side MediaPipe integration, Supabase-backed identity storage, local runtime image storage, PowerShell dev launcher, Markdown docs
- Planned implementation stack:
  React + Vite frontend, FastAPI backend, local recognition provider, Supabase/PostgreSQL + pgvector, optional remote embedding providers, MinIO/object storage, Docker Compose for local orchestration
- Intended product stack from docs:
  React + MediaPipe, FastAPI, local recognition, Supabase/PostgreSQL + pgvector, MinIO
- App shape today:
  runnable root workspace with sibling `entrylens-api/` and `entrylens-frontend/` app directories plus runtime and playground folders

## High-Value Files

- [`README.md`](/d:/Testproject2/EntryLens/README.md)
  Current setup and local run instructions.
- [`ENTRYLENS_MASTER_PLAN.md`](/d:/Testproject2/EntryLens/ENTRYLENS_MASTER_PLAN.md)
  Large backlog and intended future file tree; useful as roadmap context, not repo truth.
- [`package.json`](/d:/Testproject2/EntryLens/package.json)
  Repo-level dev entrypoint for the whole local app.
- [`scripts/dev.ps1`](/d:/Testproject2/EntryLens/scripts/dev.ps1)
  Starts backend and frontend together for local development.
- [`entrylens-api/app/main.py`](/d:/Testproject2/EntryLens/entrylens-api/app/main.py)
  FastAPI app bootstrap with CORS and route registration.
- [`entrylens-api/app/routes/identities.py`](/d:/Testproject2/EntryLens/entrylens-api/app/routes/identities.py)
  Identity CRUD, sample-management routes, and local sample-image serving endpoint.
- [`entrylens-api/app/routes/detection_logs.py`](/d:/Testproject2/EntryLens/entrylens-api/app/routes/detection_logs.py)
  Live-feed detection-log routes for review, merge, and sample-promotion workflows.
- [`entrylens-api/app/sample_images.py`](/d:/Testproject2/EntryLens/entrylens-api/app/sample_images.py)
  Local runtime storage helper for captured identity/sample images and detection-log review frames.
- [`entrylens-api/app/supabase.py`](/d:/Testproject2/EntryLens/entrylens-api/app/supabase.py)
  Core persistence wrapper for identities, samples, embeddings, and detection-log lookup helpers.
- [`entrylens-frontend/src/App.tsx`](/d:/Testproject2/EntryLens/entrylens-frontend/src/App.tsx)
  Frontend router shell for Live, Attendance, Detection Logs, Identities, Enroll, and Labs pages.
- [`entrylens-frontend/src/pages/IdentitiesPage.tsx`](/d:/Testproject2/EntryLens/entrylens-frontend/src/pages/IdentitiesPage.tsx)
  Identity directory and detail UI with CRUD, profile preview, and sample management.
- [`entrylens-frontend/src/pages/IdentityAddDataPage.tsx`](/d:/Testproject2/EntryLens/entrylens-frontend/src/pages/IdentityAddDataPage.tsx)
  Identity-specific live camera workspace for recognition checks and adding more samples from the feed.
- [`entrylens-frontend/src/pages/DetectionLogsPage.tsx`](/d:/Testproject2/EntryLens/entrylens-frontend/src/pages/DetectionLogsPage.tsx)
  Detection-log list and detail review UI for renaming unknowns, merging to existing identities, and promoting saved frames into samples.
- [`entrylens-frontend/src/pages/LabsPage.tsx`](/d:/Testproject2/EntryLens/entrylens-frontend/src/pages/LabsPage.tsx)
  In-app vision lab centered on shared detect and recognize flows with selectable engines, providers, and model profiles.
- [`entrylens-frontend/src/hooks/useRecognitionSession.ts`](/d:/Testproject2/EntryLens/entrylens-frontend/src/hooks/useRecognitionSession.ts)
  Shared live-recognition state helper used by Live, Labs, and identity add-data flows.
- [`entrylens-frontend/src/hooks/useMediaPipeLab.ts`](/d:/Testproject2/EntryLens/entrylens-frontend/src/hooks/useMediaPipeLab.ts)
  Browser-side MediaPipe Face Landmarker hook used by the shared Vision Lab detect flow.
- [`entrylens-api/app/routes/labs.py`](/d:/Testproject2/EntryLens/entrylens-api/app/routes/labs.py)
  Backend routes for shared lab state, uploads, and command execution.
- [`docs/agents.md`](/d:/Testproject2/EntryLens/docs/agents.md)
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
  FastAPI app with config, auth, provider contract, routes, schemas, and Supabase integration.
- `entrylens-frontend/`
  Vite + React dashboard with routed pages, API clients, hooks, and shared components.
- `entrylens-api/app/services/labs.py`
  File and command orchestration for the in-app labs experience.
- `scripts/`
  Repo-level launcher scripts.
- `playgrounds/mediapipe-playground/`
  Dedicated input and output storage folder for the browser-side MediaPipe detect flow used by the shared Vision Lab.
- `playgrounds/insightface-colab/`
  Supporting playground assets and docs for the optional InsightFace Colab embedding path.
- `runtime-data/`
  Local runtime storage for sample images and detection-log review frames.

## Runtime Flow Summary

There is now a runnable local runtime in the repository:

1. Browser dashboard shell with a live MediaPipe camera panel.
2. FastAPI `/health` endpoint plus mounted attendance, labs, enroll, identities, recognize, and detection-log routes.
3. React router shell for Live, Attendance, and Enroll pages.
4. Repo-level `npm run dev` launcher that starts both apps together.
5. In-app Labs page for MediaPipe detect workflows and shared recognition experiments.
6. In-app unified vision-lab selector that now supports one shared `detect` or `recognize` workflow with engine/provider and model-profile selection layered underneath.
7. The shared detect flow now has one real implementation: browser-side MediaPipe Face Landmarker.
8. Identity CRUD is now implemented with sample-level reference/profile management.
9. The app can store local sample images in `runtime-data/identity-samples/` and show the current profile picture in the identities UI.
10. Live recognition state is shared across Live, Labs, and identity add-data surfaces through one frontend helper hook.
11. Recognition labels now reset and re-identify when the visible person changes, instead of waiting for the frame to become empty.
12. Live feed now writes detection logs, with backend duplicate suppression for repeat recognized or unknown faces.
13. Detection-log review can rename placeholders, merge into existing identities, and promote captured frames into the embedding/sample store.
14. The current codebase also contains an InsightFace Colab service direction and playground assets that appear to support alternate embedding-model workflows.

Still planned from the architecture document:

1. Production-grade recognition provider integration instead of placeholder vectors.
2. Object-storage migration for sample images if local runtime storage stops being sufficient.
3. WebSocket dashboard updates.

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
- Some historical docs still contain absolute links to the old `VisitorsTrackers` workspace.
- Some character encoding is corrupted in the root Markdown files.

## Staying Memory-Efficient

- Read `docs/agents.md` first, not the full root docs.
- Use this repo map to decide whether you even need the long root documents.
- Only open the architecture sections relevant to the task.
- Do not load the entire master plan unless the task is specifically about roadmap or backlog structure.




<!-- graphify-links:start -->
## Graph Links

- [[graphify-out/wiki/index|Graphify Wiki]]
- [[graphify-out/GRAPH_REPORT|Graph Report]]
- Related file notes:
  - [[graphify-out/wiki/entrylens-api/app/main.py|entrylens-api/app/main.py]]
  - [[graphify-out/wiki/entrylens-api/app/routes/detection_logs.py|entrylens-api/app/routes/detection_logs.py]]
  - [[graphify-out/wiki/entrylens-api/app/routes/identities.py|entrylens-api/app/routes/identities.py]]
  - [[graphify-out/wiki/entrylens-api/app/routes/labs.py|entrylens-api/app/routes/labs.py]]
  - [[graphify-out/wiki/entrylens-api/app/sample_images.py|entrylens-api/app/sample_images.py]]
  - [[graphify-out/wiki/entrylens-api/app/services/labs.py|entrylens-api/app/services/labs.py]]
  - [[graphify-out/wiki/entrylens-api/app/supabase.py|entrylens-api/app/supabase.py]]
  - [[graphify-out/wiki/entrylens-frontend/src/App.tsx|entrylens-frontend/src/App.tsx]]
  - [[graphify-out/wiki/entrylens-frontend/src/hooks/useMediaPipeLab.ts|entrylens-frontend/src/hooks/useMediaPipeLab.ts]]
  - [[graphify-out/wiki/entrylens-frontend/src/hooks/useRecognitionSession.ts|entrylens-frontend/src/hooks/useRecognitionSession.ts]]
  - [[graphify-out/wiki/entrylens-frontend/src/pages/DetectionLogsPage.tsx|entrylens-frontend/src/pages/DetectionLogsPage.tsx]]
  - [[graphify-out/wiki/entrylens-frontend/src/pages/IdentitiesPage.tsx|entrylens-frontend/src/pages/IdentitiesPage.tsx]]
- Related communities:
  - [[graphify-out/wiki/communities/Community 0|Community 0]]
  - [[graphify-out/wiki/communities/Community 1|Community 1]]
  - [[graphify-out/wiki/communities/Community 2|Community 2]]
  - [[graphify-out/wiki/communities/Community 5|Community 5]]
  - [[graphify-out/wiki/communities/Community 9|Community 9]]
  - [[graphify-out/wiki/communities/Community 10|Community 10]]
<!-- graphify-links:end -->
