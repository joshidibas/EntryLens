# Azure Face Playground Plan

## Status

Status on April 11, 2026:

- this path is paused for now
- the Azure playground did not fail because of local implementation alone
- the real blocker is Azure Face identification or verification access requirements, including ACE recognition approval and related eligibility steps
- that approval path does not fit the current project goal, so this should be treated as a parked experiment rather than an active delivery track

Practical conclusion:

- keep this document as research history
- do not treat the playground as the next implementation step
- revisit only if the project later decides to pursue the required approval track for Azure facial identification features
- keep Azure experiments isolated under `playgrounds/azure-face-playground/` if this path is ever resumed

## Task Summary

Create a focused test playground for Azure Face identity workflows before building more product features.

The goal is to validate the real Azure recognition path first:

1. create or reuse a Large Person Group
2. create people inside that group
3. add training images
4. train the group
5. detect and identify a face against that trained group
6. optionally verify the detected face against the identified person
7. inspect the raw results and confidence values outside the main app flow

This plan is based on:

- [`ENTRYLENS_ARCHITECTURE.md`](/d:/Testproject2/VisitorsTrackers/ENTRYLENS_ARCHITECTURE.md)
- [`ENTRYLENS_MASTER_PLAN.md`](/d:/Testproject2/VisitorsTrackers/ENTRYLENS_MASTER_PLAN.md)
- Azure Face quickstart:
  https://learn.microsoft.com/en-us/azure/ai-services/face/quickstarts-sdk/identity-client-library?tabs=windows%2Cvisual-studio&pivots=programming-language-javascript

## Why This Comes Before More Product Features

- The current repo has a runnable UI shell, but the Azure provider is still a stub.
- The Azure quickstart shows the hardest external dependency path first: group creation, person creation, face enrollment, training, detection, identification, and verification.
- Validating that path in isolation will reduce risk before we wire real enroll and recognize routes into EntryLens.
- A playground gives us a safe place to learn Azure request and response shapes, rate limits, and failure modes without muddying the main app code too early.

## Current Repo Truth

- `entrylens-api/app/providers/azure_provider.py` is currently a scaffold that returns placeholder values only.
- No real Azure SDK or HTTP integration exists in the backend yet.
- No enrollment route exists yet.
- No recognition route exists yet.
- No persistent identity storage exists yet.
- The current `.env` already contains placeholders for:
  - `AZURE_FACE_API_KEY`
  - `AZURE_FACE_ENDPOINT`
  - `AZURE_PERSON_GROUP_ID`

## Review Notes From The Azure Quickstart

The quickstart's JavaScript path centers on these Azure operations:

1. detect faces with `detection_03`
2. use `recognition_04`
3. create a `LargePersonGroup`
4. create one `Person` per identity
5. add persisted faces to each person
6. train the large person group
7. poll until training succeeds
8. detect source faces for recognition
9. call identify against the large person group
10. optionally call verify for the selected candidate
11. delete the person group during cleanup

Important implementation implications:

- Azure Face identity access is limited and may require approval before identification features work.
- In practice for this project, the approval path appears to require ACE recognition or equivalent access review steps that are not a fit for the current intended use.
- The quickstart filters enrollment inputs using `qualityForRecognition`; only high-quality images should be enrolled.
- Face IDs are temporary and used only for later identify or verify calls.
- Training is asynchronous and must be polled.
- Free-tier and limited-access usage can trigger throttling, so the playground should surface rate-limit behavior clearly.

## Recommended Direction

Build the playground as a separate, disposable integration tool first, not as direct product code.

Recommended location:

- `playgrounds/azure-face-playground/`

Recommended stack for the playground:

- Node.js + TypeScript

Reason:

- The linked quickstart is already in JavaScript or TypeScript terms.
- This lowers translation risk while we are still learning the Azure flow.
- It keeps experimentation isolated from the production FastAPI provider abstraction.

The main EntryLens backend should still remain Python and should later absorb the validated Azure behavior behind `FaceProvider`.

## Playground Scope

### Included In Playground

- create or reuse a named Large Person Group
- create persons from local test identities
- enroll local sample images into Azure
- run training and poll for completion
- run detection on a probe image
- run identify and verify
- print raw and normalized output to console
- write a small JSON artifact with the run results
- support cleanup of the test group

### Explicitly Excluded For Now

- frontend camera capture
- MediaPipe gating
- database writes
- attendance logs
- debounce
- MinIO
- WebSocket feed
- dashboard integration

## Proposed Files

### New Playground Files

- `playgrounds/azure-face-playground/package.json`
- `playgrounds/azure-face-playground/tsconfig.json`
- `playgrounds/azure-face-playground/.env.example`
- `playgrounds/azure-face-playground/src/config.ts`
- `playgrounds/azure-face-playground/src/client.ts`
- `playgrounds/azure-face-playground/src/types.ts`
- `playgrounds/azure-face-playground/src/filesystem.ts`
- `playgrounds/azure-face-playground/src/commands/enroll.ts`
- `playgrounds/azure-face-playground/src/commands/identify.ts`
- `playgrounds/azure-face-playground/src/commands/verify.ts`
- `playgrounds/azure-face-playground/src/commands/train.ts`
- `playgrounds/azure-face-playground/src/commands/cleanup.ts`
- `playgrounds/azure-face-playground/src/index.ts`
- `playgrounds/azure-face-playground/README.md`

### Test Asset Layout

- `playgrounds/azure-face-playground/test-data/enroll/<person-name>/`
- `playgrounds/azure-face-playground/test-data/probe/`
- `playgrounds/azure-face-playground/output/`

## Test Data Convention

Use local image files rather than remote sample URLs so the playground reflects the real project setup better.

Suggested convention:

- `test-data/enroll/alice/1.jpg`
- `test-data/enroll/alice/2.jpg`
- `test-data/enroll/bob/1.jpg`
- `test-data/probe/alice-test.jpg`

Rules:

- each enrolled person should start with 2 to 5 clean face images
- each enrollment image should ideally contain exactly one face
- probe images can contain one face for early validation
- keep data small and disposable

## CLI Shape

The playground should behave like a small command runner:

```text
npm run playground -- init-group
npm run playground -- enroll
npm run playground -- train
npm run playground -- identify --file ./test-data/probe/alice-test.jpg
npm run playground -- verify --file ./test-data/probe/alice-test.jpg --person alice
npm run playground -- cleanup
```

Or, if preferred, support a single happy-path command:

```text
npm run playground -- full-run --file ./test-data/probe/alice-test.jpg
```

## Environment Variables

The playground should read:

- `AZURE_FACE_API_KEY`
- `AZURE_FACE_ENDPOINT`
- `AZURE_PERSON_GROUP_ID`

Optional playground-only vars:

- `AZURE_PLAYGROUND_GROUP_NAME`
- `AZURE_PLAYGROUND_RECOGNITION_MODEL=recognition_04`
- `AZURE_PLAYGROUND_DETECTION_MODEL=detection_03`
- `AZURE_PLAYGROUND_OUTPUT_DIR=./output`
- `AZURE_PLAYGROUND_RECREATE_GROUP=false`

Use the existing repo-level Azure env vars where possible so credentials are not duplicated.

## Implementation Steps

### Phase A: Playground Scaffold

1. Create the `playgrounds/azure-face-playground/` folder.
2. Initialize a small TypeScript CLI package.
3. Add env loading and argument parsing.
4. Add a README that explains test-data layout and commands.

### Phase B: Azure Client And Config

1. Add the Azure Face client package and supporting helpers.
2. Centralize config validation.
3. Fail fast when credentials are missing.
4. Surface the limited-access prerequisite clearly in startup output.

### Phase C: Enrollment Flow

1. Read local enroll folders.
2. Create or reuse the Large Person Group.
3. Create or map Azure persons from folder names.
4. Detect quality for each enrollment image.
5. Skip images that are not high quality or do not contain exactly one face.
6. Add valid faces as persisted faces.
7. Emit a machine-readable enrollment summary.

### Phase D: Training Flow

1. Start training for the group.
2. Poll until training completes or fails.
3. Print detailed status and write the result to `output/`.

### Phase E: Identification And Verification Flow

1. Detect face IDs from a local probe image.
2. Run identify against the trained group.
3. Resolve returned `personId` values back to Azure person names.
4. Optionally run verify for the top candidate.
5. Print both raw Azure output and a normalized summary.

### Phase F: Cleanup And Repeatability

1. Add cleanup command to delete the playground group.
2. Add an option to recreate the group from scratch.
3. Preserve output artifacts for comparison between runs.

## How This Maps Back Into EntryLens

Once the playground is working, the migration path into the main app should be:

1. move Azure client construction logic into `entrylens-api/app/providers/azure_provider.py`
2. move normalized Azure response mapping into provider schemas
3. implement `provider.enroll()` using the validated enrollment logic
4. implement `provider.identify()` using the validated detect plus identify logic
5. keep verification as a playground or admin-only diagnostic first, not a core route dependency

This keeps the playground as the proving ground and the FastAPI provider as the production wrapper.

## Risks And Early Checks

### Limited Access

- Identification may fail if the Azure Face resource does not have approval for facial identification use.
- Before coding deeply, confirm the resource is approved for the documented identification use case.
- Current observed blocker on April 10, 2026: `init-group` reached Azure and returned `403 Unsupported Feature` with inner error `UnsupportedFeature`, stating the resource is missing approval for `Identification,Verification` and directing access requests to `https://aka.ms/facerecognition`.
- Current project decision on April 11, 2026: stop pursuing this path for now because the required ACE recognition or related approval process is not workable for the present use case.

### SDK Drift

- The linked quickstart uses JavaScript or TypeScript APIs that may not map one-to-one to Python.
- That is why the playground should stay in Node or TypeScript first.

### Image Quality

- Enrollment can look broken when the real issue is poor input data.
- The playground should explicitly report:
  - number of faces detected
  - quality-for-recognition result
  - whether the image was skipped

### Rate Limits

- Free-tier throttling can distort early testing.
- The playground should log 429 responses clearly and recommend retry timing.

## Verification Steps

### Playground Verification

1. Place 2 to 5 images per person in `test-data/enroll/`.
2. Put one probe image in `test-data/probe/`.
3. Run `init-group` or `full-run`.
4. Confirm the group is created in Azure.
5. Confirm people are created in Azure.
6. Confirm at least one persisted face is added per valid person.
7. Confirm training reaches `succeeded`.
8. Run `identify` against the probe image.
9. Confirm the top returned candidate maps to the expected person when the probe is known.
10. Run `cleanup` and confirm the group is deleted if cleanup is requested.

### EntryLens Readiness Gate

Do not wire the main `AzureProvider` until these are true:

- local playground commands succeed repeatedly
- the normalized results are stable enough to map into `ProviderResponse`
- the expected Azure error cases are understood:
  - no face detected
  - low quality image
  - no candidates returned
  - training not completed
  - limited access or permission failure
  - rate limit response

## Docs Update Checklist

When implementation starts:

- update [`docs/tasks/todo.md`](/d:/Testproject2/VisitorsTrackers/docs/tasks/todo.md)
- update [`docs/project-truth/repo-map.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/repo-map.md)
- update [`docs/project-truth/architecture-truth.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/architecture-truth.md)
- append progress to [`docs/project-truth/changelog.md`](/d:/Testproject2/VisitorsTrackers/docs/project-truth/changelog.md)

## Recommended Immediate Next Task

Do not continue implementation right now.

If revisited later, restart with the smallest possible proof step:

1. create `playgrounds/azure-face-playground/`
2. add env loading and Azure client setup
3. add `init-group`, `enroll`, `train`, `identify`, and `cleanup` commands
4. test with a tiny local image set before touching the main FastAPI provider

Until Azure access requirements change, this plan should remain archived as a blocked option rather than an active next move.
