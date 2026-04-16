# Azure Face Detect Playground Plan

## Status

Status on April 11, 2026:

- this is a smaller Azure experiment focused on face detection only
- this plan does not depend on Azure identification or verification features
- the goal is to test whether Azure can still be useful for bounding-box detection and face analysis even though identity features are paused

## Task Summary

Create a dedicated playground for Azure Face detection-only flows so we can validate face rectangles, optional face attributes, and image handling outside the main EntryLens app.

The goal is to prove this narrower path first:

1. send a local image to Azure Face detect
2. receive `faceRectangle` data
3. optionally inspect any safe detection-time metadata we request
4. save a JSON result and an annotated preview image
5. compare Azure detection output with MediaPipe results on the same image

This plan is based on:

- [`ENTRYLENS_ARCHITECTURE.md`](/d:/Testproject2/VisitorsTrackers/ENTRYLENS_ARCHITECTURE.md)
- [`ENTRYLENS_MASTER_PLAN.md`](/d:/Testproject2/VisitorsTrackers/ENTRYLENS_MASTER_PLAN.md)
- [`2026-04-10-azure-face-playground.md`](/d:/Testproject2/VisitorsTrackers/docs/old/Planning/2026-04-10-azure-face-playground.md)
- [`2026-04-11-compreface-playground.md`](/d:/Testproject2/VisitorsTrackers/docs/old/Planning/2026-04-11-compreface-playground.md)

## Why This Exists Separately

- Azure identity features are blocked for the current project path.
- Detection-only is a different and much smaller technical question than recognition.
- If Azure detect works for this resource, it may still be useful for bounding boxes or offline evaluation even if identification stays unusable.
- Keeping detect-only separate prevents confusion with the paused Azure identity playground.

## Playground Separation Rule

All provider or detection experiments should live under:

- `playgrounds/`

This detect-only experiment should live in:

- `playgrounds/azure-face-detect-playground/`

Related but separate playgrounds:

- `playgrounds/azure-face-playground/` for paused identity experiments
- `playgrounds/compreface-playground/` for active non-Azure recognition experiments

## Can Azure And MediaPipe Both Be Used?

Yes, and they serve different jobs.

Recommended split:

- MediaPipe runs locally in the browser for fast face presence, landmarks, rough pose checks, and capture gating
- Azure Face detect runs as a separate remote check for `faceRectangle` output and optional server-side face analysis supported by the resource

Practical interpretation:

- MediaPipe is still the better candidate for real-time front-end gating
- Azure detect is useful as a playground experiment, a comparison tool, or a fallback bbox source if access and latency are acceptable
- detection from Azure should not be treated as a replacement for the provider abstraction used for identity recognition

## Current Repo Truth

- the repo contains no implemented playground yet
- the Azure identity path is parked due to approval constraints
- the architecture already includes MediaPipe on the client side
- the backend provider shape remains useful for recognition providers, but Azure detect-only may stay outside that abstraction unless we choose to expose it as a utility service later

## Recommended Playground Location

- `playgrounds/azure-face-detect-playground/`

Recommended stack:

- Node.js + TypeScript

Reason:

- it stays consistent with the other planned playgrounds
- it is a good fit for a small CLI that reads local images and writes output artifacts
- it avoids coupling experimentation to the production Python app too early

## Playground Scope

### Included In Playground

- read local images from disk
- call Azure Face detect for one image or a folder of images
- print raw detect responses
- normalize returned face rectangles
- draw bbox overlays onto copies of the input images
- save JSON artifacts for later comparison
- optionally run a local comparison mode against MediaPipe output if we add that later

### Explicitly Excluded For Now

- Azure identify
- Azure verify
- person groups
- enrollment
- production API routes
- dashboard integration
- attendance logs

## Proposed Files

### New Playground Files

- `playgrounds/azure-face-detect-playground/package.json`
- `playgrounds/azure-face-detect-playground/tsconfig.json`
- `playgrounds/azure-face-detect-playground/.env.example`
- `playgrounds/azure-face-detect-playground/src/config.ts`
- `playgrounds/azure-face-detect-playground/src/client.ts`
- `playgrounds/azure-face-detect-playground/src/types.ts`
- `playgrounds/azure-face-detect-playground/src/filesystem.ts`
- `playgrounds/azure-face-detect-playground/src/annotate.ts`
- `playgrounds/azure-face-detect-playground/src/normalize.ts`
- `playgrounds/azure-face-detect-playground/src/commands/detect.ts`
- `playgrounds/azure-face-detect-playground/src/commands/detect-folder.ts`
- `playgrounds/azure-face-detect-playground/src/index.ts`
- `playgrounds/azure-face-detect-playground/README.md`

### Test Asset Layout

- `playgrounds/azure-face-detect-playground/test-data/input/`
- `playgrounds/azure-face-detect-playground/output/json/`
- `playgrounds/azure-face-detect-playground/output/annotated/`

## Test Data Convention

Suggested layout:

- `test-data/input/one-face.jpg`
- `test-data/input/two-faces.jpg`
- `test-data/input/no-face.jpg`

Rules:

- start with a tiny set of known images
- include at least one single-face image
- include at least one multi-face image
- include one negative case with no clear face

## CLI Shape

The playground should behave like a small command runner:

```text
npm run playground -- detect --file ./test-data/input/one-face.jpg
npm run playground -- detect-folder --dir ./test-data/input
```

Optional later comparison mode:

```text
npm run playground -- compare-mediapipe --file ./test-data/input/one-face.jpg
```

## Environment Variables

The playground should read:

- `AZURE_FACE_API_KEY`
- `AZURE_FACE_ENDPOINT`

Optional playground-only vars:

- `AZURE_FACE_DETECT_MODEL=detection_03`
- `AZURE_FACE_DETECT_OUTPUT_DIR=./output`
- `AZURE_FACE_DETECT_RETURN_FACE_ID=false`

Important note:

- keep `returnFaceId` off by default unless there is a verified need and the resource supports it
- the purpose here is bounding-box detection, not identity workflows

## Implementation Steps

### Phase A: Playground Scaffold

1. Create `playgrounds/azure-face-detect-playground/`.
2. Initialize a small TypeScript CLI package.
3. Add env loading and argument parsing.
4. Add a README that explains setup, test-data layout, and commands.

### Phase B: Azure Detect Client

1. Add a thin Azure detect client wrapper.
2. Validate endpoint and API key on startup.
3. Add a single-image detect command.
4. Write raw responses to JSON.

### Phase C: Annotation Output

1. Normalize `faceRectangle` output.
2. Draw bounding boxes on a copied image.
3. Save annotated images into `output/annotated/`.
4. Print a concise summary to the console:
   - face count
   - rectangles
   - any service errors

### Phase D: Folder Batch Mode

1. Add folder traversal for multiple test images.
2. Write one JSON artifact per image.
3. Write a small aggregate run summary.
4. Identify obvious success and failure patterns.

### Phase E: Optional MediaPipe Comparison

1. Add a local comparison command if it becomes useful.
2. Run MediaPipe on the same image set.
3. Compare face count and bbox overlap at a coarse level.
4. Use the results to decide whether Azure detect adds enough value beyond MediaPipe.

## How This Maps Back Into EntryLens

If this experiment works, the likely integration paths are:

1. keep MediaPipe as the real-time browser gate
2. optionally use Azure detect as a diagnostic or comparison tool
3. only promote Azure detect into main app code if it solves a real problem MediaPipe does not solve well enough

This playground may never become a production dependency, and that is fine. Its job is to answer a bounded technical question cheaply.

## Risks And Early Checks

### Access Limitation

- even detect-only usage may still depend on Azure Face service access for the resource
- the very first check should be one minimal detect call with a known input image

### Latency

- Azure detect is remote and will be slower than local MediaPipe gating
- that makes it a poor fit for per-frame browser loops unless there is a very strong reason

### Cost And Rate Limits

- batch experiments should be kept small
- the playground should make failures visible and avoid pretending detection is reliable if requests are throttled or blocked

## Verification Steps

### Playground Verification

1. place at least three sample images in `test-data/input/`
2. run `detect` on one known single-face image
3. confirm JSON output contains at least one `faceRectangle`
4. confirm an annotated image is written to `output/annotated/`
5. run `detect-folder`
6. confirm face counts look reasonable across positive and negative examples

### Decision Gate

Do not wire Azure detect into the main app until these are true:

- detect-only calls succeed consistently for the current resource
- output artifacts show that bbox quality is actually useful
- the added latency and cloud dependency are justified compared with MediaPipe alone

## Recommended Immediate Next Task

Start with the smallest useful slice:

1. create `playgrounds/azure-face-detect-playground/`
2. add env loading and a single `detect --file` command
3. save raw JSON plus one annotated image
4. test with one known sample image before adding folder mode

That keeps the experiment tight, reversible, and clearly separate from both Azure identity work and the active CompreFace recognition path.




<!-- graphify-links:start -->
## Graph Links

- [[graphify-out/wiki/index|Graphify Wiki]]
- [[graphify-out/GRAPH_REPORT|Graph Report]]
<!-- graphify-links:end -->
