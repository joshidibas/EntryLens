# Agents Guide

## Purpose

This is the canonical operating guide for LLMs and coding agents working in this repository.

The current repo is a documentation-and-planning workspace for EntryLens, a face-recognition attendance and visitor tracking system. The product architecture is described in root Markdown files, but the codebase those files describe is not present yet.

## Context Bootstrap Order

1. Read [`docs/README.md`](/d:/Testproject2/VisitorsTrackers/docs/README.md).
2. Read [`docs/project-truth/repo-map.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/repo-map.md).
3. Read [`docs/project-truth/architecture-truth.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/architecture-truth.md).
4. **CRITICAL:** Read [`docs/tasks/lessons.md`](/d:/Testproject2/VisitorsTrackers/docs/tasks/lessons.md) - contains critical mistakes to avoid.
5. Read [`docs/project-truth/runtime-flows.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/runtime-flows.md).
6. Read [`docs/project-truth/data-model.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/data-model.md).
7. Read the current build instructions:
   - [`ENTRYLENS_BUILD_PLAN.md`](/d:/Testproject2/VisitorsTrackers/ENTRYLENS_BUILD_PLAN.md) (active - current implementation)
8. For broader product context, read:
   - [`ENTRYLENS_ARCHITECTURE.md`](/d:/Testproject2/VisitorsTrackers/ENTRYLENS_ARCHITECTURE.md)
   - [`docs/Planning/archive/ENTRYLENS_MASTER_PLAN_reference.md`](/d:/Testproject2/VisitorsTrackers/docs/Planning/archive/ENTRYLENS_MASTER_PLAN_reference.md)

## Read This First

Use this smaller subset when an agent needs fast, reliable context before doing work:

1. Read [`docs/agents.md`](/d:/Testproject2/VisitorsTrackers/docs/agents.md).
2. Read [`docs/project-truth/repo-map.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/repo-map.md).
3. Read [`docs/project-truth/architecture-truth.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/architecture-truth.md).
4. Read [`docs/tasks/lessons.md`](/d:/Testproject2/VisitorsTrackers/docs/tasks/lessons.md).

Read these next only if the task needs them:

- [`docs/project-truth/runtime-flows.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/runtime-flows.md) for route or operator flow work
- [`docs/project-truth/data-model.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/data-model.md) for schema or contract work
- [`docs/Planning/Plan.md`](/d:/Testproject2/VisitorsTrackers/docs/Planning/Plan.md) before non-trivial multi-step implementation
- [`ENTRYLENS_BUILD_PLAN.md`](/d:/Testproject2/VisitorsTrackers/ENTRYLENS_BUILD_PLAN.md) for current build instructions
- `docs/Planning/archive/` holds historical plans for broader context

This subset is the default recommendation because it is enough to learn:

- what exists in the repo today
- what is only planned
- the main mistakes to avoid before acting

## Canonical References

- Primary architecture source:
  [`ENTRYLENS_ARCHITECTURE.md`](/d:/Testproject2/VisitorsTrackers/ENTRYLENS_ARCHITECTURE.md)
- Current build plan source:
  [`ENTRYLENS_BUILD_PLAN.md`](/d:/Testproject2/VisitorsTrackers/ENTRYLENS_BUILD_PLAN.md)
- Archived reference (broader product vision):
  [`docs/Planning/archive/ENTRYLENS_MASTER_PLAN_reference.md`](/d:/Testproject2/VisitorsTrackers/docs/Planning/archive/ENTRYLENS_MASTER_PLAN_reference.md)

## Project Snapshot

- Product: EntryLens
- Domain: attendance and visitor tracking using browser capture plus face recognition
- Planned stack snapshot:
  Frontend uses React, Vite, React Router, MediaPipe, native WebSocket, and an API client wrapper.
  Backend uses FastAPI, Pydantic settings, SQLAlchemy, and Alembic.
  Persistence is moving toward Supabase/PostgreSQL with pgvector plus MinIO-compatible object storage.
  Recognition is moving toward a local provider behind the existing provider abstraction.
  Local development uses Docker Compose with `sentinel-db`, `sentinel-api`, `sentinel-storage`, and `sentinel-frontend`.
- Intended stack:
  React frontend, FastAPI backend, MediaPipe for browser detection, local recognition, Supabase/PostgreSQL with pgvector, MinIO, WebSocket dashboard
- Repo reality today:
  only root planning docs plus this `docs/` set
- Missing today:
  application code, Docker files, database migrations, frontend, API routes, tests, env files
- Legacy note:
  the project was previously named `SentinelVision`; `EntryLens` is the active name.

## Working Rules

- Separate planned architecture from implemented reality.
- Keep naming split explicit:
  use `EntryLens` for branding, docs, UI, and app folder names.
  use `sentinel` and `SENTINEL_*` for existing internal runtime identifiers unless the canonical root docs are deliberately revised.
- When a task asks to "implement" architecture items, create the missing repo structure or docs explicitly instead of implying it already exists.
- Use exact file paths when referencing important files.
- Prefer updating project-truth docs whenever the repo changes materially.
- If a root doc conflicts with repo contents, trust repo contents for implementation truth and call out the mismatch.
- Treat odd character encoding artifacts in the root docs as formatting issues, not as semantic changes.

## Verification Expectations

- For docs-only work, verify by checking file presence and content consistency.
- For code work later, verify against the actual files added, not the aspirational file tree in the plan.
- If no runnable code exists, say so directly instead of inventing build or test results.

## Known Risks

- The root architecture document describes many concrete paths that are not in this repo yet.
- The root master plan includes a future file tree that can be mistaken for current structure.
- Some root document text contains mojibake and encoding noise.
- Because no app code exists yet, route, auth, storage, and provider behavior are design intent, not runtime truth.

## Fast Path

- Need current truth fast:
  read [`docs/project-truth/architecture-truth.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/architecture-truth.md)
- Need the stack quickly:
  read the stack snapshot in this file, then [`docs/project-truth/repo-map.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/repo-map.md)
- Need the minimum safe bootstrap:
  read the `Read This First` section in this file, then [`docs/tasks/lessons.md`](/d:/Testproject2/VisitorsTrackers/docs/tasks/lessons.md)
- Need where to look first:
  read [`docs/project-truth/repo-map.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/repo-map.md)
- Need planned flows:
  read [`docs/project-truth/runtime-flows.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/runtime-flows.md)
- Need planning rules before starting non-trivial work:
  read [`docs/Planning/Plan.md`](/d:/Testproject2/VisitorsTrackers/docs/Planning/Plan.md)

