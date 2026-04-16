import { apiFetch } from "./client";

export interface EnrollRequest {
  name: string;
  role?: string;
  model_id?: string;
  embedding?: number[] | null;
  image_data_url?: string | null;
}

export interface EnrollResponse {
  enrolled: boolean;
  subject_id: string | null;
  name: string;
  face_count: number;
  message: string | null;
}

export async function enroll(
  name: string,
  options: {
    modelId?: string;
    embedding?: number[] | null;
    imageDataUrl?: string | null;
  } = {},
): Promise<EnrollResponse> {
  return apiFetch<EnrollResponse>("/api/v1/enroll", {
    method: "POST",
    body: JSON.stringify({
      name,
      role: "visitor",
      model_id: options.modelId ?? "local-default",
      embedding: options.embedding ?? null,
      image_data_url: options.imageDataUrl ?? null,
    }),
  });
}
