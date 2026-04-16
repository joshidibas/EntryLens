import { useRef, useState } from "react";
import { recognize, recognizeCandidates, type CandidateMatch, type RecognizeRequest } from "../api/recognize";
import { hasMeaningfulEmbeddingChange } from "../lib/recognition";
import type { DetectionSnapshot } from "../types";

const RECOGNITION_RESET_THRESHOLD = 0.6;

export interface RecognitionResultState {
  matched: boolean;
  identityId: string | null;
  name: string | null;
  similarity: number;
}

interface UseRecognitionSessionOptions {
  includeCandidates?: boolean;
  identifyIndicatorMs?: number;
  clearResultMs?: number;
  onError?: (message: string) => void;
}

export function useRecognitionSession(options: UseRecognitionSessionOptions = {}) {
  const {
    includeCandidates = false,
    identifyIndicatorMs = 1200,
    clearResultMs = 1200,
    onError,
  } = options;

  const [liveDetection, setLiveDetection] = useState<DetectionSnapshot | null>(null);
  const [identifyResult, setIdentifyResult] = useState<RecognitionResultState | null>(null);
  const [candidateMatches, setCandidateMatches] = useState<CandidateMatch[]>([]);
  const [isIdentifying, setIsIdentifying] = useState(false);
  const identifyRunIdRef = useRef(0);
  const clearIdentifyResultTimerRef = useRef<number | null>(null);

  function handleDetectionChange(snapshot: DetectionSnapshot | null) {
    const previousDetection = liveDetection;
    setLiveDetection(snapshot);

    if (clearIdentifyResultTimerRef.current) {
      window.clearTimeout(clearIdentifyResultTimerRef.current);
      clearIdentifyResultTimerRef.current = null;
    }

    if (!snapshot?.hasFace) {
      clearIdentifyResultTimerRef.current = window.setTimeout(() => {
        setIdentifyResult(null);
        setCandidateMatches([]);
      }, clearResultMs);
      return;
    }

    if (
      previousDetection?.hasFace &&
      identifyResult &&
      hasMeaningfulEmbeddingChange(
        previousDetection.embedding,
        snapshot.embedding,
        RECOGNITION_RESET_THRESHOLD,
      )
    ) {
      setIdentifyResult(null);
      setCandidateMatches([]);
    }
  }

  async function runRecognition(request: RecognizeRequest): Promise<boolean> {
    const startedAt = Date.now();
    const runId = identifyRunIdRef.current + 1;
    identifyRunIdRef.current = runId;
    setIsIdentifying(true);

    try {
      const [recognizeResult, candidates] = await Promise.all([
        recognize(request),
        includeCandidates ? recognizeCandidates(request) : Promise.resolve([]),
      ]);

      setCandidateMatches(candidates);
      setIdentifyResult({
        matched: recognizeResult.matched,
        identityId: recognizeResult.identity_id,
        name: recognizeResult.name,
        similarity: recognizeResult.similarity,
      });
      return recognizeResult.matched;
    } catch (error) {
      setIdentifyResult(null);
      setCandidateMatches([]);
      if (onError) {
        onError(error instanceof Error ? error.message : "Recognition failed.");
      }
      return false;
    } finally {
      const elapsed = Date.now() - startedAt;
      const remaining = Math.max(0, identifyIndicatorMs - elapsed);
      window.setTimeout(() => {
        if (identifyRunIdRef.current === runId) {
          setIsIdentifying(false);
        }
      }, remaining);
    }
  }

  return {
    liveDetection,
    identifyResult,
    candidateMatches,
    isIdentifying,
    handleDetectionChange,
    runRecognition,
    setIdentifyResult,
    setCandidateMatches,
  };
}
