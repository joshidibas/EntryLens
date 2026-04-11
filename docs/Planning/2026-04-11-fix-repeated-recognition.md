# Plan: Fix Repeated Recognition Issue

## Problem
When a face is recognized in the camera feed, the `onRecognize` callback is being called repeatedly even when the same person stays in frame. This causes unnecessary API calls and redundant recognition attempts.

## Root Cause
The current implementation in `CameraPanel.tsx` triggers `onRecognize` every time a face is detected with an embedding, without checking if that face was already recognized recently.

## Solution
Implement a debounce/throttle mechanism that:
1. Tracks the last recognized person
2. Blocks re-recognition for the same person within a cooldown period
3. Resets when the person leaves the frame or a new person appears

## Implementation Steps

### 1. Add recognition state tracking
- Add refs to track: last recognized name, last recognition time, face presence state
- Track if face was present in previous frame vs current frame

### 2. Add cooldown mechanism
- After successful recognition, store the recognized name and timestamp
- Before calling `onRecognize`, check:
  - Is same person as last recognized?
  - Is within cooldown period (e.g., 3 seconds)?
  - Is face still present (wasn't gone and came back)?

### 3. Face departure detection
- Track `hasFace` state changes
- Reset recognition state when face leaves frame
- Allow re-recognition when same person returns after leaving

## Files to Modify
- `entrylens-frontend/src/components/CameraPanel.tsx`

## Expected Behavior
1. First detection triggers recognition normally
2. Same person stays in frame → no re-trigger until cooldown expires
3. Face leaves and returns → triggers recognition again
4. Different person appears → triggers immediately