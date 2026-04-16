import type { ChangeEvent } from "react";
import { useEffect, useMemo, useState } from "react";
import { ApiError } from "../api/client";
import CameraPanel from "../components/CameraPanel";
import { getLabsState } from "../api/labs";
import { addEmbeddingToIdentity, listIdentities, type IdentitySummary } from "../api/identities";
import { enroll, EnrollResponse } from "../api/enroll";
import { useRecognitionSession } from "../hooks/useRecognitionSession";
import { useMediaPipeLab } from "../hooks/useMediaPipeLab";
import type { CommandResultPayload, LabModel, LabStatePayload, LabTarget, OperationId } from "../types";

const FALLBACK_TARGETS: LabTarget[] = [
  { id: "mediapipe", label: "MediaPipe", description: "Local browser-side face detection and landmark playground.", status: "ready", operation: "detect", engine_kind: "local", models: [{ id: "face-landmarker", label: "Face Landmarker", description: "Browser-side landmarks and pose gating." }] },
  {
    id: "local-recognition",
    label: "Local Recognition",
    description: "Local enrollment and recognition flow backed by MediaPipe embeddings and Supabase storage.",
    status: "ready",
    operation: "recognize",
    engine_kind: "local",
    models: [
      { id: "local-default", label: "Local Default", description: "Local recognition with MediaPipe embeddings.", input_mode: "browser-embedding", enabled: true, status: "ready", health: "ok" },
      { id: "insightface-local", label: "InsightFace (Local)", description: "Backend-hosted InsightFace embedding extraction.", input_mode: "image-data", enabled: false, status: "disabled", health: "unavailable", unavailable_reason: "Install local InsightFace backend dependencies to enable this model." },
    ],
  },
];

const OPERATIONS: Array<{ id: OperationId; label: string }> = [
  { id: "detect", label: "Detect Face" },
  { id: "recognize", label: "Recognize Face" },
];

export default function LabsPage() {
  const [selectedOperation, setSelectedOperation] = useState<OperationId>("recognize");
  const [selectedTarget, setSelectedTarget] = useState("local-recognition");
  const [selectedModel, setSelectedModel] = useState("");
  const [lab, setLab] = useState<LabStatePayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [, setCommandResult] = useState<CommandResultPayload | null>(null);
  const [busyCommand, setBusyCommand] = useState("");
  const [personName, setPersonName] = useState("");
  const [localTab, setLocalTab] = useState<"enroll" | "identify">("identify");
  const [identities, setIdentities] = useState<IdentitySummary[]>([]);
  const [selectedIdentityId, setSelectedIdentityId] = useState("");
  const [unknownName, setUnknownName] = useState("");
  const [unknownActionBusy, setUnknownActionBusy] = useState("");
  useMediaPipeLab();
  const {
    liveDetection,
    identifyResult,
    candidateMatches,
    isIdentifying,
    handleDetectionChange,
    runRecognition,
    setIdentifyResult,
    setCandidateMatches,
  } = useRecognitionSession({
    includeCandidates: true,
    onError: (message) => setError(message),
  });

  const targets = lab?.targets ?? FALLBACK_TARGETS;
  const filteredTargets = useMemo(() => targets.filter((target) => target.operation === selectedOperation), [targets, selectedOperation]);
  const currentTarget = useMemo(() => filteredTargets.find((target) => target.id === selectedTarget) ?? filteredTargets[0] ?? null, [filteredTargets, selectedTarget]);
  const enabledModels = useMemo(() => (currentTarget?.models ?? []).filter((model) => model.enabled !== false), [currentTarget]);
  const currentModel = useMemo<LabModel | null>(() => currentTarget?.models?.find((model) => model.id === selectedModel) ?? enabledModels[0] ?? currentTarget?.models?.[0] ?? null, [currentTarget, selectedModel, enabledModels]);
  const isRecognize = selectedOperation === "recognize";
  const isPlanned = currentTarget?.status === "planned";
  const isMediaPipe = currentTarget?.id === "mediapipe";
  const isLocalRecognition = currentTarget?.id === "local-recognition";
  const requiresRemoteImage = currentModel?.input_mode === "image-data";
  const hasRequiredModelInput = requiresRemoteImage ? !!liveDetection?.imageDataUrl : !!liveDetection?.embedding;

  function getRecognitionRequest(snapshot = liveDetection) {
    return {
      model_id: currentModel?.id ?? "local-default",
      embedding: requiresRemoteImage ? null : snapshot?.embedding ?? null,
      image_data_url: snapshot?.imageDataUrl ?? null,
    };
  }

  async function refreshState(targetOverride = currentTarget?.id ?? selectedTarget) {
    setLoading(true);
    setError("");
    try {
      const payload = await getLabsState(targetOverride);
      setLab(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load lab state.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refreshState();
  }, [selectedTarget]);

  useEffect(() => {
    if (!currentTarget) {
      return;
    }
    const selectableModels = currentTarget.models.filter((model) => model.enabled !== false);
    if (!selectableModels.some((model) => model.id === selectedModel)) {
      setSelectedModel(selectableModels[0]?.id ?? currentTarget.models[0]?.id ?? "");
    }
  }, [currentTarget, selectedModel]);

  useEffect(() => {
    void refreshIdentities();
  }, []);

  async function handleCommand(command: string) {
    setBusyCommand(command);
    setError("");
    setSuccess("");
    setCommandResult(null);
    try {
      if (isMediaPipe && command === "detect") {
        setSuccess("MediaPipe detect completed.");
      } else if (currentTarget?.id === "local-recognition" && command === "enroll") {
        if (!personName) {
          setError("Please enter a name to enroll.");
          setBusyCommand("");
          return;
        }
        if (!hasRequiredModelInput) {
          setError(requiresRemoteImage
            ? "No face image is available yet. Please ensure your face is visible in the camera."
            : "No face embedding. Please ensure your face is visible in the camera.");
          setBusyCommand("");
          return;
        }
        const result: EnrollResponse = await enroll(personName, {
          modelId: currentModel?.id,
          embedding: requiresRemoteImage ? null : liveDetection?.embedding ?? null,
          imageDataUrl: liveDetection?.imageDataUrl,
        });
        if (result.enrolled) {
          setSuccess(`Enrolled as ${result.name}`);
          setPersonName("");
        } else {
          setError(result.message || "Enrollment failed");
        }
      } else {
        setSuccess(`${command} completed.`);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.suggestion ? `${err.message} ${err.suggestion}` : err.message);
      } else {
        setError(err instanceof Error ? err.message : "Command failed.");
      }
    } finally {
      setBusyCommand("");
    }
  }

  async function refreshIdentities() {
    try {
      const items = await listIdentities();
      setIdentities(items);
      if (!selectedIdentityId && items[0]?.id) {
        setSelectedIdentityId(items[0].id);
      }
    } catch {
      // Keep the current screen usable even if identity listing fails.
    }
  }

  async function handleCreateFromUnknown() {
    if (!unknownName || !hasRequiredModelInput) {
      setError("Enter a name and keep a face visible before creating a new person.");
      return;
    }

    setUnknownActionBusy("create");
    setError("");
    setSuccess("");
    try {
      const result = await enroll(unknownName, {
        modelId: currentModel?.id,
        embedding: requiresRemoteImage ? null : liveDetection?.embedding ?? null,
        imageDataUrl: liveDetection?.imageDataUrl,
      });
      if (!result.enrolled) {
        setError(result.message || "Enrollment failed.");
        return;
      }
      setSuccess(`Created ${result.name} from the current unknown face sample.`);
      setUnknownName("");
      setCandidateMatches([]);
      setIdentifyResult({
        matched: true,
        identityId: result.subject_id,
        name: result.name,
        similarity: 1,
      });
      await refreshIdentities();
      if (result.subject_id) {
        setSelectedIdentityId(result.subject_id);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.suggestion ? `${err.message} ${err.suggestion}` : err.message);
      } else {
        setError(err instanceof Error ? err.message : "Could not create a new person.");
      }
    } finally {
      setUnknownActionBusy("");
    }
  }

  async function handleAddSampleToExisting() {
    if (!selectedIdentityId || !hasRequiredModelInput) {
      setError("Choose an existing person and keep a face visible before adding a sample.");
      return;
    }

    setUnknownActionBusy("append");
    setError("");
    setSuccess("");
    try {
      const selectedCandidate = candidateMatches.find((item) => item.identity_id === selectedIdentityId);
      const result = await addEmbeddingToIdentity(selectedIdentityId, {
        modelId: currentModel?.id,
        embedding: requiresRemoteImage ? null : liveDetection?.embedding ?? null,
        sourceConfidence: selectedCandidate?.similarity,
        imageDataUrl: liveDetection?.imageDataUrl,
      });
      const selectedIdentity = identities.find((item) => item.id === selectedIdentityId);
      setSuccess(result.message || `Added a new sample to ${selectedIdentity?.display_name ?? "the selected person"}.`);
      setCandidateMatches([]);
      await refreshIdentities();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.suggestion ? `${err.message} ${err.suggestion}` : err.message);
      } else {
        setError(err instanceof Error ? err.message : "Could not add a new sample to this person.");
      }
    } finally {
      setUnknownActionBusy("");
    }
  }

  return (
    <section className="lab-layout">
      {!isPlanned && isRecognize && isLocalRecognition ? (
        <section className="panel">
          <div className="panel-header">
            <div><p className="eyebrow">Local Recognition</p><h3>Enrollment & Identification</h3></div>
          </div>

          {error ? <p className="error-banner">{error}</p> : null}
          {success ? <p className="success-banner">{success}</p> : null}

          <label style={{ marginBottom: "1rem", display: "block" }}>
            <span style={{ display: "block", marginBottom: "0.35rem", fontWeight: 600, fontSize: "0.875rem" }}>Recognition model</span>
            <select
              value={currentModel?.id ?? ""}
              onChange={(event: ChangeEvent<HTMLSelectElement>) => setSelectedModel(event.target.value)}
              style={{ width: "100%", padding: "0.65rem", borderRadius: "8px", border: "1px solid #cbd5e1" }}
            >
              {(currentTarget?.models ?? []).map((model) => (
                <option key={model.id} value={model.id} disabled={model.enabled === false}>
                  {model.enabled === false ? `${model.label} (not configured)` : model.label}
                </option>
              ))}
            </select>
            {currentModel ? <span style={{ display: "block", marginTop: "0.35rem", color: "#64748b", fontSize: "0.85rem" }}>{currentModel.description}</span> : null}
            {currentModel?.health ? (
              <span style={{ display: "block", marginTop: "0.35rem", color: currentModel.health === "ok" ? "#15803d" : currentModel.health === "degraded" ? "#b45309" : "#b91c1c", fontSize: "0.85rem" }}>
                Health: {currentModel.health}
              </span>
            ) : null}
            {currentModel?.enabled === false && currentModel.unavailable_reason ? (
              <span style={{ display: "block", marginTop: "0.35rem", color: "#b45309", fontSize: "0.85rem" }}>{currentModel.unavailable_reason}</span>
            ) : null}
          </label>

          <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
            <button type="button" onClick={() => { setLocalTab("enroll"); setIdentifyResult(null); }} style={{ padding: "0.5rem 1rem", backgroundColor: localTab === "enroll" ? "#3b82f6" : "#e5e7eb", color: localTab === "enroll" ? "white" : "#374151", border: "none", borderRadius: "4px", cursor: "pointer" }}>Enroll</button>
            <button type="button" onClick={() => { setLocalTab("identify"); setIdentifyResult(null); }} style={{ padding: "0.5rem 1rem", backgroundColor: localTab === "identify" ? "#3b82f6" : "#e5e7eb", color: localTab === "identify" ? "white" : "#374151", border: "none", borderRadius: "4px", cursor: "pointer" }}>Identify</button>
          </div>

          {localTab === "enroll" ? (
            <>
              <p className="helper-copy">Enter your name, position your face in the camera, then click Enroll.</p>
              <label style={{ marginBottom: "0.5rem", display: "block" }}>Your name<input value={personName} onChange={(event: ChangeEvent<HTMLInputElement>) => setPersonName(event.target.value)} placeholder="Enter your name" style={{ width: "100%", padding: "0.5rem", marginTop: "0.25rem" }} /></label>
              <CameraPanel onDetectionChange={handleDetectionChange} />
              <div style={{ marginTop: "0.5rem", fontSize: "0.875rem" }}>
                {liveDetection?.hasFace ? <span style={{ color: "#22c55e" }}>Face detected</span> : <span style={{ color: "#6b7280" }}>No face detected</span>}
                {hasRequiredModelInput && <span style={{ marginLeft: "1rem" }}>{requiresRemoteImage ? "Image ready" : "Embedding ready"}</span>}
              </div>
              <button type="button" onClick={() => void handleCommand("enroll")} disabled={!personName || !hasRequiredModelInput || busyCommand === "enroll"} style={{ marginTop: "1rem", width: "100%", padding: "0.75rem", backgroundColor: (!personName || !hasRequiredModelInput) ? "#9ca3af" : "#3b82f6", color: "white", border: "none", borderRadius: "4px", fontSize: "1rem", fontWeight: "bold" }}>{busyCommand === "enroll" ? "Enrolling..." : "Enroll"}</button>
            </>
          ) : (
            <>
              <p className="helper-copy">Live camera with auto-recognition. Your name will appear when recognized.</p>
              <CameraPanel
                onDetectionChange={handleDetectionChange}
                onRecognize={(snapshot) => runRecognition(getRecognitionRequest(snapshot))}
                recognizedName={identifyResult?.matched ? identifyResult.name ?? undefined : undefined}
                isRecognizing={isIdentifying}
              />
              <div style={{ marginTop: "1rem", fontSize: "0.875rem" }}>
                <span style={{ color: liveDetection?.hasFace ? "#22c55e" : "#6b7280" }}>
                  {liveDetection?.hasFace ? `Face ${liveDetection.detectedFaces}` : "No face detected"}
                </span>
                {isIdentifying && <span style={{ color: "#3b82f6", marginLeft: "0.5rem" }}>Identifying...</span>}
              </div>
              {identifyResult?.matched && identifyResult.name ? (
                <div style={{ marginTop: "1rem", padding: "1rem", borderRadius: "8px", backgroundColor: "#dcfce7", border: "2px solid #22c55e" }}>
                  <div style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#166534" }}>{identifyResult.name}</div>
                  <div style={{ fontSize: "0.875rem", color: "#15803d" }}>Confidence: {(identifyResult.similarity * 100).toFixed(1)}%</div>
                </div>
              ) : null}
              {!isIdentifying && liveDetection?.hasFace && !identifyResult?.matched ? (
                <div style={{ marginTop: "1rem", padding: "1rem", borderRadius: "12px", backgroundColor: "#eff6ff", border: "1px solid #bfdbfe", display: "grid", gap: "1rem" }}>
                  <div>
                    <div style={{ fontSize: "1rem", fontWeight: 700, color: "#1d4ed8" }}>Unknown face</div>
                    <div style={{ fontSize: "0.875rem", color: "#334155" }}>
                      This face is not currently identified. You can create a new person or add this sample to an existing person to widen their embedding variety.
                    </div>
                  </div>

                  {candidateMatches.length > 0 ? (
                    <div style={{ display: "grid", gap: "0.5rem" }}>
                      <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "#0f172a" }}>Closest existing identities</div>
                      {candidateMatches.slice(0, 3).map((candidate) => (
                        <div key={candidate.identity_id} style={{ padding: "0.75rem", borderRadius: "10px", backgroundColor: "white", border: "1px solid #dbeafe" }}>
                          <div style={{ fontWeight: 600 }}>{candidate.display_name}</div>
                          <div style={{ fontSize: "0.875rem", color: "#475569" }}>
                            Match confidence: {(candidate.similarity * 100).toFixed(1)}% · Stored samples: {candidate.sample_count}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : null}

                  <div style={{ display: "grid", gap: "0.75rem" }}>
                    <label style={{ display: "grid", gap: "0.35rem" }}>
                      <span style={{ fontWeight: 600, fontSize: "0.875rem" }}>Create new person</span>
                      <input
                        value={unknownName}
                        onChange={(event: ChangeEvent<HTMLInputElement>) => setUnknownName(event.target.value)}
                        placeholder="Enter a new name"
                        style={{ width: "100%", padding: "0.65rem", borderRadius: "8px", border: "1px solid #cbd5e1" }}
                      />
                    </label>
                    <button
                      type="button"
                      onClick={() => void handleCreateFromUnknown()}
                      disabled={!unknownName || !hasRequiredModelInput || unknownActionBusy !== ""}
                      style={{ padding: "0.75rem 1rem", backgroundColor: "#2563eb", color: "white", border: "none", borderRadius: "8px", fontWeight: 700 }}
                    >
                      {unknownActionBusy === "create" ? "Creating..." : "Create New Person From This Face"}
                    </button>
                  </div>

                  <div style={{ display: "grid", gap: "0.75rem" }}>
                    <label style={{ display: "grid", gap: "0.35rem" }}>
                      <span style={{ fontWeight: 600, fontSize: "0.875rem" }}>Add as another sample to existing person</span>
                      <select
                        value={selectedIdentityId}
                        onChange={(event: ChangeEvent<HTMLSelectElement>) => setSelectedIdentityId(event.target.value)}
                        style={{ width: "100%", padding: "0.65rem", borderRadius: "8px", border: "1px solid #cbd5e1" }}
                      >
                        <option value="">Select an existing person</option>
                        {identities.map((identity) => (
                          <option key={identity.id} value={identity.id}>
                            {identity.display_name} ({identity.embedding_count} samples)
                          </option>
                        ))}
                      </select>
                    </label>
                    <button
                      type="button"
                      onClick={() => void handleAddSampleToExisting()}
                      disabled={!selectedIdentityId || !hasRequiredModelInput || unknownActionBusy !== ""}
                      style={{ padding: "0.75rem 1rem", backgroundColor: "#0f766e", color: "white", border: "none", borderRadius: "8px", fontWeight: 700 }}
                    >
                      {unknownActionBusy === "append" ? "Saving Sample..." : "Add Current Face As Another Sample"}
                    </button>
                  </div>
                </div>
              ) : null}
            </>
          )}
        </section>
      ) : null}

      <section className="panel">
        <div className="panel-header"><div><p className="eyebrow">Run</p><h3>Commands</h3></div></div>
        {isLocalRecognition ? (
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button type="button" onClick={() => void handleCommand("enroll")} disabled={busyCommand === "enroll"} style={{ padding: "0.75rem 1rem", backgroundColor: "#3b82f6", color: "white", border: "none", borderRadius: "4px" }}>Enroll</button>
          </div>
        ) : <p style={{ color: "#6b7280" }}>Select a target to see commands</p>}
      </section>
    </section>
  );
}
