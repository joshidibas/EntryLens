# Backend Model Runtime Transition Plan

## Task Summary

Transition the current experimental `InsightFace (Colab)` direction into a backend-hosted model runtime that runs directly inside the EntryLens backend or behind a backend-owned local service boundary.

The architecture should preserve the current Labs model picker idea, but make model selection plug-and-play so new models, different model families, or multiple models can be added later without rewriting route handlers or the frontend flow each time.

---

## Current Repo Truth

The current repo already has several building blocks that make this transition feasible:

- the frontend can now send `model_id` through enroll, recognize, and sample-add flows
- backend routes already call a model-aware resolver in `entrylens-api/app/services/embedding_models.py`
- model-aware storage routing already exists in `entrylens-api/app/supabase.py`
- Supabase already has separate embedding tables and RPCs for:
  - `embeddings` with `vector(16)` for `local-default`
  - `insightface_embeddings` with `vector(512)` for `insightface-colab`
- Labs metadata already exposes multiple models through `entrylens-api/app/services/labs.py`
- current live detection and camera capture remain MediaPipe/browser-side and should stay that way for now

Current weak points:

- the InsightFace path still depends on `INSIGHTFACE_COLAB_URL`
- Colab is temporary, slow to wake, and operationally brittle
- the backend model resolver is still small and procedural, not yet a true pluggable registry
- there is no first-class abstraction yet for:
  - model capabilities
  - per-model storage rules
  - multiple active embedding families
  - future ensemble or multi-model matching strategies
- **[GAP]** no runner interface contract is enforced — runners are ad-hoc and duck-typed
- **[GAP]** no model health or readiness signal is surfaced to the frontend or operator
- **[GAP]** no model-specific structured error codes are returned to the client
- **[GAP]** no weight integrity check or version pinning for local model assets
- **[GAP]** no graceful fallback behavior when a model runner fails mid-request
- **[GAP]** `embedding_models.py` resolver is not tested in isolation — model selection logic has no unit coverage

---

## Goals

- remove Google Colab as the preferred inference host
- run InsightFace directly in the backend as the next default experimental path
- keep the frontend model-picker UX intact
- make model integration pluggable so future models can be added with minimal route changes
- support multiple embedding families without mixing incompatible vectors
- allow future use of more than one model at a time for the same identity set
- expose model health and readiness as first-class operational state
- enforce a runner interface contract so new runners are structurally validated, not assumed

---

## Non-Goals

- replacing browser-side MediaPipe face detection in this phase
- changing `/live` detection-log behavior unless required by the new backend model boundary
- collapsing all embeddings into one shared vector table
- introducing production-grade distributed model orchestration in the first transition step
- implementing every future model immediately
- GPU-accelerated inference in this phase
- model versioning or A/B traffic splitting in this phase

---

## Design Principles

### Keep Detection Separate From Embedding Inference

MediaPipe/browser-side face presence, basic gating, and current frame capture can remain as they are.

The transition should change embedding extraction and matching architecture, not the current camera UX.

### Make The Backend Own Model Execution

The frontend should only send:

- `model_id`
- image data when required
- local embedding only for models that explicitly accept browser-provided embeddings

The backend should decide:

- how embeddings are produced
- which model runner is used
- which storage table and RPC are used
- whether a model is available on this machine

### Model Metadata Must Be First-Class

Every model should expose metadata such as:

- `id`
- `label`
- `description`
- `embedding_dimension`
- `input_mode`
  - `browser-embedding`
  - `image-data`
- `storage_key`
- `matching_rpc`
- `availability`
- `status`
  - `ready`
  - `experimental`
  - `disabled`
- `health` — `ok`, `degraded`, or `unavailable` *(new)*
- `unavailable_reason` — human-readable string surfaced to Labs UI when not ready *(new)*
- `load_strategy` — `eager`, `lazy`, or `preloaded` *(new)*
- `weight_source` — where the model weights come from, for operator diagnostics *(new)*

This should become the single source of truth for Labs, routes, and storage routing.

### Do Not Mix Embedding Families

Different embedding dimensions and model families must remain isolated at the storage and matching layer.

Examples:

- `local-default` should continue using `vector(16)` and `match_embeddings`
- `insightface-local` should use `vector(512)` and `match_insightface_embeddings`
- future models should get their own table or a compatible shared table only when dimensions and similarity semantics truly match

### Prefer Additive Integration

The transition should rename or replace the Colab runtime path without destabilizing the current MediaPipe path.

### Enforce Runner Contracts Structurally

Every runner must implement a defined base interface. The registry should refuse to register a runner that does not satisfy it. This prevents silent drift where a new runner omits required behavior and only fails at inference time.

### Surface Errors With Model Context

When a model runner fails, the error returned to the client must include the `model_id` and a machine-readable `error_code`. Generic 500 responses with no model context are not acceptable in the new architecture.

---

## Proposed Architecture

### 1. Model Registry Layer

Create a backend-owned model registry that defines each supported recognition model in one place.

Responsibilities:

- return model metadata to Labs
- validate model IDs at request ingestion
- expose whether a model is available on the current machine
- expose how each model accepts input
- expose which storage path and match RPC belong to that model
- expose per-model health and readiness state

Suggested location: `entrylens-api/app/services/model_registry.py`

Interface:

- `get_registered_models() -> list[ModelDefinition]`
- `get_model_definition(model_id: str) -> ModelDefinition`
- `list_enabled_models() -> list[ModelDefinition]`
- `is_model_available(model_id: str) -> bool`
- `get_model_health(model_id: str) -> ModelHealth` *(new)*

`ModelDefinition` should be a typed Pydantic model, not a plain dict.

### 2. Model Runner Interface

Separate "which model is selected" from "how that model computes an embedding."

Base interface — every runner must implement:

```python
class BaseModelRunner(ABC):
    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def resolve_embedding(
        self,
        image_data_url: str | None,
        browser_embedding: list[float] | None,
        model_def: ModelDefinition,
    ) -> ResolvedEmbedding: ...

    @abstractmethod
    def health(self) -> ModelHealth: ...
```

Runners:

- `MediaPipeEmbeddingRunner` — accepts browser-provided embedding, passes it through
- `InsightFaceLocalRunner` — accepts image data URL, extracts 512-d embedding locally
- future: `ArcFaceRunner`, `FaceNetRunner`, `OpenCLIPFaceRunner`

Suggested module layout:

- `entrylens-api/app/services/model_runners/base.py`
- `entrylens-api/app/services/model_runners/mediapipe_browser.py`
- `entrylens-api/app/services/model_runners/insightface_local.py`

The registry should hold a runner instance per model ID and dispatch through the interface, never call runner methods directly from route handlers.

Important distinction:

- invalid runner registration is a startup/configuration error
- unavailable runner dependencies or missing weights are runtime availability states

That means:

- if a runner does not implement the required interface, app startup should fail fast
- if a runner is valid but its dependencies or weights are unavailable, the app should still boot and report the model as `health: unavailable`

### 3. Storage And Matching Router

Move model-specific storage decisions out of route handlers and out of scattered helper functions.

The model definition should declare:

- storage table
- similarity RPC
- embedding dimension

Responsibilities:

- `store_embedding_for_model(model_id, identity_id, embedding, metadata)`
- `search_embeddings_for_model(model_id, query_embedding, threshold, limit)`
- `count_embeddings_for_model(model_id, identity_id)`
- `delete_embeddings_for_model(model_id, identity_id)` *(new — needed for identity cleanup)*

This may stay in `app/supabase.py` initially, but routing decisions should come from the model registry instead of hard-coded `if model_id == ...` branches.

**[GAP addressed]** Add a dimension validation step before any insert: compare `len(embedding)` against `model_def.embedding_dimension` and reject mismatches with a structured error before they reach Supabase.

### 4. Capability-Driven Labs UI

The frontend should render model options from backend metadata only.

This avoids hand-maintaining parallel fallback definitions each time a model changes.

Frontend should trust backend metadata for:

- whether a model is enabled
- whether it needs image input or browser embedding input
- whether it is experimental
- whether the model is unavailable and why

**[GAP addressed]** The Labs UI should also consume and display `health` so the operator sees a degraded or unavailable model clearly rather than discovering it at inference time.

**[GAP addressed]** The frontend should render `unavailable_reason` inline next to disabled models in the picker, not only on hover or in a separate diagnostics view.

Single source of truth rule:

- the backend model registry is the canonical source of model metadata
- `labs.py` must not maintain its own independent copy of model definitions
- if Labs continues returning model metadata inside `/api/v1/labs`, it should do so by reading directly from the registry
- `GET /models` and `/api/v1/labs` must not diverge in shape or semantics for shared model fields

Preferred direction:

- keep `GET /api/v1/labs` as the UI bootstrap payload for the Labs page
- add `GET /models` and `GET /models/{model_id}/health` as diagnostics and reusable backend-facing metadata endpoints
- make `labs.py` delegate to the registry so there is still only one canonical model-definition source

### 5. Structured Error Response Contract

**[GAP — new section]**

When any model-related failure occurs, the API must return a structured error body rather than a bare HTTP error code. Suggested shape:

```json
{
  "error": "model_unavailable",
  "model_id": "insightface-local",
  "detail": "InsightFace weights not found at expected path.",
  "suggestion": "Run: pip install insightface and ensure weights are present."
}
```

Error codes to define:

- `model_not_found` — unknown `model_id` sent by client
- `model_unavailable` — model exists but dependencies or weights are missing
- `model_degraded` — model loaded but last inference returned anomalous output
- `input_mode_mismatch` — client sent browser embedding for an image-only model
- `embedding_dimension_mismatch` — stored embedding dimension does not match model definition
- `inference_failed` — runner raised an exception during embedding extraction

Route handlers should catch runner errors, map them to these codes, and return them consistently.

Frontend propagation rule:

- the frontend API client must preserve structured model errors instead of collapsing them to a plain message string
- UI flows should be able to read at least:
  - `error`
  - `model_id`
  - `detail`
  - `suggestion`

### 6. Optional Multi-Model Future Path

Design the registry so a future feature can:

- enroll the same identity into multiple model families
- recognize with one selected model
- or run multiple models and combine candidate results later

This future should not be implemented immediately, but the architecture should make it possible.

Recommended rule:

- per request, use one primary `model_id`
- per identity, allow samples across multiple model families
- later add optional multi-model comparison or fusion behind a separate feature flag

---

## Naming Direction

Replace the Colab-specific runtime naming with backend-owned names.

Recommended direction:

- keep existing historical `insightface-colab` data path readable for compatibility if needed
- introduce `insightface-local` as the active runtime model ID

Reason:

- it describes where inference happens from the app's point of view
- it leaves room for future `insightface-remote` or `insightface-gpu-node` variants if needed

---

## File Paths Expected To Change

### Backend

- `entrylens-api/app/config.py`
- `entrylens-api/app/services/labs.py`
- `entrylens-api/app/services/embedding_models.py`
- `entrylens-api/app/services/insightface_colab.py`
- `entrylens-api/app/supabase.py`
- `entrylens-api/app/routes/enroll.py`
- `entrylens-api/app/routes/recognize.py`
- `entrylens-api/app/routes/identities.py`
- `entrylens-api/app/schemas/enroll.py`
- `entrylens-api/app/schemas/recognize.py`
- `entrylens-api/app/schemas/identity.py`
- `entrylens-api/setup_supabase.sql`

### New Backend Modules

- `entrylens-api/app/services/model_registry.py`
- `entrylens-api/app/services/model_runners/base.py`
- `entrylens-api/app/services/model_runners/mediapipe_browser.py`
- `entrylens-api/app/services/model_runners/insightface_local.py`
- `entrylens-api/app/schemas/errors.py` *(new — structured error response shapes)*
- `entrylens-api/app/routes/models.py` *(new — health and diagnostics endpoint)*

### Frontend

- `entrylens-frontend/src/api/client.ts`
- `entrylens-frontend/src/pages/LabsPage.tsx`
- `entrylens-frontend/src/types.ts`
- `entrylens-frontend/src/api/labs.ts`
- `entrylens-frontend/src/api/enroll.ts`
- `entrylens-frontend/src/api/recognize.ts`
- `entrylens-frontend/src/api/identities.ts`
- `entrylens-frontend/src/hooks/useRecognitionSession.ts`

### Docs

- `README.md`
- `docs/database/schema.md`
- `docs/project-truth/architecture-truth.md`
- `docs/project-truth/runtime-flows.md`
- `docs/project-truth/changelog.md`
- `docs/tasks/todo.md`

---

## Proposed Implementation Steps

### Step 1: Freeze The Colab Plan And Make Backend Runtime The Active Direction

- archive the Colab-first plan
- stop treating Colab as the preferred target in active planning docs
- keep any Colab code only as transitional or optional fallback logic
- remove `INSIGHTFACE_COLAB_URL` from required config; demote it to optional with a deprecation warning on startup

### Step 2: Define The Structured Error Schema

Before touching any route logic, define `app/schemas/errors.py` with all model error codes listed in the Structured Error Response Contract section above.

This anchors the error contract early and prevents route handlers from growing bespoke error strings later.

### Step 3: Introduce A Backend Model Registry

Create a central registry that defines all supported recognition models.

Initial models:

- `local-default`
- `insightface-local`

Registry metadata should include:

- `id`
- `label`
- `description`
- `embedding_dimension`
- `input_mode`
- `storage_table`
- `match_rpc`
- `enabled`
- `status`
- `health`
- `unavailable_reason`
- `load_strategy`
- `weight_source`

`ModelDefinition` must be a typed Pydantic model, not a plain dict.

The registry must enforce two separate behaviors:

- raise a startup error if a registered runner does not satisfy the `BaseModelRunner` interface
- allow startup to continue if a valid runner reports `health: unavailable` because local dependencies or weights are missing

### Step 4: Implement The Runner Base Interface

Define `BaseModelRunner` as an abstract base class in `model_runners/base.py` with:

- `is_available() -> bool`
- `resolve_embedding(...) -> ResolvedEmbedding`
- `health() -> ModelHealth`

No runner should be registered in the registry unless it subclasses `BaseModelRunner`. This enforces the contract at import time rather than at inference time.

### Step 5: Convert `embedding_models.py` Into Registry-Driven Resolution

Replace hard-coded `if model_id == ...` branching with:

- model lookup via registry
- runner dispatch via base interface
- dimension validation before storage

This keeps route handlers stable even when new models are introduced. Route handlers should not need to know which runner handles a given model.

### Step 6: Add InsightFace Local Runner

Implement `InsightFaceLocalRunner` that:

- accepts `image_data_url`
- decodes image bytes
- loads InsightFace model locally using lazy-load-then-cache strategy
- extracts a 512-d embedding
- returns normalized `ResolvedEmbedding`
- returns `health()` state reflecting whether weights are loaded and last inference succeeded

This should replace the Colab HTTP call as the main backend path.

### Step 7: Keep Browser-Embedding Models As A Separate Runner Type

Preserve support for `local-default` through `MediaPipeEmbeddingRunner`.

This runner accepts a browser-provided embedding, validates its dimension, and passes it through to storage. It does not do inference. This is a deliberate `input_mode` distinction, not a degenerate case.

### Step 8: Make Storage Routing Registry-Driven

Refactor `app/supabase.py` so model storage and matching do not depend on scattered constants.

The storage layer should ask the registry which table to insert into, which RPC to call for search, and which dimension to validate against.

Add dimension validation before any insert (see Gap in section 3).

Add `delete_embeddings_for_model` to support identity cleanup flows.

### Step 9: Expose A Model Health Endpoint

Add `entrylens-api/app/routes/models.py` with at minimum:

- `GET /models` — returns full registry metadata including health state for all models
- `GET /models/{model_id}/health` — returns health detail for a single model

This gives the Labs UI and local operators a first-class diagnostic surface without polling the enroll or recognize routes to discover failures.

### Step 10: Refactor Labs Metadata To Delegate To The Registry

Update `entrylens-api/app/services/labs.py` so it no longer owns any independent model definitions.

It should:

- request model metadata from the backend model registry
- include that metadata in `/api/v1/labs` for Labs page bootstrap
- avoid any hard-coded model list except as a narrow fallback for catastrophic bootstrap failure

This prevents drift between Labs state and `/models` diagnostics.

### Step 11: Update Labs To Use Registry Metadata Only

The Labs page should consume model data from the backend only and render:

- enabled/disabled state
- `health` badge (`ok`, `degraded`, `unavailable`)
- `unavailable_reason` inline next to disabled models
- `input_mode` to drive whether the frontend sends image data or a browser embedding

The dropdown should adapt cleanly when a model is disabled, requires image input, is experimental, or is newly added.

### Step 12: Update Frontend API Error Handling

Refactor `entrylens-frontend/src/api/client.ts` so structured backend errors survive the client boundary.

Recommended direction:

- introduce a typed frontend error shape such as `ApiError`
- when the response body is JSON and includes `error` or `detail`, throw an `ApiError` instance instead of a plain `Error`
- keep `message` user-friendly, but preserve:
  - `error_code`
  - `model_id`
  - `detail`
  - `suggestion`

This is required for Labs to show meaningful per-model diagnostics and recovery actions.

### Step 13: Decide How Local Model Weights Are Managed

Before Step 6, choose one operational approach:

1. load InsightFace weights automatically on backend startup
2. lazy-load on first request, then cache in process
3. preload from a cache folder with explicit startup diagnostics

Recommended first choice: **lazy-load on first request, then cache in process**

Reason: lower startup friction, easier local iteration, simpler first milestone. The `health()` method on the runner surfaces whether the cache is warm.

### Step 14: Add Local Runtime Diagnostics

The `health()` method on each runner should expose:

- whether dependencies are installed
- whether weights loaded successfully
- whether the runner is ready
- timestamp of last successful inference
- error detail from the last failure if in `degraded` state

This information flows through the registry into `GET /models` and into Labs metadata. Operators should never need to grep logs to understand why a model is disabled.

### Step 15: Add Unit Coverage For Registry And Resolver

**[GAP addressed]** Before the new resolver is live in routes, add unit tests for:

- `get_model_definition` with a known and an unknown model ID
- `is_model_available` when runner reports available vs not
- `resolve_embedding` dispatch to the correct runner based on `model_id`
- dimension validation rejection before storage insert
- structured error code returned for each failure mode

These tests should run without a real InsightFace installation by mocking the runner.

### Step 16: Leave Room For Multi-Model Expansion

Once the registry and runner boundaries are in place, future models should only need:

- one model definition entry in the registry
- one runner implementation subclassing `BaseModelRunner`
- one storage target (table + RPC)
- optional docs and UI label changes

Route handlers should not need any changes. That is the main architecture success criterion.

---

## Suggested Data And Contract Direction

### Request Contracts

Keep the existing contract shape:

```json
{
  "model_id": "insightface-local",
  "embedding": null,
  "image_data_url": "data:image/jpeg;base64,..."
}
```

For browser-embedding models:

```json
{
  "model_id": "local-default",
  "embedding": [0.1, 0.2, ...],
  "image_data_url": "data:image/jpeg;base64,..."
}
```

**[GAP addressed]** The backend should validate `input_mode` against what was sent. If a client sends a browser embedding to an `image-data` model, or sends no image to an `image-data` model, the backend should return `input_mode_mismatch` before reaching the runner.

### Storage Direction

Keep separate tables or compatible families by dimension.

Immediate target:

- keep `embeddings` for `local-default`
- rename or repurpose `insightface_embeddings` for backend-local InsightFace
- avoid destructive migration until the backend-local path is verified

**[GAP addressed]** Add a migration guard: if `insightface-colab` embeddings exist in `insightface_embeddings` with dimension 512, they are compatible with `insightface-local` and can be matched against without any data migration. Document this explicitly so operators are not surprised.

---

## Risks

### Local Dependency Risk

Running InsightFace in the backend introduces Python and runtime dependency complexity:

- model weights
- onnxruntime compatibility
- CPU vs GPU behavior

Mitigation:

- expose diagnostics in model metadata and `GET /models/{model_id}/health`
- keep the model disabled when dependencies are missing
- document local setup clearly
- **return `model_unavailable` with a human-readable `suggestion` field instead of a 500**

### Startup And Latency Risk

Model loading may be slow or memory-heavy.

Mitigation:

- lazy-load and cache the runner
- make readiness explicit in Labs via `health` field
- log load time on first inference and surface it in diagnostics

### Architectural Regression Risk

If the registry is bypassed and model-specific logic leaks back into routes, the plug-and-play goal will fail.

Mitigation:

- keep routes thin
- keep model metadata, input mode, and storage routing centralized
- **unit tests for the resolver layer catch regressions before routes are touched**

### Mixed-Model Identity Risk

Identities may end up with samples across different model families.

That is acceptable, but recognition and candidate logic must always stay model-specific unless a future fusion strategy is deliberately added.

**[GAP addressed]** Add a warning log (not an error) when the same identity has samples under more than one model family, so this condition is visible before multi-model fusion is implemented.

### Silent Input Mode Mismatch Risk

**[GAP — new]** A client may send a browser embedding when the selected model expects image data, or vice versa. Without explicit validation this will produce incorrect embeddings silently.

Mitigation: validate `input_mode` against the received payload before dispatching to the runner, return `input_mode_mismatch` with a clear message.

### Embedding Dimension Corruption Risk

**[GAP — new]** A runner bug or model weight mismatch could produce an embedding with the wrong dimension. Storing it would corrupt the identity's sample set silently.

Mitigation: validate `len(embedding)` against `model_def.embedding_dimension` after every runner call and before any Supabase insert. Reject with `embedding_dimension_mismatch` and log the actual vs expected dimension.

---

## Verification Plan

### Backend Runtime Checks

1. API boots without Colab config set.
2. Startup warning is logged if `INSIGHTFACE_COLAB_URL` is still present in environment.
3. Labs reports `local-default` as enabled with `health: ok`.
4. Labs reports `insightface-local` as enabled only when local dependencies are available.
5. Labs reports `insightface-local` as `health: unavailable` with a readable `unavailable_reason` when weights are missing.
6. Selecting a disabled model returns `model_unavailable` error code, not a bare 500.
7. `GET /models` returns full metadata for all registered models.
8. `GET /models/insightface-local/health` returns runner health detail.

### Regression Checks

1. MediaPipe `local-default` enrollment still works.
2. MediaPipe `local-default` recognition still works.
3. Unknown-face creation still works.
4. Add-sample-to-existing still works.
5. Labs dropdown renders correctly with no changes to frontend model definitions.
6. Existing `insightface-colab` embeddings in `insightface_embeddings` are not touched by migration.

### InsightFace Local Checks

1. `insightface-local` enroll succeeds with image input and returns a 512-d embedding.
2. `insightface-local` recognize succeeds against `insightface_embeddings`.
3. Sample-append works with `insightface-local`.
4. No `vector(16)` path is used for InsightFace samples.
5. Runner `health()` returns `ok` after first successful inference.
6. Runner `health()` returns `unavailable` before weights are loaded.

### Input And Dimension Validation Checks

1. Sending a browser embedding to `insightface-local` returns `input_mode_mismatch`.
2. Sending no image to `insightface-local` returns `input_mode_mismatch`.
3. A runner returning the wrong embedding length is rejected before Supabase insert with `embedding_dimension_mismatch`.

### Structured Error Checks

1. Unknown `model_id` returns `model_not_found` with the submitted ID in the response body.
2. Disabled model returns `model_unavailable` with `detail` and `suggestion`.
3. Runner exception during inference returns `inference_failed` with `model_id` present.
4. No model-related failure returns a bare 500 with no `model_id` context.
5. Frontend API client preserves `error`, `model_id`, `detail`, and `suggestion` instead of flattening them into a generic string.

### Plug-And-Play Checks

1. Adding a new model requires:
   - one registry entry
   - one runner subclassing `BaseModelRunner`
   - one storage target
2. Route handlers do not need model-specific branching for the new model.
3. Labs dropdown updates from metadata without hard-coded UI rewrites.
4. Unit tests for the resolver pass without modifying test infrastructure.
5. `/api/v1/labs` and `GET /models` expose consistent model metadata for shared fields.

---

## Docs Update Checklist

- [ ] Update `README.md` with backend-local model setup notes and dependency installation instructions
- [ ] Update `docs/database/schema.md` for the long-term model-family storage direction and migration guard notes
- [ ] Update `docs/project-truth/architecture-truth.md`
- [ ] Update `docs/project-truth/runtime-flows.md`
- [ ] Update `docs/project-truth/changelog.md`
- [ ] Update `docs/tasks/todo.md`
- [ ] Document `GET /models` and `GET /models/{model_id}/health` in API reference
- [ ] Document structured error codes in a dedicated `docs/errors.md`
- [ ] Document weight management and local setup in `docs/local-model-setup.md`

---

## Completion Criteria

This transition plan is complete when:

- InsightFace no longer depends on Google Colab as the preferred runtime
- the backend owns model execution for all non-browser models
- every runner satisfies the `BaseModelRunner` interface contract
- Labs can render selectable models from backend metadata including health state
- routes remain stable while models become replaceable
- adding a new model no longer requires editing multiple route handlers or bespoke frontend logic
- all model-related failures return structured errors with `model_id` and `error_code`
- input mode and embedding dimension are validated before storage on every request
- the architecture can support one selected model now and multiple model families later
- unit tests cover the resolver, registry lookup, and all structured error paths

<!-- graphify-links:start -->
## Graph Links

- [[graphify-out/wiki/index|Graphify Wiki]]
- [[graphify-out/GRAPH_REPORT|Graph Report]]
- Related file notes:
  - [[graphify-out/wiki/entrylens-api/app/config.py|entrylens-api/app/config.py]]
  - [[graphify-out/wiki/entrylens-api/app/routes/enroll.py|entrylens-api/app/routes/enroll.py]]
  - [[graphify-out/wiki/entrylens-api/app/routes/identities.py|entrylens-api/app/routes/identities.py]]
  - [[graphify-out/wiki/entrylens-api/app/routes/models.py|entrylens-api/app/routes/models.py]]
  - [[graphify-out/wiki/entrylens-api/app/routes/recognize.py|entrylens-api/app/routes/recognize.py]]
  - [[graphify-out/wiki/entrylens-api/app/schemas/enroll.py|entrylens-api/app/schemas/enroll.py]]
  - [[graphify-out/wiki/entrylens-api/app/schemas/errors.py|entrylens-api/app/schemas/errors.py]]
  - [[graphify-out/wiki/entrylens-api/app/schemas/identity.py|entrylens-api/app/schemas/identity.py]]
  - [[graphify-out/wiki/entrylens-api/app/schemas/recognize.py|entrylens-api/app/schemas/recognize.py]]
  - [[graphify-out/wiki/entrylens-api/app/services/embedding_models.py|entrylens-api/app/services/embedding_models.py]]
  - [[graphify-out/wiki/entrylens-api/app/services/insightface_colab.py|entrylens-api/app/services/insightface_colab.py]]
  - [[graphify-out/wiki/entrylens-api/app/services/labs.py|entrylens-api/app/services/labs.py]]
- Related communities:
  - [[graphify-out/wiki/communities/Community 0|Community 0]]
  - [[graphify-out/wiki/communities/Community 1|Community 1]]
  - [[graphify-out/wiki/communities/Community 2|Community 2]]
  - [[graphify-out/wiki/communities/Community 3|Community 3]]
  - [[graphify-out/wiki/communities/Community 5|Community 5]]
  - [[graphify-out/wiki/communities/Community 7|Community 7]]
<!-- graphify-links:end -->
