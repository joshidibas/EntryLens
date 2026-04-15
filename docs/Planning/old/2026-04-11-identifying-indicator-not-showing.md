# Plan: Fix "Identifying" Indicator Not Showing

## Problem
When a face is being identified, the "Identifying..." indicator does not appear in the UI, even though the identification works correctly. The `isIdentifying` state is being set correctly, but the UI does not reflect this.

## Current Behavior
- Face detected → recognition triggers ✓
- API returns result with name ✓
- `isIdentifying` is set to `true` and then `false` ✓
- UI does not show "Identifying..." indicator ✗

## Suspected Root Causes
1. React state update timing - the component may re-render before the state change propagates
2. The "Identifying..." text is positioned in a location that's not visible
3. State is being reset too quickly (though logs show it's set properly)

## Investigation Steps
1. Add debug logging to verify isIdentifying state changes are happening
2. Check if the "Identifying..." text is rendering with correct conditional
3. Verify the parent component is passing the prop correctly
4. Check if there are any styling issues hiding the text

## Files to Check
- `entrylens-frontend/src/pages/LabsPage.tsx` - Where isIdentifying is set and UI is rendered
- `entrylens-frontend/src/components/CameraPanel.tsx` - Receives isRecognizing prop

## Solution Approaches
1. Ensure the indicator is in a prominent location (next to face count)
2. Add visual loading indicator in CameraPanel
3. Use a longer visible delay before resetting isIdentifying
4. Add fallback display when isIdentifying is true

## Priority
High - Without visual feedback, users don't know identification is happening



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
