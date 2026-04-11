import { apiFetch } from "./client";

export interface EnrollRequest {
  name: string;
  role?: string;
  embedding: number[];
  image_data_url?: string | null;
}

export interface EnrollResponse {
  enrolled: boolean;
  subject_id: string | null;
  name: string;
  face_count: number;
  message: string | null;
}

export async function enroll(name: string, embedding: number[], imageDataUrl?: string | null): Promise<EnrollResponse> {
  return apiFetch<EnrollResponse>("/api/v1/enroll", {
    method: "POST",
    body: JSON.stringify({
      name,
      role: "visitor",
      embedding,
      image_data_url: imageDataUrl ?? null,
    }),
  });
}
