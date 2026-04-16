# Docs README

This `docs/` tree is the low-noise entry point for future LLMs and developers working in this repository.

The repository now contains both planning material and runnable application code. These docs exist to keep current repo truth separate from older architecture and roadmap documents that still describe planned or partially outdated paths.

## Read Order

1. `docs/agents.md`
2. `docs/project-truth/repo-map.md`
3. `docs/project-truth/architecture-truth.md`
4. `docs/project-truth/runtime-flows.md`
5. `docs/project-truth/data-model.md`
6. `docs/Planning/Plan.md`
7. `README.md`
8. `ENTRYLENS_MASTER_PLAN.md` (root - broader backlog and intended future tree)

## Read This First

For most future agent sessions, start with this tighter subset instead of loading everything:

1. Read [`docs/agents.md`](/d:/Testproject2/EntryLens/docs/agents.md).
2. Read [`docs/project-truth/repo-map.md`](/d:/Testproject2/EntryLens/docs/project-truth/repo-map.md).
3. Read [`docs/project-truth/architecture-truth.md`](/d:/Testproject2/EntryLens/docs/project-truth/architecture-truth.md).
4. Read [`docs/tasks/lessons.md`](/d:/Testproject2/EntryLens/docs/tasks/lessons.md).

Then expand only as needed:

- add `docs/project-truth/runtime-flows.md` for route or operator flow work
- add `docs/project-truth/data-model.md` for schema or contract work
- add `docs/Planning/Plan.md` before non-trivial multi-step implementation
- read `README.md` for current local setup and run instructions
- read `ENTRYLENS_MASTER_PLAN.md` only if you need the broader backlog and historical intended file tree

This shorter path is preferred because it gives agents the current repo state, the main design/reality split, and the most important failure-prevention rules with minimal noise.

## What Lives Here

- `docs/agents.md`
  Canonical quick-start for coding agents and LLMs.
- `docs/project-truth/repo-map.md`
  Small repo map with first places to inspect.
- `docs/project-truth/architecture-truth.md`
  Current architecture truth, including what is real now versus planned.
- `docs/project-truth/runtime-flows.md`
  Important runtime and operator flows pulled from the architecture plan.
- `docs/project-truth/data-model.md`
  Practical data model reference based on the planned PostgreSQL schema.
- `docs/database/`
  Database schema and changelog for tracking schema changes.
  - `docs/database/schema.md` - Full database schema reference
  - `docs/database/changelog.md` - Database change history (migrations)
- `docs/project-truth/changelog.md`
  Meaningful documentation-truth change log.
- `docs/Planning/Plan.md`
  Required planning workflow for non-trivial work.
- `docs/Planning/old/`
  Archive for completed or explicitly retired dated plan files.
- `docs/Planning/archive/`
  Archive for historical planning documents retained for reference.
- `docs/tasks/todo.md`
  Current working checklist and verification notes.
- `docs/tasks/lessons.md`
  Repeated mistakes, corrections, and preventive rules.
- `README.md`
  Current setup and local run instructions for the repo.
- `ENTRYLENS_MASTER_PLAN.md`
  Large root backlog and future-looking implementation plan that still contains legacy naming.

## Quick Reference Rules

- State what exists in this repo now, not what the architecture intends later.
- Treat [`README.md`](/d:/Testproject2/EntryLens/README.md) and [`docs/project-truth/repo-map.md`](/d:/Testproject2/EntryLens/docs/project-truth/repo-map.md) as the fastest current-state entry points.
- Treat [`ENTRYLENS_MASTER_PLAN.md`](/d:/Testproject2/EntryLens/ENTRYLENS_MASTER_PLAN.md) as roadmap context, not implementation truth.
- Do not claim paths like `sentinel-api/` or `sentinel-frontend/` exist unless they are actually added to the repo.
- Update `docs/project-truth/*` when repo reality changes.




<!-- graphify-links:start -->
## Graph Links

- [[graphify-out/wiki/index|Graphify Wiki]]
- [[graphify-out/GRAPH_REPORT|Graph Report]]
<!-- graphify-links:end -->
