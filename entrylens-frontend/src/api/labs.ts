import { apiFetch, apiFetchBlob } from "./client";
import type { LabStatePayload } from "../types";

export function getLabsState(target = "mediapipe"): Promise<LabStatePayload> {
  return apiFetch<LabStatePayload>(`/api/v1/labs?target=${encodeURIComponent(target)}`);
}

export function uploadEnrollImages(personName: string, files: File[], target = "local-recognition"): Promise<{ saved_files: string[]; person: string }> {
  const formData = new FormData();
  formData.append("person_name", personName);
  formData.append("target", target);
  for (const file of files) {
    formData.append("files", file);
  }

  return apiFetch<{ saved_files: string[]; person: string }>("/api/v1/labs/enroll-images", {
    method: "POST",
    body: formData,
  });
}

export function uploadProbeImage(file: File, probeName = "", target = "mediapipe"): Promise<{ probe_file: string }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("target", target);
  if (probeName) {
    formData.append("probe_name", probeName);
  }

  return apiFetch<{ probe_file: string }>("/api/v1/labs/probe-image", {
    method: "POST",
    body: formData,
  });
}

export function runLabsCommand(
  command: string,
  options: { target?: string; filePath?: string; personName?: string } = {},
): Promise<Record<string, unknown>> {
  const params = new URLSearchParams();
  params.set("target", options.target || "mediapipe");
  if (options.filePath) {
    params.set("file_path", options.filePath);
  }
  if (options.personName) {
    params.set("person_name", options.personName);
  }

  const suffix = params.toString() ? `?${params.toString()}` : "";
  return apiFetch<Record<string, unknown>>(`/api/v1/labs/commands/${command}${suffix}`, {
    method: "POST",
  });
}

export function fetchLabsFileBlob(target: string, filePath: string): Promise<Blob> {
  const params = new URLSearchParams();
  params.set("target", target);
  params.set("file_path", filePath);
  return apiFetchBlob(`/api/v1/labs/files?${params.toString()}`);
}
