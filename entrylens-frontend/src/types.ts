export type OperationId = "detect" | "recognize";

export interface LabModel {
  id: string;
  label: string;
  description: string;
}

export interface LabTarget {
  id: string;
  label: string;
  description: string;
  status?: "ready" | "planned";
  operation: OperationId;
  engine_kind: string;
  models: LabModel[];
  supports_enroll_upload?: boolean;
  supports_probe_upload?: boolean;
}

export interface LabStatePayload {
  targets?: LabTarget[];
  probe_files?: string[];
  enroll_files?: string[];
  artifacts?: Array<{ relative_path?: string; name?: string }>;
  state?: {
    people?: Record<string, unknown>;
  };
  credentials?: {
    has_api_key?: boolean;
    has_endpoint?: boolean;
    has_group_id?: boolean;
    requires_group_id?: boolean;
  };
}

export interface MediaPipePoint {
  x: number;
  y: number;
  z: number;
}

export interface FaceBox {
  originX: number;
  originY: number;
  width: number;
  height: number;
}

export interface DetectionSnapshot {
  engine: string;
  model: string;
  detectedFaces: number;
  hasFace: boolean;
  imageWidth?: number;
  imageHeight?: number;
  frameWidth?: number;
  frameHeight?: number;
  firstFaceLandmarkCount: number;
  sampleLandmarks: MediaPipePoint[];
  firstFaceBox?: FaceBox | null;
  detectedAt?: string;
  embedding?: number[];
}

export interface CommandResultPayload {
  ok?: boolean;
  target?: string;
  command?: string;
  selected_model?: string;
  result?: unknown;
  stderr?: string;
  stdout?: string;
  exit_code?: number;
}
