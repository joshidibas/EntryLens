import { apiFetch } from "./client";

export interface RecognizeRequest {
  model_id?: string;
  embedding?: number[] | null;
  image_data_url?: string | null;
  camera_id?: string;
}

export interface RecognizeResponse {
  matched: boolean;
  identity_id: string | null;
  name: string | null;
  similarity: number;
  message: string | null;
}

export interface CandidateMatch {
  identity_id: string;
  display_name: string;
  identity_type: string;
  similarity: number;
  sample_count: number;
}

export async function recognize(request: RecognizeRequest): Promise<RecognizeResponse> {
  return apiFetch<RecognizeResponse>("/api/v1/recognize", {
    method: "POST",
    body: JSON.stringify({
      model_id: request.model_id ?? "local-default",
      embedding: request.embedding ?? null,
      image_data_url: request.image_data_url ?? null,
      camera_id: request.camera_id ?? null,
    }),
  });
}

export async function recognizeCandidates(request: RecognizeRequest): Promise<CandidateMatch[]> {
  return apiFetch<CandidateMatch[]>("/api/v1/recognize/candidates", {
    method: "POST",
    body: JSON.stringify({
      model_id: request.model_id ?? "local-default",
      embedding: request.embedding ?? null,
      image_data_url: request.image_data_url ?? null,
      camera_id: request.camera_id ?? null,
    }),
  });
}
