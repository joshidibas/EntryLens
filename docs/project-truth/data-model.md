# Data Model

This file reflects the practical planned data structures described in the architecture document. These structures are not implemented in this repository yet.

## Core Auth And Admin Data Structures

- API key configuration for Phase 1 auth
- Environment-based provider selection:
  `SENTINEL_RECOGNITION_PROVIDER=local`
- Threshold settings:
  `SENTINEL_HIGH_CONFIDENCE_THRESHOLD`
  `SENTINEL_LOW_CONFIDENCE_THRESHOLD`
  `SENTINEL_DEBOUNCE_WINDOW_SECONDS`

## Main Product Data Structures

### `identities`

- `id`
  UUID primary key
- `name`
  display name
- `role`
  planned values: `staff` or `visitor`
- `provider_subject_id`
  provider-owned identity reference
- `enrolled_at`
- `metadata`
  JSONB extra fields

### `attendance_logs`

- `id`
- `identity_id`
  nullable reference to `identities`
- `status`
  planned values: `confirmed`, `visitor`, `pending_review`
- `similarity`
- `image_key`
  MinIO object key
- `detected_at`
- `camera_id`

### `review_queue`

- `id`
- `attendance_log_id`
- `candidate_identity_id`
- `similarity`
- `image_key`
- `status`
  planned values: `pending`, `confirmed`, `rejected`
- `reviewed_at`
- `created_at`

### `embeddings_mirror`

- `identity_id`
- `embedding`
  planned `VECTOR(128)`
- `created_at`

## Ambiguous Or Inconsistent Naming

- `provider_subject_id` is the current preferred name.
- Older provider-specific naming like `compreface_subject_id` is explicitly deprecated in the architecture doc.
- The design mixes "identity", "subject", and "PersonId" depending on layer:
  use `identity` for local DB records and `provider_subject_id` for external provider references.

## Working Rules Before Changing Queries, Writes, Or Contracts

- Confirm the schema exists in code before editing migrations or models.
- Keep provider-agnostic naming unless there is a real implementation reason not to.
- Do not hardcode confidence thresholds or debounce values.
- If the code later diverges from this planned schema, update this file to reflect runtime truth.
- Treat provider response shapes as contracts that should live behind the `FaceProvider` abstraction, not inside route handlers.
