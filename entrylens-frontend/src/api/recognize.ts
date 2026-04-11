import { apiFetch } from "./client";

export interface RecognizeRequest {
  embedding: number[];
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

export async function recognize(embedding: number[]): Promise<RecognizeResponse> {
  return apiFetch<RecognizeResponse>("/api/v1/recognize", {
    method: "POST",
    body: JSON.stringify({
      embedding,
    }),
  });
}

export async function recognizeCandidates(embedding: number[]): Promise<CandidateMatch[]> {
  return apiFetch<CandidateMatch[]>("/api/v1/recognize/candidates", {
    method: "POST",
    body: JSON.stringify({
      embedding,
    }),
  });
}
