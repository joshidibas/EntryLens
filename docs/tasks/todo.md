# Todo

## Current Task

✅ COMPLETED (2026-04-11): Local recognition enrollment via Labs

User can enroll their face from live camera in Labs page and test recognition.

## Implementation Checklist

- [x] Remove Azure from the active runtime configuration and app wiring.
- [x] Remove Azure playground folders from the repo workspace.
- [x] Keep MediaPipe live detection active in `/live` and `/labs`.
- [x] Add Supabase env placeholders and config loading to the backend.
- [x] Add a Supabase client module in the backend (app/supabase.py).
- [x] Add a local recognition provider scaffold that targets Supabase-backed identities.
- [x] Add planned `recognize` and `enroll` route shapes for the local-recognition path.
- [x] Create Supabase tables (identities, embeddings) and match_embeddings function

## Database Documentation

- `docs/database/schema.md` - Full database schema reference
- `docs/database/changelog.md` - Database change history

## Verification Notes

- File verification (2026-04-11):
  - `entrylens-api/app/supabase.py` - EXISTS - SupabaseClient class
  - `entrylens-api/app/routes/enroll.py` - EXISTS - POST /api/v1/enroll endpoint
  - `entrylens-api/app/routes/recognize.py` - EXISTS - POST /api/v1/recognize endpoint
  - `entrylens-frontend/src/api/enroll.ts` - EXISTS - Frontend API call
  - `entrylens-frontend/src/api/recognize.ts` - EXISTS - Frontend API call
  - `entrylens-frontend/src/hooks/useMediaPipeLab.ts` - EXISTS - MediaPipe with embedding output
  - Supabase tables created: public.identities, public.embeddings
  - Supabase function created: public.match_embeddings

## Review Or Outcome Notes

- MediaPipe is now the primary active engine for detection.
- Local recognition via Labs is working: enroll + identify flow.
- Face embeddings stored as vector(16) from MediaPipe facial transformation matrix.
- Database schema documented in `docs/database/`

