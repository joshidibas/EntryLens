import { FaceLandmarker, FilesetResolver } from "@mediapipe/tasks-vision";
import { useRef, useState } from "react";
import type { DetectionSnapshot, MediaPipePoint } from "../types";

const WASM_ROOT = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.22-rc.20250304/wasm";
const MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task";

function loadImageFromBlob(blob) {
  return new Promise((resolve, reject) => {
    const objectUrl = URL.createObjectURL(blob);
    const image = new Image();
    image.onload = () => {
      URL.revokeObjectURL(objectUrl);
      resolve(image);
    };
    image.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("Could not decode the selected image for MediaPipe."));
    };
    image.src = objectUrl;
  });
}

function toPoint(point: { x: number; y: number; z: number }): MediaPipePoint {
  return {
    x: Number(point.x.toFixed(4)),
    y: Number(point.y.toFixed(4)),
    z: Number(point.z.toFixed(4)),
  };
}

function captureVideoFrameDataUrl(video: HTMLVideoElement): string | undefined {
  const width = video.videoWidth || video.clientWidth || 0;
  const height = video.videoHeight || video.clientHeight || 0;
  if (!width || !height) {
    return undefined;
  }

  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext("2d");
  if (!context) {
    return undefined;
  }

  context.drawImage(video, 0, 0, width, height);
  return canvas.toDataURL("image/jpeg", 0.85);
}

function summarizeLandmarks(result: any, image: HTMLImageElement): DetectionSnapshot {
  const faceCount = result.faceLandmarks?.length ?? 0;
  const firstFace = result.faceLandmarks?.[0] ?? [];

  let embedding: number[] | undefined;
  if (result.facialTransformationMatrixes && result.facialTransformationMatrixes.length > 0) {
    const matrix = result.facialTransformationMatrixes[0].data;
    if (matrix && matrix.length === 16) {
      embedding = Array.from(matrix);
    }
  }

  return {
    engine: "mediapipe",
    model: "face-landmarker",
    detectedFaces: faceCount,
    hasFace: faceCount > 0,
    imageWidth: image.naturalWidth || image.width,
    imageHeight: image.naturalHeight || image.height,
    firstFaceLandmarkCount: firstFace.length,
    sampleLandmarks: firstFace.slice(0, 5).map(toPoint),
    embedding,
  };
}

function summarizeVideoLandmarks(result: any, video: HTMLVideoElement): DetectionSnapshot {
  const faceCount = result.faceLandmarks?.length ?? 0;
  const firstFace = result.faceLandmarks?.[0] ?? [];
  const frameWidth = video.videoWidth || video.clientWidth || 0;
  const frameHeight = video.videoHeight || video.clientHeight || 0;
  const xs = firstFace.map((point) => point.x * frameWidth);
  const ys = firstFace.map((point) => point.y * frameHeight);
  const firstFaceBox = xs.length > 0 && ys.length > 0 ? {
    originX: Math.max(0, Math.min(...xs)),
    originY: Math.max(0, Math.min(...ys)),
    width: Math.max(...xs) - Math.min(...xs),
    height: Math.max(...ys) - Math.min(...ys),
  } : null;

  let embedding: number[] | undefined;
  if (result.facialTransformationMatrixes && result.facialTransformationMatrixes.length > 0) {
    const matrix = result.facialTransformationMatrixes[0].data;
    if (matrix && matrix.length === 16) {
      embedding = Array.from(matrix);
    }
  }

  return {
    engine: "mediapipe",
    model: "face-landmarker",
    detectedFaces: faceCount,
    hasFace: faceCount > 0,
    frameWidth,
    frameHeight,
    firstFaceLandmarkCount: firstFace.length,
    sampleLandmarks: firstFace.slice(0, 5).map(toPoint),
    firstFaceBox: firstFaceBox ? {
      originX: Number(firstFaceBox.originX.toFixed(1)),
      originY: Number(firstFaceBox.originY.toFixed(1)),
      width: Number(firstFaceBox.width.toFixed(1)),
      height: Number(firstFaceBox.height.toFixed(1)),
    } : null,
    embedding,
    imageDataUrl: faceCount > 0 ? captureVideoFrameDataUrl(video) : undefined,
  };
}

export function useMediaPipeLab() {
  const imageDetectorRef = useRef<FaceLandmarker | null>(null);
  const videoDetectorRef = useRef<FaceLandmarker | null>(null);
  const [status, setStatus] = useState("idle");

  async function createDetector(runningMode: "IMAGE" | "VIDEO") {
    const filesetResolver = await FilesetResolver.forVisionTasks(WASM_ROOT);
    return FaceLandmarker.createFromOptions(filesetResolver, {
      baseOptions: {
        modelAssetPath: MODEL_URL,
      },
      runningMode,
      numFaces: 5,
      outputFaceBlendshapes: false,
      outputFacialTransformationMatrixes: true,
      minFaceDetectionConfidence: 0.5,
      minFacePresenceConfidence: 0.5,
      minTrackingConfidence: 0.5,
    });
  }

  async function ensureImageDetector() {
    if (imageDetectorRef.current) {
      return imageDetectorRef.current;
    }

    setStatus("loading");
    imageDetectorRef.current = await createDetector("IMAGE");
    setStatus("ready");
    return imageDetectorRef.current;
  }

  async function ensureVideoDetector() {
    if (videoDetectorRef.current) {
      return videoDetectorRef.current;
    }

    setStatus("loading");
    videoDetectorRef.current = await createDetector("VIDEO");
    setStatus("ready");
    return videoDetectorRef.current;
  }

  async function detectFromBlob(blob: Blob): Promise<DetectionSnapshot> {
    const detector = await ensureImageDetector();
    const image = await loadImageFromBlob(blob);
    const result = detector.detect(image);
    setStatus("ready");
    return summarizeLandmarks(result, image);
  }

  async function detectFromVideoFrame(video: HTMLVideoElement, timestampMs = performance.now()): Promise<DetectionSnapshot> {
    const detector = await ensureVideoDetector();
    const result = detector.detectForVideo(video, timestampMs);
    setStatus("ready");
    return summarizeVideoLandmarks(result, video);
  }

  return {
    status,
    detectFromBlob,
    detectFromVideoFrame,
  };
}
