# Runtime Flows

These flows are planned flows extracted from the architecture document. They are not implemented in the current repository snapshot.

## Login And Auth Flow

- Current planned Phase 1 auth:
  API key protection on `/api/v1/*`
- Health endpoint planned to be public:
  `/health`
- Planned Phase 2 auth shift:
  JWT-based login and session handling

Verification shortcut files once code exists:

- `sentinel-api/app/main.py`
- `sentinel-api/app/auth.py`
- `sentinel-api/app/config.py`

## Authorization Or Gating Flow

- Browser captures frames from the camera.
- MediaPipe checks head pose and face stability.
- Only valid stable face chips are posted to the API.
- Backend auth validates request access before recognition or enrollment work.
- Recognition thresholds decide confirmed match, pending review, or visitor outcome.

Verification shortcut files once code exists:

- `entrylens-frontend/src/hooks/useMediaPipeLab.ts`
- `sentinel-frontend/src/hooks/useRecognitionLoop.js`
- `sentinel-api/app/routes/recognize.py`
- `sentinel-api/app/services/recognition_service.py`

## Session Handling

- No implemented session handling exists in this repo.
- Planned Phase 1 uses API keys, so browser session management is minimal.
- Planned Phase 2 introduces JWT expiry and authenticated user sessions.

Verification shortcut files once code exists:

- `sentinel-api/app/auth.py`
- `sentinel-api/app/routes/auth.py`

## Privileged Backend Action Flow

Recognition flow, planned:

1. Browser sends base64 face chip to `POST /api/v1/recognize`.
2. FastAPI verifies API key.
3. Provider strategy calls `provider.identify()`.
4. Threshold logic writes to attendance and maybe review queue.
5. Image storage writes chip to MinIO.
6. WebSocket pushes event to dashboard clients.

Enrollment flow, planned:

1. Operator uploads photos to `POST /api/v1/enroll`.
2. Backend validates and decodes images.
3. Provider strategy calls `provider.enroll()`.
4. Identity metadata is stored in PostgreSQL.

Review flow, planned:

1. Operator opens pending review queue.
2. Confirm calls review endpoint.
3. Backend re-enrolls additional sample through the provider.
4. Review item and attendance log are updated.

Verification shortcut files once code exists:

- `sentinel-api/app/providers/base.py`
- `entrylens-api/app/providers/local_provider.py`
- `sentinel-api/app/routes/enroll.py`
- `sentinel-api/app/routes/review.py`
- `sentinel-api/app/services/review_service.py`
- `sentinel-api/app/services/storage_service.py`

## Audit And Logging Flow

Planned audit surfaces:

- `attendance_logs` for recognition outcomes
- `review_queue` for uncertain matches
- MinIO face chip storage with TTL for image audit support
- CSV export for external review

No implemented logging or audit code exists in the repo today.

Verification shortcut files once code exists:

- `sentinel-api/app/routes/attendance.py`
- `sentinel-api/app/routes/export.py`
- `sentinel-api/app/models.py`
- `sentinel-api/alembic/versions/001_initial_schema.py`



<!-- graphify-links:start -->
## Graph Links

- [[graphify-out/wiki/index|Graphify Wiki]]
- [[graphify-out/GRAPH_REPORT|Graph Report]]
- Related file notes:
  - [[graphify-out/wiki/entrylens-api/app/providers/local_provider.py|entrylens-api/app/providers/local_provider.py]]
  - [[graphify-out/wiki/entrylens-frontend/src/hooks/useMediaPipeLab.ts|entrylens-frontend/src/hooks/useMediaPipeLab.ts]]
- Related communities:
  - [[graphify-out/wiki/communities/Community 3|Community 3]]
  - [[graphify-out/wiki/communities/Community 9|Community 9]]
<!-- graphify-links:end -->
