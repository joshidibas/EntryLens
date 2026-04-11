import { apiFetch, buildApiUrl } from "./client";

export interface IdentitySummary {
  id: string;
  display_name: string;
  identity_type: string;
  status: string;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
  embedding_count: number;
  profile_sample_id: string | null;
}

export interface IdentitySampleSummary {
  id: string;
  created_at: string | null;
  updated_at: string | null;
  sample_kind: string;
  image_path: string | null;
  capture_source: string | null;
  capture_confidence: number | null;
  is_reference: boolean;
  is_profile_source: boolean;
}

export interface AddIdentitySampleResponse {
  added: boolean;
  identity_id: string;
  sample_count: number;
  message: string | null;
}

export interface IdentitySampleActionResponse {
  ok: boolean;
  identity_id: string;
  sample_id: string;
  message: string | null;
}

export interface IdentityDetail {
  id: string;
  display_name: string;
  identity_type: string;
  status: string;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
  sample_count: number;
  profile_sample_id: string | null;
}

export interface IdentityDeleteResponse {
  ok: boolean;
  identity_id: string;
}

export function getIdentitySampleImageUrl(imagePath: string | null | undefined): string | null {
  if (!imagePath) {
    return null;
  }

  const params = new URLSearchParams({ image_path: imagePath });
  return buildApiUrl(`/api/v1/identities/sample-image?${params.toString()}`);
}

export async function listIdentities(): Promise<IdentitySummary[]> {
  return apiFetch<IdentitySummary[]>("/api/v1/identities");
}

export async function createIdentity(
  displayName: string,
  identityType: string,
  status = "active",
  notes: string | null = null,
): Promise<IdentityDetail> {
  return apiFetch<IdentityDetail>("/api/v1/identities", {
    method: "POST",
    body: JSON.stringify({
      display_name: displayName,
      identity_type: identityType,
      status,
      notes,
    }),
  });
}

export async function getIdentity(identityId: string): Promise<IdentityDetail> {
  return apiFetch<IdentityDetail>(`/api/v1/identities/${identityId}`);
}

export async function updateIdentity(
  identityId: string,
  displayName: string,
  identityType: string,
  status: string,
  notes: string | null,
): Promise<IdentityDetail> {
  return apiFetch<IdentityDetail>(`/api/v1/identities/${identityId}`, {
    method: "PATCH",
    body: JSON.stringify({
      display_name: displayName,
      identity_type: identityType,
      status,
      notes,
    }),
  });
}

export async function deleteIdentity(identityId: string): Promise<IdentityDeleteResponse> {
  return apiFetch<IdentityDeleteResponse>(`/api/v1/identities/${identityId}`, {
    method: "DELETE",
  });
}

export async function addEmbeddingToIdentity(
  identityId: string,
  embedding: number[],
  sourceConfidence?: number,
  imageDataUrl?: string | null,
): Promise<AddIdentitySampleResponse> {
  return apiFetch<AddIdentitySampleResponse>(`/api/v1/identities/${identityId}/embeddings`, {
    method: "POST",
    body: JSON.stringify({
      embedding,
      sample_kind: "face",
      image_data_url: imageDataUrl ?? null,
      capture_source: "unknown-review",
      capture_confidence: sourceConfidence ?? null,
    }),
  });
}

export async function listEmbeddingsForIdentity(identityId: string): Promise<IdentitySampleSummary[]> {
  return apiFetch<IdentitySampleSummary[]>(`/api/v1/identities/${identityId}/embeddings`);
}

export async function deleteEmbedding(identityId: string, embeddingId: string): Promise<IdentitySampleActionResponse> {
  return apiFetch<IdentitySampleActionResponse>(`/api/v1/identities/${identityId}/embeddings/${embeddingId}`, {
    method: "DELETE",
  });
}

export async function promoteEmbedding(identityId: string, embeddingId: string): Promise<IdentitySampleActionResponse> {
  return apiFetch<IdentitySampleActionResponse>(`/api/v1/identities/${identityId}/embeddings/${embeddingId}/promote`, {
    method: "POST",
  });
}

export async function setProfileSample(identityId: string, embeddingId: string): Promise<IdentitySampleActionResponse> {
  return apiFetch<IdentitySampleActionResponse>(`/api/v1/identities/${identityId}/embeddings/${embeddingId}/set-profile`, {
    method: "POST",
  });
}
