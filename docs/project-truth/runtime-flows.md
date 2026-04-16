# Runtime Flows

These flows summarize the current runtime behavior visible in the repository, plus a short note where roadmap behavior is still only planned.

## Login And Auth Flow

- Current auth:
  API key protection on `/api/v1/*`
- Public health endpoint:
  `/health`
- Planned later auth shift:
  JWT-based login and session handling

Verification shortcut files:

- `entrylens-api/app/main.py`
- `entrylens-api/app/auth.py`
- `entrylens-api/app/config.py`

## Authorization Or Gating Flow

- Browser captures frames from the camera.
- MediaPipe checks head pose and face stability.
- Frontend posts valid face chips or captured frames to the API for recognize or enroll flows.
- Backend auth validates request access before recognition or enrollment work.
- Recognition thresholds decide automatic tagging versus review-oriented follow-up.

Verification shortcut files:

- `entrylens-frontend/src/hooks/useMediaPipeLab.ts`
- `entrylens-frontend/src/hooks/useRecognitionSession.ts`
- `entrylens-api/app/routes/recognize.py`
- `entrylens-api/app/providers/local_provider.py`

## Session Handling

- No user login session handling exists in this repo today.
- Current access control uses API keys, so browser session management is minimal.
- Planned Phase 2 introduces JWT expiry and authenticated user sessions.

Verification shortcut files:

- `entrylens-api/app/auth.py`
- `entrylens-api/app/routes/system.py`

## Privileged Backend Action Flow

Recognition flow, current:

1. Browser sends base64 face chip to `POST /api/v1/recognize`.
2. FastAPI verifies API key.
3. The configured provider resolves an embedding and attempts identity matching.
4. Threshold logic decides whether the result is auto-tagged or should remain a review case.
5. Live-feed flows can also persist a detection log image locally under `runtime-data/detection-logs/`.

Enrollment flow, current:

1. Operator uploads photos to `POST /api/v1/enroll`.
2. Backend validates and decodes images.
3. Provider strategy resolves embeddings and stores them through the Supabase client.
4. Optional sample images are saved locally under `runtime-data/identity-samples/`.
5. Identity metadata and sample rows are stored in Supabase/PostgreSQL.

Detection-log review flow, current:

1. Live-feed recognition creates or updates `detection_logs`.
2. Low-confidence or unmatched detections can point to placeholder unknown identities.
3. Operator opens `/detection-logs` or a specific detection-log detail view.
4. The backend can rename a placeholder identity, merge it into an existing identity, or promote the captured frame into the sample store.

Verification shortcut files:

- `entrylens-api/app/providers/base.py`
- `entrylens-api/app/providers/local_provider.py`
- `entrylens-api/app/routes/enroll.py`
- `entrylens-api/app/routes/recognize.py`
- `entrylens-api/app/routes/detection_logs.py`
- `entrylens-api/app/routes/identities.py`
- `entrylens-api/app/sample_images.py`

## Audit And Logging Flow

Current audit and logging surfaces:

- `detection_logs` for live-feed reviewable events
- local runtime image storage for saved detection frames and identity samples
- `attendance_logs` remains part of the broader product model
- `review_queue` and export surfaces remain planned

Verification shortcut files:

- `entrylens-api/app/routes/attendance.py`
- `entrylens-api/app/routes/detection_logs.py`
- `entrylens-api/app/sample_images.py`
- `entrylens-api/setup_supabase.sql`




<!-- graphify-links:start -->
## Graph Links

- [[graphify-out/wiki/index|Graphify Wiki]]
- [[graphify-out/GRAPH_REPORT|Graph Report]]
- Related file notes:
  - [[graphify-out/wiki/entrylens-api/app/auth.py|entrylens-api/app/auth.py]]
  - [[graphify-out/wiki/entrylens-api/app/config.py|entrylens-api/app/config.py]]
  - [[graphify-out/wiki/entrylens-api/app/main.py|entrylens-api/app/main.py]]
  - [[graphify-out/wiki/entrylens-api/app/providers/base.py|entrylens-api/app/providers/base.py]]
  - [[graphify-out/wiki/entrylens-api/app/providers/local_provider.py|entrylens-api/app/providers/local_provider.py]]
  - [[graphify-out/wiki/entrylens-api/app/routes/attendance.py|entrylens-api/app/routes/attendance.py]]
  - [[graphify-out/wiki/entrylens-api/app/routes/detection_logs.py|entrylens-api/app/routes/detection_logs.py]]
  - [[graphify-out/wiki/entrylens-api/app/routes/enroll.py|entrylens-api/app/routes/enroll.py]]
  - [[graphify-out/wiki/entrylens-api/app/routes/identities.py|entrylens-api/app/routes/identities.py]]
  - [[graphify-out/wiki/entrylens-api/app/routes/recognize.py|entrylens-api/app/routes/recognize.py]]
  - [[graphify-out/wiki/entrylens-api/app/routes/system.py|entrylens-api/app/routes/system.py]]
  - [[graphify-out/wiki/entrylens-api/app/sample_images.py|entrylens-api/app/sample_images.py]]
- Related communities:
  - [[graphify-out/wiki/communities/Community 0|Community 0]]
  - [[graphify-out/wiki/communities/Community 2|Community 2]]
  - [[graphify-out/wiki/communities/Community 3|Community 3]]
  - [[graphify-out/wiki/communities/Community 4|Community 4]]
  - [[graphify-out/wiki/communities/Community 8|Community 8]]
  - [[graphify-out/wiki/communities/Community 9|Community 9]]
<!-- graphify-links:end -->
