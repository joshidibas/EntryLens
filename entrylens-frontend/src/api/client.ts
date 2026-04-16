const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY ?? "";

export class ApiError extends Error {
  status: number;
  errorCode?: string;
  modelId?: string | null;
  detail?: string;
  suggestion?: string | null;

  constructor(
    message: string,
    options: {
      status: number;
      errorCode?: string;
      modelId?: string | null;
      detail?: string;
      suggestion?: string | null;
    },
  ) {
    super(message);
    this.name = "ApiError";
    this.status = options.status;
    this.errorCode = options.errorCode;
    this.modelId = options.modelId;
    this.detail = options.detail;
    this.suggestion = options.suggestion;
  }
}

export function buildApiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

export async function apiFetch<T = unknown>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers ?? {});
  if (API_KEY) {
    headers.set("X-API-Key", API_KEY);
  }
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  if (!headers.has("Content-Type") && options.body && !isFormData) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(buildApiUrl(path), {
    ...options,
    headers,
  });

  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    if (typeof payload === "string") {
      throw new ApiError(payload || "Request failed.", { status: response.status, detail: payload || "Request failed." });
    }
    throw new ApiError(payload.detail ?? "Request failed.", {
      status: response.status,
      errorCode: payload.error,
      modelId: payload.model_id,
      detail: payload.detail ?? "Request failed.",
      suggestion: payload.suggestion,
    });
  }

  return payload as T;
}

export async function apiFetchBlob(path: string, options: RequestInit = {}): Promise<Blob> {
  const headers = new Headers(options.headers ?? {});
  if (API_KEY) {
    headers.set("X-API-Key", API_KEY);
  }

  const response = await fetch(buildApiUrl(path), {
    ...options,
    headers,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new ApiError(text || "Request failed.", { status: response.status, detail: text || "Request failed." });
  }

  return response.blob();
}
