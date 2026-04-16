# Agents Guide

## Purpose

This is the canonical operating guide for LLMs and coding agents working in this repository.

This repo is an active EntryLens workspace with runnable application code, planning docs, and graphified project context. Agents should use the codebase and `docs/project-truth/*` as implementation truth, and treat older root planning documents as roadmap context.

## Context Bootstrap Order

1. Read [`docs/README.md`](/d:/Testproject2/EntryLens/docs/README.md).
2. Read [`docs/project-truth/repo-map.md`](/d:/Testproject2/EntryLens/docs/project-truth/repo-map.md).
3. Read [`graphify-out/GRAPH_REPORT.md`](/d:/Testproject2/EntryLens/graphify-out/GRAPH_REPORT.md) before architecture or codebase questions.
4. **CRITICAL:** Read [`docs/tasks/lessons.md`](/d:/Testproject2/EntryLens/docs/tasks/lessons.md) for mistakes to avoid.
5. Read [`docs/project-truth/runtime-flows.md`](/d:/Testproject2/EntryLens/docs/project-truth/runtime-flows.md) when working on route or operator behavior.
6. Read [`docs/project-truth/data-model.md`](/d:/Testproject2/EntryLens/docs/project-truth/data-model.md) when changing schema, contracts, or storage.
7. Read [`README.md`](/d:/Testproject2/EntryLens/README.md) for setup and run instructions.
8. Read [`ENTRYLENS_MASTER_PLAN.md`](/d:/Testproject2/EntryLens/ENTRYLENS_MASTER_PLAN.md) only for broader backlog and roadmap context.

## Read This First

Use this smaller subset when an agent needs fast, reliable context before doing work:

1. Read [`docs/agents.md`](/d:/Testproject2/EntryLens/docs/agents.md).
2. Read [`docs/project-truth/repo-map.md`](/d:/Testproject2/EntryLens/docs/project-truth/repo-map.md).
3. Read [`graphify-out/GRAPH_REPORT.md`](/d:/Testproject2/EntryLens/graphify-out/GRAPH_REPORT.md).
4. Read [`docs/tasks/lessons.md`](/d:/Testproject2/EntryLens/docs/tasks/lessons.md).

Read these next only if the task needs them:

- [`docs/project-truth/runtime-flows.md`](/d:/Testproject2/EntryLens/docs/project-truth/runtime-flows.md) for route or operator flow work
- [`docs/project-truth/data-model.md`](/d:/Testproject2/EntryLens/docs/project-truth/data-model.md) for schema or contract work
- [`docs/Planning/Plan.md`](/d:/Testproject2/EntryLens/docs/Planning/Plan.md) before non-trivial multi-step implementation
- [`README.md`](/d:/Testproject2/EntryLens/README.md) for current setup and run instructions
- `docs/Planning/archive/` holds historical plans for broader context

This subset is the default recommendation because it is enough to learn:

- what exists in the repo today
- what is only planned
- the main mistakes to avoid before acting

## Canonical References

- Current implementation truth:
  [`docs/project-truth/repo-map.md`](/d:/Testproject2/EntryLens/docs/project-truth/repo-map.md)
- Current runtime and setup truth:
  [`README.md`](/d:/Testproject2/EntryLens/README.md)
- Broader roadmap reference:
  [`ENTRYLENS_MASTER_PLAN.md`](/d:/Testproject2/EntryLens/ENTRYLENS_MASTER_PLAN.md)

## Project Snapshot

- Product: EntryLens
- Domain: attendance and visitor tracking using browser capture plus face recognition
- Current stack snapshot:
  Frontend uses React 19, Vite, TypeScript, React Router, and browser-side MediaPipe tooling.
  Backend uses FastAPI, Pydantic settings, and a local provider abstraction.
  Persistence uses Supabase/PostgreSQL plus local runtime image storage under `runtime-data/`.
  Local development uses repo scripts and `npm run dev` from the root.
- Intended stack:
  React frontend, FastAPI backend, MediaPipe for browser detection, local recognition, Supabase/PostgreSQL with pgvector, MinIO, WebSocket dashboard
- Repo reality today:
  runnable backend and frontend apps plus planning and truth docs
- Missing today:
  production storage migration, WebSocket dashboard updates, and some roadmap items from the master plan
- Legacy note:
  the project was previously named `SentinelVision`; `EntryLens` is the active name.

## Working Rules

- Separate planned architecture from implemented reality.
- Keep naming split explicit:
  use `EntryLens` for branding, docs, UI, and app folder names.
  use `sentinel` and `SENTINEL_*` for existing internal runtime identifiers unless they are intentionally migrated.
- When answering architecture or codebase questions, check `graphify-out/GRAPH_REPORT.md` first and prefer the graphify wiki over raw file crawling when available.
- Use exact file paths when referencing important files.
- Prefer updating project-truth docs whenever the repo changes materially.
- If a root doc conflicts with repo contents, trust repo contents for implementation truth and call out the mismatch.
- Treat odd character encoding artifacts in the root docs as formatting issues, not as semantic changes.

## Verification Expectations

- For docs-only work, verify by checking file presence and content consistency.
- For code work later, verify against the actual files added, not the aspirational file tree in the plan.
- Do not invent routes, storage behavior, or setup steps that are not visible in the current code.

## Known Risks

- The root master plan includes a future file tree and legacy `sentinel-*` names that can be mistaken for current structure.
- Some root document text contains mojibake and encoding noise.
- Some docs still contain old `VisitorsTrackers` absolute links and pre-code language unless they are refreshed.

## Fast Path

- Need current truth fast:
  read [`docs/project-truth/repo-map.md`](/d:/Testproject2/EntryLens/docs/project-truth/repo-map.md)
- Need the stack quickly:
  read the stack snapshot in this file, then [`README.md`](/d:/Testproject2/EntryLens/README.md)
- Need the minimum safe bootstrap:
  read the `Read This First` section in this file, then [`docs/tasks/lessons.md`](/d:/Testproject2/EntryLens/docs/tasks/lessons.md)
- Need where to look first:
  read [`docs/project-truth/repo-map.md`](/d:/Testproject2/EntryLens/docs/project-truth/repo-map.md)
- Need planned flows:
  read [`docs/project-truth/runtime-flows.md`](/d:/Testproject2/EntryLens/docs/project-truth/runtime-flows.md)
- Need planning rules before starting non-trivial work:
  read [`docs/Planning/Plan.md`](/d:/Testproject2/EntryLens/docs/Planning/Plan.md)




<!-- graphify-links:start -->
## Graph Links

- [[graphify-out/wiki/index|Graphify Wiki]]
- [[graphify-out/GRAPH_REPORT|Graph Report]]
<!-- graphify-links:end -->
