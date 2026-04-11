# Changelog

## 2026-04-11

- Expanded the identity model and local sample-image flow to support richer CRUD, profile preview, and identity-specific add-data workflows.
- Added a dedicated identity add-data page for live verification and adding more samples from the camera feed.
- Refactored frontend recognition state into a shared helper hook used by Live, Labs, and identity add-data pages.
- Fixed stale recognition labels so a different person entering frame clears the previous identity and triggers a fresh recognition pass.
- Applied the database-side schema for `detection_logs` and placeholder unknown-identity review flow as the next implementation baseline.
- Implemented `/api/v1/detection-logs` plus merge and promote actions for Live-feed-only review records.
- Added frontend detection-log list/detail pages and wired `/live` to create logs without affecting Labs or identity add-data flows.
- Added placeholder unknown-identity review flow so operators can rename the placeholder, merge into an existing identity, or promote the stored frame into embeddings.

## 2026-04-10

- Added initial `docs/` context system from `llm-context-setup-prompt.md`.
- Documented that the repository currently contains planning docs only, not app implementation.
- Added project-truth files covering repo map, architecture truth, runtime flows, and planned data model.
- Added planning, task tracking, and lessons files for future agent work.
- Added a dated bootstrap plan for taking EntryLens from docs-only state to a locally runnable dashboard UI.
- Added a concise planned stack snapshot to the core docs for faster LLM bootstrap.
- Added a tighter "read this first" subset to reduce future agent context loading and front-load the most important truth and lessons docs.
- Revised the active bootstrap plan to defer Docker work and prioritize direct local backend/frontend startup first.
- Revised the active bootstrap plan again so local development uses one repo-level dev entrypoint instead of asking the user to start backend and frontend separately.
- Renamed the active project name from `SentinelVision` to `EntryLens` across the docs context and root planning documents.
- Renamed root planning files to [`ENTRYLENS_ARCHITECTURE.md`](/d:/Testproject2/VisitorsTrackers/ENTRYLENS_ARCHITECTURE.md) and [`ENTRYLENS_MASTER_PLAN.md`](/d:/Testproject2/VisitorsTrackers/ENTRYLENS_MASTER_PLAN.md).
- Added the first runnable EntryLens scaffold with `entrylens-api/`, `entrylens-frontend/`, root env files, and a repo-level `npm run dev` launcher.
- Added a FastAPI bootstrap with config loading, API key auth, `/health`, and a protected placeholder attendance route.
- Added a Vite + React dashboard shell with routed Live, Attendance, and Enroll pages plus API/WebSocket status indicators.
- Verified the full local shell boots without Docker from the single repo-level dev command.
- Reviewed the Azure Face identity quickstart and added a dedicated playground-first implementation plan in [`docs/old/Planning/2026-04-10-azure-face-playground.md`](/d:/Testproject2/VisitorsTrackers/docs/old/Planning/2026-04-10-azure-face-playground.md).
- Added `playgrounds/azure-face-playground/`, a TypeScript CLI for Azure group setup, enrollment, training, identification, verification, and cleanup experiments.
- Added a repo-level `npm run playground:azure` shortcut and verified the playground builds and shows CLI help locally.
- Added a protected in-app Azure Lab with backend upload/command routes and a frontend `/azure-lab` page for creating enroll and probe datasets directly from the UI.
- Verified the main app still boots after the Azure Lab integration and that `/api/v1/azure-lab` responds successfully with the configured API key.
- Improved Azure playground and lab error reporting so Azure inner errors are shown directly in the UI, and documented that the current Face resource is blocked by missing `Identification` / `Verification` approval.
- Added `playgrounds/azure-face-detect-playground/`, a separate TypeScript CLI for Azure detect-only experiments that write raw JSON artifacts and SVG bbox previews.
- Added a repo-level `npm run playground:azure-detect` shortcut and verified that the new detect-only playground builds and shows CLI help.
- Upgraded the in-app `/azure-lab` page into a selector-based playground lab so the UI can switch between Azure identity and Azure detect workflows instead of being hard-wired to one provider path.
- Added a visible planned `CompreFace` option to the playground selector so the lab now reads as a provider picker and can grow into the next self-hosted path without another UI reshuffle.
- Added `MediaPipe` as a selectable planned target in the lab and broadened the UI framing from a provider-only picker into a more general vision lab.
- Reshaped the vision lab into a single shared playground flow with `Task -> Engine/Provider -> Model Profile` selectors so detection and recognition options can be explored in one place while their implementations stay separated behind the scenes.
- Made MediaPipe the first real non-Azure implementation inside the shared detect flow by adding browser-side Face Landmarker execution, MediaPipe-specific input storage under `playgrounds/mediapipe-playground/`, and a protected lab file route for feeding uploaded images back into the frontend.
- Migrated the active frontend surface from JSX to TS/TSX so the repo is aligned with the current build-plan direction before further feature work.
- Removed Azure from the active runtime path by switching the app to a neutral local provider stub, removing Azure env values from the active env files, and dropping the Azure playground folders from `playgrounds/`.
- Reframed the current repo truth around MediaPipe live detect plus planned local recognition and Supabase integration instead of Azure experimentation.

