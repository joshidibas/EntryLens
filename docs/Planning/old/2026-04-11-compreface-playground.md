# CompreFace Playground Plan

## Status

Status on April 11, 2026:

- this is the active playground direction replacing Azure for near-term experimentation
- the goal is to validate a non-Azure recognition path that avoids ACE recognition or similar approval gating
- this playground should stay isolated from main app code until the request and response flow is proven

## Task Summary

Create a provider-specific playground for CompreFace so we can validate enrollment and recognition outside the main EntryLens app flow.

The goal is to prove the core path first:

1. start or connect to a CompreFace instance
2. create or configure a recognition service
3. enroll identities from local test images
4. run recognition against local probe images
5. inspect raw responses and normalized provider-shaped output
6. record what maps cleanly into the `FaceProvider` contract

This plan is based on:

- [`ENTRYLENS_ARCHITECTURE.md`](/d:/Testproject2/VisitorsTrackers/ENTRYLENS_ARCHITECTURE.md)
- [`ENTRYLENS_MASTER_PLAN.md`](/d:/Testproject2/VisitorsTrackers/ENTRYLENS_MASTER_PLAN.md)
- the existing Azure playground planning doc kept as a paused reference:
  [`2026-04-10-azure-face-playground.md`](/d:/Testproject2/VisitorsTrackers/docs/old/Planning/2026-04-10-azure-face-playground.md)

## Why This Direction Fits Better Now

- Azure identification is blocked by approval requirements that do not fit the present use case.
- The architecture already anticipates a provider-agnostic backend and a future CompreFace provider.
- A self-hosted playground gives us faster iteration on enrollment and recognition behavior without depending on cloud feature access.
- The playground lets us learn the provider contract before wiring anything into FastAPI routes or the dashboard loop.

## Playground Separation Rule

All provider experiments should live in a dedicated repo folder:

- `playgrounds/`

Each provider gets its own isolated subfolder:

- `playgrounds/azure-face-playground/`
- `playgrounds/compreface-playground/`

Reason:

- provider experiments stay disposable
- package dependencies do not leak into the main app too early
- switching direction later does not create confusion in `entrylens-api/`
- docs and test data can stay next to the experiment they belong to

## Current Repo Truth

- the repo currently has planning docs but no implemented provider playground
- the backend provider abstraction is still the right long-term shape
- no CompreFace playground folder exists yet
- no CompreFace provider implementation exists yet
- Azure research is now parked, not deleted

## Recommended Playground Location

- `playgrounds/compreface-playground/`

Recommended stack for the playground:

- Node.js + TypeScript

Reason:

- it keeps parity with the previous playground exploration style
- it is a good fit for a small CLI runner
- it keeps the experiment independent from the production Python backend

The main EntryLens backend should still remain Python and should later absorb validated behavior behind `FaceProvider`.

## Playground Scope

### Included In Playground

- read config from a local `.env`
- call CompreFace REST endpoints directly
- create or select a recognition service context
- enroll persons from local image folders
- recognize faces from local probe images
- print raw API responses
- print normalized provider-shaped summaries
- write JSON output artifacts for comparison between runs
- optionally clear or recreate test subjects

### Explicitly Excluded For Now

- frontend camera capture
- MediaPipe quality gating
- database writes
- attendance logs
- WebSocket feed
- dashboard integration
- production auth wiring

## Proposed Files

### New Playground Files

- `playgrounds/compreface-playground/package.json`
- `playgrounds/compreface-playground/tsconfig.json`
- `playgrounds/compreface-playground/.env.example`
- `playgrounds/compreface-playground/src/config.ts`
- `playgrounds/compreface-playground/src/client.ts`
- `playgrounds/compreface-playground/src/types.ts`
- `playgrounds/compreface-playground/src/filesystem.ts`
- `playgrounds/compreface-playground/src/normalize.ts`
- `playgrounds/compreface-playground/src/commands/enroll.ts`
- `playgrounds/compreface-playground/src/commands/recognize.ts`
- `playgrounds/compreface-playground/src/commands/list-subjects.ts`
- `playgrounds/compreface-playground/src/commands/delete-subject.ts`
- `playgrounds/compreface-playground/src/index.ts`
- `playgrounds/compreface-playground/README.md`

### Test Asset Layout

- `playgrounds/compreface-playground/test-data/enroll/<person-name>/`
- `playgrounds/compreface-playground/test-data/probe/`
- `playgrounds/compreface-playground/output/`

## Test Data Convention

Use local image files so the playground matches the intended project workflow.

Suggested convention:

- `test-data/enroll/alice/1.jpg`
- `test-data/enroll/alice/2.jpg`
- `test-data/enroll/bob/1.jpg`
- `test-data/probe/alice-test.jpg`

Rules:

- each enrolled identity should start with 2 to 5 clean face images
- each enrollment image should ideally contain exactly one face
- probe images should start with one clear face
- keep the dataset small and disposable

## CLI Shape

The playground should behave like a small command runner:

```text
npm run playground -- enroll
npm run playground -- recognize --file ./test-data/probe/alice-test.jpg
npm run playground -- list-subjects
npm run playground -- delete-subject --subject alice
```

Or support a repeatable happy-path command:

```text
npm run playground -- full-run --file ./test-data/probe/alice-test.jpg
```

## Environment Variables

The playground should read:

- `COMPREFACE_URL`
- `COMPREFACE_API_KEY`
- `COMPREFACE_RECOGNITION_SERVICE_KEY`
- `COMPREFACE_DETECTION_SERVICE_KEY`

Optional playground-only vars:

- `COMPREFACE_PLAYGROUND_OUTPUT_DIR=./output`
- `COMPREFACE_PLAYGROUND_SIMILARITY_THRESHOLD=0.75`
- `COMPREFACE_PLAYGROUND_RECREATE_SUBJECTS=false`

Use repo-level provider env conventions where practical, but keep playground-specific flags local to this tool.

## Implementation Steps

### Phase A: Playground Scaffold

1. Create the `playgrounds/compreface-playground/` folder.
2. Initialize a small TypeScript CLI package.
3. Add env loading and argument parsing.
4. Add a README that explains local setup, test-data layout, and commands.

### Phase B: Client And Config

1. Add a thin CompreFace client wrapper around the needed REST calls.
2. Centralize config validation.
3. Fail fast when required env vars are missing.
4. Print clear startup errors when the CompreFace service is unreachable.

### Phase C: Enrollment Flow

1. Read local enroll folders.
2. Map folder names to CompreFace subjects.
3. Upload enrollment images for each subject.
4. Record raw API responses and a normalized summary per subject.
5. Emit a machine-readable enrollment artifact in `output/`.

### Phase D: Recognition Flow

1. Read a local probe image.
2. Call the recognition endpoint.
3. Capture raw matches, similarity, and subject values.
4. Convert the response into a provider-shaped summary:
   - `subject_id`
   - `similarity`
   - `raw_response`
5. Save results to `output/`.

### Phase E: Subject Management And Repeatability

1. Add subject listing for quick inspection.
2. Add subject deletion or reset helpers for disposable testing.
3. Preserve result artifacts between runs for comparison.

## How This Maps Back Into EntryLens

Once the playground is working, the migration path into the main app should be:

1. implement `entrylens-api/app/providers/compreface_provider.py`
2. move client construction logic into the provider layer
3. map CompreFace recognition responses into `ProviderResponse`
4. map enrollment results into `EnrollResponse`
5. keep route handlers and services calling only the provider abstraction

This keeps the playground as the proving ground and the FastAPI provider as the production wrapper.

## Risks And Early Checks

### Service Availability

- if CompreFace is not running or reachable, the playground should fail clearly and early
- the first proof step should be a simple connectivity call before building deeper command flow

### Response Shape Drift

- provider mapping should not assume the API returns the exact field names we want long term
- raw responses should always be captured alongside normalized summaries

### Local Resource Overhead

- CompreFace may be heavier than the current machine comfortably supports if fully containerized with all services
- if that becomes a blocker, the playground should still preserve the API contract work and help us decide whether to use another lightweight provider or remote host later

## Verification Steps

### Playground Verification

1. start or connect to a working CompreFace instance
2. place 2 to 5 images per person in `test-data/enroll/`
3. put one probe image in `test-data/probe/`
4. run `enroll`
5. confirm the expected subjects exist in CompreFace
6. run `recognize` against the probe image
7. confirm the top returned subject matches the expected person when the probe is known
8. confirm a normalized JSON artifact is written to `output/`
9. run subject cleanup if desired and confirm disposable test identities are removed

### EntryLens Readiness Gate

Do not wire the main `CompreFaceProvider` until these are true:

- local playground commands succeed repeatedly
- the normalized results map cleanly into `ProviderResponse`
- the expected error cases are understood:
  - no face detected
  - multiple faces
  - no matches returned
  - service unavailable
  - bad API key or service key

## Recommended Immediate Next Task

Start with the smallest useful playground slice:

1. create `playgrounds/compreface-playground/`
2. add env loading and a connectivity check
3. add `enroll` and `recognize` commands only
4. test with a tiny local image set before touching the main FastAPI provider

That keeps the next step tight, reversible, and aligned with the provider abstraction already defined in the project docs.
