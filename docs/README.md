# Docs README

This `docs/` tree is the low-noise entry point for future LLMs and developers working in this repository.

The repository currently contains planning and architecture material only. The application code described in the root documents is not present in this checkout yet, so these docs focus on current truth and on how to avoid treating planned paths as implemented paths.

## Read Order

1. `docs/agents.md`
2. `docs/project-truth/repo-map.md`
3. `docs/project-truth/architecture-truth.md`
4. `docs/project-truth/runtime-flows.md`
5. `docs/project-truth/data-model.md`
6. `docs/Planning/Plan.md`
7. `ENTRYLENS_BUILD_PLAN.md` (root - current build instructions)
8. `docs/Planning/archive/ENTRYLENS_MASTER_PLAN_reference.md` (archived - broader product vision)

## Read This First

For most future agent sessions, start with this tighter subset instead of loading everything:

1. Read [`docs/agents.md`](/d:/Testproject2/VisitorsTrackers/docs/agents.md).
2. Read [`docs/project-truth/repo-map.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/repo-map.md).
3. Read [`docs/project-truth/architecture-truth.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/architecture-truth.md).
4. Read [`docs/tasks/lessons.md`](/d:/Testproject2/VisitorsTrackers/docs/tasks/lessons.md).

Then expand only as needed:

- add `docs/project-truth/runtime-flows.md` for route or operator flow work
- add `docs/project-truth/data-model.md` for schema or contract work
- add `docs/Planning/Plan.md` before non-trivial multi-step implementation
- read `ENTRYLENS_BUILD_PLAN.md` for current implementation instructions
- read `docs/Planning/archive/ENTRYLENS_MASTER_PLAN_reference.md` only if you need the broader product vision from the original master plan

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
- `ENTRYLENS_BUILD_PLAN.md`
  Current build instructions for implementing the local recognition pipeline.
- `ENTRYLENS_ARCHITECTURE.md`
  Main product design source.
- `docs/Planning/archive/ENTRYLENS_MASTER_PLAN_reference.md`
  Original master plan archived for broader context (product vision, sprints, epics).

## Quick Reference Rules

- State what exists in this repo now, not what the architecture intends later.
- Treat [`ENTRYLENS_ARCHITECTURE.md`](/d:/Testproject2/VisitorsTrackers/ENTRYLENS_ARCHITECTURE.md) as the main product design source.
- Treat [`ENTRYLENS_BUILD_PLAN.md`](/d:/Testproject2/VisitorsTrackers/ENTRYLENS_BUILD_PLAN.md) as the current execution source.
- Use [`docs/Planning/archive/ENTRYLENS_MASTER_PLAN_reference.md`](/d:/Testproject2/VisitorsTrackers/docs/Planning/archive/ENTRYLENS_MASTER_PLAN_reference.md) only when you need broader context about original product vision.
- Do not claim paths like `sentinel-api/` or `sentinel-frontend/` exist unless they are actually added to the repo.
- Update `docs/project-truth/*` when repo reality changes.



<!-- graphify-links:start -->
## Graph Links

- [[graphify-out/wiki/index|Graphify Wiki]]
- [[graphify-out/GRAPH_REPORT|Graph Report]]
<!-- graphify-links:end -->
