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

export async function recognize(embedding: number[]): Promise<RecognizeResponse> {
  return apiFetch<RecognizeResponse>("/api/v1/recognize", {
    method: "POST",
    body: JSON.stringify({
      embedding,
    }),
  });
}