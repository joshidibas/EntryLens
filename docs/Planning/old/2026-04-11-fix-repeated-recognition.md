# Plan: Fix Repeated Recognition Issue

## Status: COMPLETED

## Problem
When a face is recognized in the camera feed, the `onRecognize` callback was being called repeatedly even when the same person stays in frame. This caused unnecessary API calls and redundant recognition attempts.

## Root Cause
The current implementation in `CameraPanel.tsx` triggered `onRecognize` every time a face was detected with an embedding, without checking if that face was already recognized recently.

## Solution Implemented
Implemented a debounce/throttle mechanism that:
1. Tracks the last recognized embedding
2. Blocks re-recognition for the same face within a 3-second cooldown period
3. Resets when the person leaves the frame

## Changes Made
- `entrylens-frontend/src/components/CameraPanel.tsx` - Added throttling logic with refs
- `entrylens-frontend/src/pages/LabsPage.tsx` - Simplified by removing duplicate throttling

## Result
- Same face stays in frame → recognition only triggers once (after 2s delay)
- Face leaves and returns → triggers again
- Different person appears → triggers immediately



<!-- graphify-links:start -->
## Graph Links

- [[graphify-out/wiki/index|Graphify Wiki]]
- [[graphify-out/GRAPH_REPORT|Graph Report]]
- Related file notes:
  - [[graphify-out/wiki/entrylens-frontend/src/components/CameraPanel.tsx|entrylens-frontend/src/components/CameraPanel.tsx]]
  - [[graphify-out/wiki/entrylens-frontend/src/pages/LabsPage.tsx|entrylens-frontend/src/pages/LabsPage.tsx]]
- Related communities:
  - [[graphify-out/wiki/communities/Community 8|Community 8]]
  - [[graphify-out/wiki/communities/Community 11|Community 11]]
<!-- graphify-links:end -->
