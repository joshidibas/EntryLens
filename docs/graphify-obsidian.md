---
title: Graphify + Obsidian Workflow
tags:
  - graphify
  - obsidian
  - docs
---

# Graphify + Obsidian Workflow

This repository can use three layers together:

1. `docs/` for narrative project knowledge and decisions
2. `graphify-out/` for structural code intelligence
3. Obsidian as the local navigation and graph-view UI

## Refresh Flow

Run this from the repo root:

```powershell
.\scripts\refresh_graphify_obsidian.ps1
```

That does two things:

1. regenerates `graphify-out/graph.json` and `graphify-out/GRAPH_REPORT.md`
2. regenerates `graphify-out/wiki/` and refreshes generated graph links inside docs

## Where To Start In Obsidian

Open the repo root as your vault, then start here:

- [[graphify-out/wiki/index|Graphify Wiki]]
- [[graphify-out/GRAPH_REPORT|Graph Report]]
- [[docs/README|Docs README]]
- [[docs/project-truth/repo-map|Repo Map]]

## How The Pieces Connect

- Docs now include a generated `Graph Links` section.
- File notes inside `graphify-out/wiki/` link back to the docs that mention them.
- Community notes group related files and symbols from the Graphify graph.
- Obsidian backlinks and Graph View can now traverse across docs, graph notes, and source-file notes.

## Recommended Usage Pattern

Use `docs/` when you want intent, plans, and current truth.

Use `graphify-out/wiki/` when you want code structure, hot spots, and connected symbols.

Use Obsidian Graph View or backlinks when you want to move between those two worlds quickly.


<!-- graphify-links:start -->
## Graph Links

- [[graphify-out/wiki/index|Graphify Wiki]]
- [[graphify-out/GRAPH_REPORT|Graph Report]]
<!-- graphify-links:end -->
