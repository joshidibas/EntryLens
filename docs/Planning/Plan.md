# Planning Rules

## Purpose

This file defines how non-trivial work should be planned in this repository.

## When Planning Is Required

Planning is required when work includes any of the following:

- creating multiple new files or folders
- implementing more than one subsystem
- changing architecture, auth, storage, or provider boundaries
- work that depends on both root planning docs
- any task that will take multiple steps to verify

## Required Workflow

1. Read [`docs/agents.md`](/d:/Testproject2/VisitorsTrackers/docs/agents.md).
2. Read [`docs/tasks/lessons.md`](/d:/Testproject2/VisitorsTrackers/docs/tasks/lessons.md) - this is mandatory to avoid past mistakes.
3. Confirm current repo truth in [`docs/project-truth/architecture-truth.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/architecture-truth.md).
4. Read only the relevant sections of the root architecture and master plan docs.
5. Write or update a plan file before large implementation work.
6. Execute in small checkpoints.
7. Verify actual repo artifacts, not planned artifacts.
8. Update project-truth docs if repo reality changed.

## Default Plan Destination

Store plans in `docs/Planning/`.

Archived or completed plans belong in `docs/Planning/old/`.

## Plan File Naming Convention

Use:

- `docs/Planning/YYYY-MM-DD-short-task-name.md`

When a user says to move a plan to old, archive a finished plan, or mark a plan complete, move that dated plan file into:

- `docs/Planning/old/YYYY-MM-DD-short-task-name.md`

Example:

- `docs/Planning/2026-04-10-bootstrap-sentinel-api.md`

## What Each Plan Should Include

- task summary
- current repo truth
- assumptions
- file paths expected to change
- implementation steps
- verification steps
- docs update checklist

## Verification Rule

Do not mark work complete until verification is tied to actual files or runtime behavior present in the repository.

If code does not exist yet, the plan should say that directly.

## Plan Archive Rule

When a dated plan is no longer active:

- move it from `docs/Planning/` to `docs/Planning/old/`
- treat "move the plan to old" and "mark the plan complete" as the same archive action unless the user says otherwise
- when user explicitly says "mark as completed", "plan complete", "move to old folder", or similar, immediately move the plan file to `docs/Planning/old/` with prefix `completed-`
- keep `docs/Planning/Plan.md` in place as the active planning workflow guide

## Docs Update Rule

Any change that affects repo structure, architecture truth, runtime flows, or data model expectations must update:

- the relevant file in `docs/project-truth/`
- `docs/project-truth/changelog.md`
- `docs/tasks/todo.md` when the task is active



<!-- graphify-links:start -->
## Graph Links

- [[graphify-out/wiki/index|Graphify Wiki]]
- [[graphify-out/GRAPH_REPORT|Graph Report]]
<!-- graphify-links:end -->
