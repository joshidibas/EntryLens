import { useEffect, useRef, useState } from "react";
import { useMediaPipeLab } from "../hooks/useMediaPipeLab";
import { getEmbeddingKey, hasMeaningfulEmbeddingChange } from "../lib/recognition";
import type { DetectionSnapshot } from "../types";

const MIN_RECOGNITION_INDICATOR_MS = 1200;
const UNMATCHED_RETRY_MS = 800;
const RECOGNITION_RESET_THRESHOLD = 0.6;

function drawOverlay(
  canvas: HTMLCanvasElement | null,
  snapshot: DetectionSnapshot | null,
  displayLabel: string,
  recognizedName?: string,
) {
  const context = canvas?.getContext("2d");
  if (!context) return;

  context.clearRect(0, 0, canvas.width, canvas.height);

  if (!snapshot?.hasFace || !snapshot.firstFaceBox) {
    return;
  }

  const { originX, originY, width, height } = snapshot.firstFaceBox;
  const paddedSize = Math.max(width, height) * 1.15;
  const squareSize = Math.min(paddedSize, canvas.width, canvas.height);
  const squareX = Math.max(0, Math.min(originX + (width - squareSize) / 2, canvas.width - squareSize));
  const squareY = Math.max(0, Math.min(originY + (height - squareSize) / 2, canvas.height - squareSize));
  const corner = Math.max(18, squareSize * 0.14);

  context.strokeStyle = recognizedName ? "#22c55e" : "#96ffde";
  context.lineWidth = 4;
  context.strokeRect(squareX, squareY, squareSize, squareSize);

  context.strokeStyle = "#ffffff";
  context.lineWidth = 5;
  context.beginPath();
  context.moveTo(squareX, squareY + corner);
  context.lineTo(squareX, squareY);
  context.lineTo(squareX + corner, squareY);
  context.moveTo(squareX + squareSize - corner, squareY);
  context.lineTo(squareX + squareSize, squareY);
  context.lineTo(squareX + squareSize, squareY + corner);
  context.moveTo(squareX, squareY + squareSize - corner);
  context.lineTo(squareX, squareY + squareSize);
  context.lineTo(squareX + corner, squareY + squareSize);
  context.moveTo(squareX + squareSize - corner, squareY + squareSize);
  context.lineTo(squareX + squareSize, squareY + squareSize);
  context.lineTo(squareX + squareSize, squareY + squareSize - corner);
  context.stroke();

  context.fillStyle = recognizedName ? "rgba(34, 197, 94, 0.14)" : "rgba(150, 255, 222, 0.14)";
  context.fillRect(squareX, squareY, squareSize, squareSize);

  context.fillStyle = "rgba(8, 24, 38, 0.78)";
  context.fillRect(squareX, Math.max(0, squareY - 28), 140, 24);

  // The canvas itself is mirrored with CSS so the overlay matches the selfie view.
  // Flip just the text in canvas space so it reads normally on screen.
  context.save();
  context.scale(-1, 1);
  context.fillStyle = recognizedName ? "#22c55e" : "#ecfff9";
  context.font = "14px Segoe UI";
  context.fillText(displayLabel, -(squareX + 130), Math.max(16, squareY - 11));
  context.restore();
}

export default function CameraPanel({ 
  onDetectionChange,
  onRecognize,
  recognizedName,
  isRecognizing
}: { 
  onDetectionChange?: (snapshot: DetectionSnapshot | null) => void;
  onRecognize?: (snapshot: DetectionSnapshot) => boolean | Promise<boolean>;
  recognizedName?: string;
  isRecognizing?: boolean;
}) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const overlayRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef(0);
  const lastDetectionAtRef = useRef(0);
  const mediaPipeLab = useMediaPipeLab();
  const [cameraState, setCameraState] = useState("idle");
  const [cameraError, setCameraError] = useState("");
  const [latestSnapshot, setLatestSnapshot] = useState<DetectionSnapshot | null>(null);
  const [localRecognizing, setLocalRecognizing] = useState(false);
  const lastAttemptedTimeRef = useRef(0);
  const lastAttemptedEmbeddingRef = useRef<string>("");
  const lockedEmbeddingRef = useRef<number[] | null>(null);
  const wasFacePresentRef = useRef(false);
  const recognizeRunIdRef = useRef(0);
  const recognitionLockedRef = useRef(false);

  const recognitionActive = localRecognizing || !!isRecognizing;
  const isRecognitionMode = !!onRecognize;
  const statusLabel = !latestSnapshot?.hasFace
    ? "0"
    : recognizedName
      ? recognizedName
      : isRecognitionMode
        ? "Unknown"
        : `Face ${latestSnapshot.detectedFaces}`;

  useEffect(() => {
    onDetectionChange?.(latestSnapshot);
  }, [latestSnapshot, onDetectionChange]);

  const faceJustLeft = wasFacePresentRef.current && !latestSnapshot?.hasFace;
  const faceJustAppeared = !wasFacePresentRef.current && latestSnapshot?.hasFace;

  useEffect(() => {
    if (faceJustLeft) {
      lastAttemptedEmbeddingRef.current = "";
      lastAttemptedTimeRef.current = 0;
      recognitionLockedRef.current = false;
      lockedEmbeddingRef.current = null;
    }

    if (
      latestSnapshot?.hasFace &&
      recognitionLockedRef.current &&
      hasMeaningfulEmbeddingChange(
        latestSnapshot.embedding,
        lockedEmbeddingRef.current ?? undefined,
        RECOGNITION_RESET_THRESHOLD,
      )
    ) {
      recognitionLockedRef.current = false;
      lockedEmbeddingRef.current = null;
      lastAttemptedEmbeddingRef.current = "";
      lastAttemptedTimeRef.current = 0;
    }
    wasFacePresentRef.current = !!latestSnapshot?.hasFace;
  }, [latestSnapshot]);

  useEffect(() => {
    if (!onRecognize || !latestSnapshot?.hasFace) {
      return;
    }
    if (recognitionActive) {
      return;
    }
    if (recognitionLockedRef.current) {
      return;
    }
    const currentEmbeddingKey = getEmbeddingKey(latestSnapshot.embedding);
    const now = Date.now();
    const isRecentUnmatchedRetry =
      currentEmbeddingKey &&
      currentEmbeddingKey === lastAttemptedEmbeddingRef.current &&
      now - lastAttemptedTimeRef.current < UNMATCHED_RETRY_MS;
    if (isRecentUnmatchedRetry) {
      return;
    }
    const snapshot = latestSnapshot;
    const startedAt = Date.now();
    const runId = recognizeRunIdRef.current + 1;
    recognizeRunIdRef.current = runId;
    lastAttemptedEmbeddingRef.current = currentEmbeddingKey;
    lastAttemptedTimeRef.current = startedAt;
    console.debug("[CameraPanel] Recognition started", {
      runId,
      detectedFaces: snapshot.detectedFaces,
      embeddingKey: currentEmbeddingKey,
    });
    setLocalRecognizing(true);

    void Promise.resolve(onRecognize(snapshot))
      .then(() => {
        // Settle recognition for the current face until the person meaningfully changes or leaves frame.
        recognitionLockedRef.current = true;
        lockedEmbeddingRef.current = snapshot.embedding ?? null;
      })
      .catch(() => undefined)
      .finally(() => {
        const elapsed = Date.now() - startedAt;
        const remaining = Math.max(0, MIN_RECOGNITION_INDICATOR_MS - elapsed);
        window.setTimeout(() => {
          if (recognizeRunIdRef.current === runId) {
            console.debug("[CameraPanel] Recognition indicator cleared", {
              runId,
              elapsedMs: Date.now() - startedAt,
            });
            setLocalRecognizing(false);
          }
        }, remaining);
      });
  }, [latestSnapshot, onRecognize, recognitionActive]);

  const overlayLabel = latestSnapshot?.hasFace
    ? recognizedName
      ? recognizedName
      : isRecognitionMode
        ? "Unknown"
        : `Faces: ${latestSnapshot.detectedFaces}`
    : "";

  useEffect(() => {
    drawOverlay(overlayRef.current, latestSnapshot, overlayLabel, recognizedName);
  }, [latestSnapshot, overlayLabel, recognizedName]);

  function syncOverlaySize() {
    const video = videoRef.current;
    const overlay = overlayRef.current;
    if (!video || !overlay) return;

    const width = video.videoWidth || 1280;
    const height = video.videoHeight || 720;
    if (overlay.width !== width) overlay.width = width;
    if (overlay.height !== height) overlay.height = height;
  }

  function stopCamera() {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = 0;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.srcObject = null;
    }

    setLatestSnapshot(null);
    setCameraState("stopped");
    setCameraError("");
  }

  async function runDetectionLoop() {
    const video = videoRef.current;
    if (!video) return;
    syncOverlaySize();

    const now = performance.now();
    if (now - lastDetectionAtRef.current >= 120) {
      lastDetectionAtRef.current = now;
      try {
        const snapshot = await mediaPipeLab.detectFromVideoFrame(video, now);
        setLatestSnapshot({
          ...snapshot,
          detectedAt: new Date().toLocaleTimeString(),
        });
        setCameraState("streaming");
        setCameraError("");
      } catch (error) {
        setCameraError(error instanceof Error ? error.message : "Detection failed.");
        setCameraState("error");
      }
    }

    animationFrameRef.current = requestAnimationFrame(runDetectionLoop);
  }

  async function startCamera() {
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError("Camera access is not available in this browser.");
      setCameraState("error");
      return;
    }

    setCameraError("");
    setCameraState("starting");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "user",
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });

      streamRef.current = stream;

      const video = videoRef.current;
      if (!video) {
        throw new Error("Camera surface did not initialize.");
      }

      video.srcObject = stream;
      await video.play();

      const overlay = overlayRef.current;
      if (overlay) {
        overlay.width = video.videoWidth || 1280;
        overlay.height = video.videoHeight || 720;
      }

      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }

      lastDetectionAtRef.current = 0;
      animationFrameRef.current = requestAnimationFrame(runDetectionLoop);
    } catch (error) {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }

      setCameraError(error instanceof Error ? error.message : "Could not start the camera.");
      setCameraState("error");
    }
  }

  return (
    <section className="panel camera-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Camera</p>
          <h3>Live Entry Feed</h3>
        </div>
        <span className="panel-tag">
          {cameraState === "streaming" ? "MediaPipe live" : "Live detect"}
          {recognitionActive && " - Identifying"}
        </span>
      </div>

      <div className="camera-status-row">
        <div className="status-card">
          <strong>Camera State</strong>
          <span>{cameraState}</span>
        </div>
        <div className="status-card">
          <strong>Detector</strong>
          <span>{mediaPipeLab.status}</span>
        </div>
        <div className="status-card">
          <strong>Faces In Frame</strong>
          <span>
            {statusLabel}
            {recognitionActive ? (
              <>
                {" "}
                <span className="inline-activity">
                  <span className="inline-activity-spinner" aria-hidden="true" />
                  Identifying
                </span>
              </>
            ) : null}
          </span>
        </div>
      </div>

      {cameraError ? <p className="error-banner">{cameraError}</p> : null}

      <div className="camera-stage">
        <div className="camera-frame live-camera-frame">
          <video ref={videoRef} className="live-camera-video" playsInline muted />
          <canvas ref={overlayRef} className="live-camera-overlay" />
          {recognitionActive ? (
            <div className="camera-frame-badge">
              <span className="inline-activity">
                <span className="inline-activity-spinner" aria-hidden="true" />
                Identifying
              </span>
            </div>
          ) : null}
          {cameraState !== "streaming" ? (
            <div className="camera-empty-state">
              {cameraState === "starting" ? (
                <strong>Starting camera...</strong>
              ) : (
                <>
                  <strong>Start Camera to Begin</strong>
                  <button type="button" onClick={startCamera} style={{ marginTop: "1rem", padding: "0.75rem 1.5rem", backgroundColor: "#3b82f6", color: "white", border: "none", borderRadius: "8px", cursor: "pointer", fontSize: "1rem" }}>
                    Start Camera
                  </button>
                </>
              )}
            </div>
          ) : null}
        </div>
      </div>

      <div className="lab-grid">
        <div className="status-card">
          <strong>Frame</strong>
          <span>{latestSnapshot ? `${latestSnapshot.frameWidth} x ${latestSnapshot.frameHeight}` : "Waiting for camera"}</span>
        </div>
        <div className="status-card">
          <strong>Last Detection</strong>
          <span>{latestSnapshot?.detectedAt ?? "No frames analyzed yet"}</span>
        </div>
      </div>
    </section>
  );
}
