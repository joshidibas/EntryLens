# Data Model

This file reflects the practical current data model direction in the repository after the identity CRUD schema migration.

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
- `display_name`
  primary editable display name used by CRUD flows
- `identity_type`
  primary editable identity type such as `visitor`, `staff`, `student`, or `contractor`
- `status`
  current lifecycle status, default `active`
- `notes`
  admin/operator notes
- `review_source`
  creation source for review-driven identities such as `live-detection`
- `merged_into_identity_id`
  optional pointer used during placeholder merge workflows
- `profile_sample_id`
  the sample selected as the main ref/profile picture
- `provider_subject_id`
  provider-owned identity reference
- `created_at`
- `updated_at`

Legacy compatibility columns still present in the database:

- `name`
- `role`

New code should prefer `display_name` and `identity_type`.

### `embeddings`

- `id`
- `identity_id`
  required reference to `identities`
- `embedding`
  current placeholder `VECTOR(16)` from MediaPipe transform output
- `sample_kind`
  currently `face`
- `image_path`
  currently a local runtime path under `runtime-data/identity-samples/`; later can move to object storage
- `capture_source`
  where the sample came from
- `capture_confidence`
  confidence at capture/review time
- `is_reference`
  one preferred matching/reference sample per identity
- `is_profile_source`
  one sample that acts as the visual profile source per identity
- `metadata`
  legacy compatibility JSON
- `created_at`
- `updated_at`

The physical table name is still `embeddings`, but the domain meaning is now closer to `identity_samples`.

Current runtime behavior:

- enroll and add-sample flows can capture a browser frame and save it locally
- the saved relative path is persisted in `image_path`
- one sample can be selected as both the visual profile source and the preferred reference sample

### `detection_logs`

- `id`
- `source`
  currently `live-feed`
- `camera_id`
  frontend camera/feed identifier
- `image_path`
  local runtime path under `runtime-data/detection-logs/`
- `embedding`
  stored `VECTOR(16)` snapshot embedding from the live frame
- `embedding_signature`
  rounded subset used to suppress rapid duplicate unknown logs
- `auto_similarity`
  similarity returned by automatic recognition
- `auto_identity_id`
  identity suggested by recognition, if any
- `auto_display_name`
  display name captured at recognition time
- `auto_tagged`
  true only when similarity is `>= 0.95`
- `current_identity_id`
  current linked identity for review; low-confidence detections point to a placeholder unknown identity
- `review_status`
  current UI review state such as `pending`, `auto-tagged`, `resolved`, or `ignored`
- `review_notes`
- `reviewed_at`
- `promoted_embedding_id`
  sample row created from this detection frame, if promoted
- `promoted_at`
- `detected_at`
- `created_at`
- `updated_at`

Current runtime behavior:

- only the `/live` page writes `detection_logs`
- if similarity is below `0.95` or no match is returned, the backend creates a placeholder unknown identity and links the log to it
- the detection-log detail page can rename that placeholder into a real identity, merge it into an existing identity, or promote the stored frame into the sample store
- duplicate suppression happens per recognized identity or per unknown embedding signature within a short backend window

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

## Ambiguous Or Inconsistent Naming

- `provider_subject_id` is the current preferred name.
- Older provider-specific naming like `compreface_subject_id` is explicitly deprecated in the architecture doc.
- The design mixes "identity", "subject", and "PersonId" depending on layer:
  use `identity` for local DB records and `provider_subject_id` for external provider references.
- The database still uses `embeddings` as the physical table name, but the product/domain meaning is now closer to `identity_samples`.
- `detection_logs` is the review/event surface; attendance is still separate.

## Working Rules Before Changing Queries, Writes, Or Contracts

- Confirm the schema exists in code before editing migrations or models.
- Keep provider-agnostic naming unless there is a real implementation reason not to.
- Do not hardcode confidence thresholds or debounce values.
- Keep detection-log writes scoped to Live feed unless the product rules explicitly change.
- If the code later diverges from this planned schema, update this file to reflect runtime truth.
- Treat provider response shapes as contracts that should live behind the `FaceProvider` abstraction, not inside route handlers.
