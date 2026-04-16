# MediaPipe Vision Lab Plan

## Task Summary

Make MediaPipe the first real non-Azure implementation inside the shared Vision Lab so the unified lab can run an actual local detect flow, not just planned placeholders.

The user-facing goal is:

1. choose `Detect Face`
2. choose `MediaPipe`
3. choose a MediaPipe model profile
4. upload or select an input image
5. run detection locally in the browser
6. inspect structured results in the same shared lab used by Azure options

## Current Repo Truth

- the shared lab UI already exists at `entrylens-frontend/src/pages/AzureLabPage.jsx`
- the lab now supports a unified `Task -> Engine / Provider -> Model Profile` selector shape
- `MediaPipe` currently appears only as a planned target
- Azure-backed flows are the only real runnable lab targets today
- no MediaPipe frontend dependency is installed yet
- no MediaPipe lab-specific storage folder exists under `playgrounds/`

## Assumptions

- the first useful MediaPipe slice is detect-only, not recognition
- browser-side MediaPipe is the right place for the first real local implementation
- implementation logic can stay separate while the shared lab UI remains unified
- storing uploaded test images under a dedicated playground folder is still useful even when execution happens in the browser

## File Paths Expected To Change

- `docs/old/Planning/2026-04-11-mediapipe-vision-lab.md`
- `docs/tasks/todo.md`
- `docs/project-truth/repo-map.md`
- `docs/project-truth/architecture-truth.md`
- `docs/project-truth/changelog.md`
- `entrylens-frontend/package.json`
- `entrylens-frontend/src/pages/AzureLabPage.jsx`
- `entrylens-frontend/src/styles.css`
- `entrylens-frontend/src/api/azureLab.js`
- `entrylens-frontend/src/hooks/useMediaPipeLab.js`
- `entrylens-api/app/routes/azure_lab.py`
- `entrylens-api/app/services/azure_lab.py`
- `playgrounds/mediapipe-playground/README.md`
- `playgrounds/mediapipe-playground/test-data/input/.gitkeep`
- `playgrounds/mediapipe-playground/output/.gitkeep`

## Implementation Steps

### Phase A: MediaPipe Target Becomes Real

1. Add a dedicated `playgrounds/mediapipe-playground/` folder for input and output separation.
2. Mark the backend target as ready for probe uploads.
3. Add a backend file-serving route so the frontend can fetch uploaded input images safely.

### Phase B: Frontend MediaPipe Runtime

1. Add the MediaPipe Tasks Vision frontend dependency.
2. Create a small hook that loads the Face Landmarker once and runs detection on an image element.
3. Return structured output suitable for the shared lab:
   - face count
   - presence indicator
   - basic landmark result summary
   - image dimensions

### Phase C: Shared Lab Integration

1. Keep the shared selectors unchanged conceptually.
2. When `Task = Detect Face` and `Engine = MediaPipe`, run browser-side detection instead of backend command execution.
3. Show MediaPipe results in the same result panel used by other engines.
4. Keep Azure detect under the same detect flow for comparison.

### Phase D: Verification

1. Verify the frontend still builds.
2. Verify backend syntax after route and service updates.
3. Verify MediaPipe can process at least one uploaded image from the shared lab.

## Verification Steps

1. Open the Vision Lab.
2. Set:
   - `Task = Detect Face`
   - `Engine / Provider = MediaPipe`
3. Upload a clear single-face image.
4. Run detection.
5. Confirm the result panel shows a non-empty MediaPipe result payload.
6. Confirm switching back to `Azure Detect` still preserves the shared lab structure.

## Docs Update Checklist

- update `docs/tasks/todo.md`
- update `docs/project-truth/repo-map.md`
- update `docs/project-truth/architecture-truth.md`
- append to `docs/project-truth/changelog.md`




<!-- graphify-links:start -->
## Graph Links

- [[graphify-out/wiki/index|Graphify Wiki]]
- [[graphify-out/GRAPH_REPORT|Graph Report]]
<!-- graphify-links:end -->
