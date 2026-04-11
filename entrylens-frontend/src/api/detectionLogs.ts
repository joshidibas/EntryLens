import { apiFetch, buildApiUrl } from "./client";

export interface DetectionLogIdentitySummary {
  id: string;
  display_name: string;
  identity_type: string;
  status: string;
}

export interface DetectionLogSummary {
  id: string;
  source: string;
  camera_id: string | null;
  image_path: string | null;
  auto_similarity: number | null;
  auto_tagged: boolean;
  review_status: string;
  detected_at: string | null;
  current_identity: DetectionLogIdentitySummary | null;
  auto_identity: DetectionLogIdentitySummary | null;
  promoted_embedding_id: string | null;
}

export interface DetectionLogDetail extends DetectionLogSummary {
  auto_display_name: string | null;
  review_notes: string | null;
  reviewed_at: string | null;
  promoted_at: string | null;
  embedding_present: boolean;
}

export interface CreateDetectionLogResponse {
  created: boolean;
  detection_log: DetectionLogDetail;
}

export interface DetectionLogActionResponse {
  ok: boolean;
  detection_log_id: string;
  message: string;
}

export function getDetectionLogImageUrl(imagePath: string | null | undefined): string | null {
  if (!imagePath) {
    return null;
  }

  const params = new URLSearchParams({ image_path: imagePath });
  return buildApiUrl(`/api/v1/identities/sample-image?${params.toString()}`);
}

export async function createDetectionLog(payload: {
  embedding: number[];
  image_data_url?: string | null;
  camera_id?: string | null;
  auto_similarity?: number | null;
  auto_identity_id?: string | null;
  auto_display_name?: string | null;
}): Promise<CreateDetectionLogResponse> {
  return apiFetch<CreateDetectionLogResponse>("/api/v1/detection-logs", {
    method: "POST",
    body: JSON.stringify({
      embedding: payload.embedding,
      image_data_url: payload.image_data_url ?? null,
      camera_id: payload.camera_id ?? null,
      auto_similarity: payload.auto_similarity ?? null,
      auto_identity_id: payload.auto_identity_id ?? null,
      auto_display_name: payload.auto_display_name ?? null,
    }),
  });
}

export async function listDetectionLogs(): Promise<DetectionLogSummary[]> {
  return apiFetch<DetectionLogSummary[]>("/api/v1/detection-logs");
}

export async function getDetectionLog(detectionLogId: string): Promise<DetectionLogDetail> {
  return apiFetch<DetectionLogDetail>(`/api/v1/detection-logs/${detectionLogId}`);
}

export async function updateDetectionLog(
  detectionLogId: string,
  payload: {
    review_status?: string;
    review_notes?: string | null;
    display_name?: string;
    identity_type?: string;
    status?: string;
  },
): Promise<DetectionLogDetail> {
  return apiFetch<DetectionLogDetail>(`/api/v1/detection-logs/${detectionLogId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function mergeDetectionLogIdentity(
  detectionLogId: string,
  targetIdentityId: string,
): Promise<DetectionLogActionResponse> {
  return apiFetch<DetectionLogActionResponse>(`/api/v1/detection-logs/${detectionLogId}/merge-identity`, {
    method: "POST",
    body: JSON.stringify({
      target_identity_id: targetIdentityId,
    }),
  });
}

export async function promoteDetectionLogSample(
  detectionLogId: string,
  payload: {
    target_identity_id?: string | null;
    sample_kind?: string;
    capture_source?: string;
    set_as_reference?: boolean;
    set_as_profile?: boolean;
  } = {},
): Promise<DetectionLogActionResponse> {
  return apiFetch<DetectionLogActionResponse>(`/api/v1/detection-logs/${detectionLogId}/promote-sample`, {
    method: "POST",
    body: JSON.stringify({
      target_identity_id: payload.target_identity_id ?? null,
      sample_kind: payload.sample_kind ?? "face",
      capture_source: payload.capture_source ?? "detection-log",
      set_as_reference: payload.set_as_reference ?? false,
      set_as_profile: payload.set_as_profile ?? false,
    }),
  });
}
