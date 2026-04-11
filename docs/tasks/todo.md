# Todo

## Current Task

DONE (2026-04-11): Detection logs and unknown-identity review flow

Live feed now creates `detection_logs`, auto-tags at high confidence, creates placeholder unknown identities when needed, and supports later merge/review from detection-log detail pages.

## Implementation Checklist

- [x] Remove Azure from the active runtime configuration and app wiring.
- [x] Remove Azure playground folders from the repo workspace.
- [x] Keep MediaPipe live detection active in `/live` and `/labs`.
- [x] Add Supabase env placeholders and config loading to the backend.
- [x] Add a Supabase client module in the backend (`app/supabase.py`).
- [x] Add a local recognition provider scaffold that targets Supabase-backed identities.
- [x] Add planned `recognize` and `enroll` route shapes for the local-recognition path.
- [x] Create Supabase tables (`identities`, `embeddings`) and `match_embeddings` function.
- [x] Apply `detection_logs` schema and unknown-identity review columns in the database.
- [x] Add backend `detection_logs` schemas, helpers, and routes.
- [x] Write detection logs from Live feed only.
- [x] Prevent rapid duplicate detection logs for the same recognized person or unknown signature.
- [x] Add detection-log list/detail pages.
- [x] Add detail-page rename / merge / promote-sample actions.

## Database Documentation

- `docs/database/schema.md` - Full database schema reference
- `docs/database/changelog.md` - Database change history

## Review Or Outcome Notes

- MediaPipe is still the primary active engine for detection and placeholder matching.
- Local recognition via Labs and Live works, and only `/live` now writes `detection_logs`.
- `detection_logs` is separate from attendance and supports placeholder unknown review plus later identity merge/promotion.
