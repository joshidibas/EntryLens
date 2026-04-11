import { useEffect, useMemo, useRef, useState } from "react";
import { createDetectionLog, type DetectionLogDetail } from "../api/detectionLogs";
import CameraPanel from "../components/CameraPanel";
import LiveFeed from "../components/LiveFeed";
import { useRecognitionSession } from "../hooks/useRecognitionSession";
import { getEmbeddingKey } from "../lib/recognition";

export default function LivePage() {
  const { liveDetection, identifyResult, isIdentifying, handleDetectionChange, runRecognition } = useRecognitionSession();
  const [logError, setLogError] = useState("");
  const [recentLog, setRecentLog] = useState<DetectionLogDetail | null>(null);
  const lastLoggedEmbeddingKeyRef = useRef("");

  const currentEmbeddingKey = useMemo(
    () => getEmbeddingKey(liveDetection?.embedding),
    [liveDetection?.embedding],
  );

  useEffect(() => {
    if (!liveDetection?.hasFace || !currentEmbeddingKey) {
      lastLoggedEmbeddingKeyRef.current = "";
      setRecentLog(null);
    }
  }, [currentEmbeddingKey, liveDetection?.hasFace]);

  useEffect(() => {
    if (!liveDetection?.hasFace || !liveDetection.embedding || isIdentifying || !identifyResult) {
      return;
    }

    if (lastLoggedEmbeddingKeyRef.current === currentEmbeddingKey) {
      return;
    }

    let cancelled = false;

    async function storeDetectionLog() {
      try {
        const response = await createDetectionLog({
          embedding: liveDetection.embedding ?? [],
          image_data_url: liveDetection.imageDataUrl ?? null,
          camera_id: "live-main",
          auto_similarity: identifyResult.similarity,
          auto_identity_id: identifyResult.identityId,
          auto_display_name: identifyResult.name,
        });
        if (cancelled) {
          return;
        }
        lastLoggedEmbeddingKeyRef.current = currentEmbeddingKey;
        setRecentLog(response.detection_log);
        setLogError("");
      } catch (error) {
        if (cancelled) {
          return;
        }
        setLogError(error instanceof Error ? error.message : "Could not save this live detection log.");
      }
    }

    void storeDetectionLog();
    return () => {
      cancelled = true;
    };
  }, [currentEmbeddingKey, identifyResult, isIdentifying, liveDetection]);

  return (
    <section className="page-grid">
      <CameraPanel
        onDetectionChange={handleDetectionChange}
        onRecognize={runRecognition}
        recognizedName={identifyResult?.matched ? identifyResult.name ?? undefined : undefined}
        isRecognizing={isIdentifying}
      />
      <LiveFeed
        detection={liveDetection}
        identifyResult={
          identifyResult?.matched && identifyResult.name
            ? { name: identifyResult.name, similarity: identifyResult.similarity }
            : null
        }
        isIdentifying={isIdentifying}
        recentLog={recentLog}
        logError={logError}
      />
    </section>
  );
}
