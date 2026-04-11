import type { ChangeEvent } from "react";
import { useEffect, useMemo, useState, useRef } from "react";
import CameraPanel from "../components/CameraPanel";
import LiveFeed from "../components/LiveFeed";
import { fetchLabsFileBlob, getLabsState, runLabsCommand } from "../api/labs";
import { enroll, EnrollResponse } from "../api/enroll";
import { recognize, RecognizeResponse } from "../api/recognize";
import { useMediaPipeLab } from "../hooks/useMediaPipeLab";
import type { CommandResultPayload, DetectionSnapshot, LabModel, LabStatePayload, LabTarget, OperationId } from "../types";

const FALLBACK_TARGETS: LabTarget[] = [
  { id: "mediapipe", label: "MediaPipe", description: "Local browser-side face detection and landmark playground.", status: "ready", operation: "detect", engine_kind: "local", models: [{ id: "face-landmarker", label: "Face Landmarker", description: "Browser-side landmarks and pose gating." }] },
  { id: "local-recognition", label: "Local Recognition", description: "Local enrollment and recognition flow backed by MediaPipe embeddings and Supabase storage.", status: "ready", operation: "recognize", engine_kind: "local", models: [{ id: "local-default", label: "Local Default", description: "Local recognition with MediaPipe embeddings." }] },
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
  const [commandResult, setCommandResult] = useState<CommandResultPayload | null>(null);
  const [busyCommand, setBusyCommand] = useState("");
  const [personName, setPersonName] = useState("");
  const [liveDetection, setLiveDetection] = useState<DetectionSnapshot | null>(null);
  const [localTab, setLocalTab] = useState<"enroll" | "identify">("enroll");
  const [identifyResult, setIdentifyResult] = useState<{name: string; similarity: number} | null>(null);
  const [isIdentifying, setIsIdentifying] = useState(false);
  const lastIdentifiedFaceRef = useRef<string>("");
  const mediaPipeLab = useMediaPipeLab();

  const targets = lab?.targets ?? FALLBACK_TARGETS;
  const filteredTargets = useMemo(() => targets.filter((target) => target.operation === selectedOperation), [targets, selectedOperation]);
  const currentTarget = useMemo(() => filteredTargets.find((target) => target.id === selectedTarget) ?? filteredTargets[0] ?? null, [filteredTargets, selectedTarget]);
  const currentModel = useMemo<LabModel | null>(() => currentTarget?.models?.find((model) => model.id === selectedModel) ?? currentTarget?.models?.[0] ?? null, [currentTarget, selectedModel]);
  const isRecognize = selectedOperation === "recognize";
  const isPlanned = currentTarget?.status === "planned";
  const isMediaPipe = currentTarget?.id === "mediapipe";
  const isLocalRecognition = currentTarget?.id === "local-recognition";

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
    refreshState();
  }, [selectedTarget]);

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
        if (!liveDetection?.embedding) {
          setError("No face embedding. Please ensure your face is visible in the camera.");
          setBusyCommand("");
          return;
        }
        const result: EnrollResponse = await enroll(personName, liveDetection.embedding);
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
      setError(err instanceof Error ? err.message : "Command failed.");
    } finally {
      setBusyCommand("");
    }
  }

  return (
    <section className="lab-layout">
      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Labs</p>
            <h3>Vision Lab</h3>
          </div>
          <span className="panel-tag">{OPERATIONS.find((item) => item.id === selectedOperation)?.label}{isPlanned ? " Planned" : ""}</span>
        </div>

        <div className="selector-grid">
          <label>Task<select value={selectedOperation} onChange={(event: ChangeEvent<HTMLSelectElement>) => setSelectedOperation(event.target.value as OperationId)}>{OPERATIONS.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}</select></label>
          <label>Engine / Provider<select value={currentTarget?.id ?? ""} onChange={(event: ChangeEvent<HTMLSelectElement>) => setSelectedTarget(event.target.value)}>{filteredTargets.map((target) => <option key={target.id} value={target.id}>{target.label}</option>)}</select></label>
        </div>

        {error ? <p className="error-banner">{error}</p> : null}
        {success ? <p className="success-banner">{success}</p> : null}
      </section>

      {!isPlanned && isRecognize && isLocalRecognition ? (
        <section className="panel">
          <div className="panel-header">
            <div><p className="eyebrow">Local Recognition</p><h3>Enrollment & Identification</h3></div>
          </div>
          
          <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
            <button type="button" onClick={() => { setLocalTab("enroll"); setIdentifyResult(null); }} style={{ padding: "0.5rem 1rem", backgroundColor: localTab === "enroll" ? "#3b82f6" : "#e5e7eb", color: localTab === "enroll" ? "white" : "#374151", border: "none", borderRadius: "4px", cursor: "pointer" }}>Enroll</button>
            <button type="button" onClick={() => { setLocalTab("identify"); setIdentifyResult(null); }} style={{ padding: "0.5rem 1rem", backgroundColor: localTab === "identify" ? "#3b82f6" : "#e5e7eb", color: localTab === "identify" ? "white" : "#374151", border: "none", borderRadius: "4px", cursor: "pointer" }}>Identify</button>
          </div>

          {localTab === "enroll" ? (
            <>
              <p className="helper-copy">Enter your name, position your face in the camera, then click Enroll.</p>
              <label style={{ marginBottom: "0.5rem", display: "block" }}>Your name<input value={personName} onChange={(event: ChangeEvent<HTMLInputElement>) => setPersonName(event.target.value)} placeholder="Enter your name" style={{ width: "100%", padding: "0.5rem", marginTop: "0.25rem" }} /></label>
              <CameraPanel onDetectionChange={setLiveDetection} />
              <div style={{ marginTop: "0.5rem", fontSize: "0.875rem" }}>
                {liveDetection?.hasFace ? <span style={{ color: "#22c55e" }}>Face detected</span> : <span style={{ color: "#6b7280" }}>No face detected</span>}
                {liveDetection?.embedding && <span style={{ marginLeft: "1rem" }}>Embedding ready</span>}
              </div>
              <button type="button" onClick={() => handleCommand("enroll")} disabled={!personName || !liveDetection?.embedding || busyCommand === "enroll"} style={{ marginTop: "1rem", width: "100%", padding: "0.75rem", backgroundColor: (!personName || !liveDetection?.embedding) ? "#9ca3af" : "#3b82f6", color: "white", border: "none", borderRadius: "4px", fontSize: "1rem", fontWeight: "bold" }}>{busyCommand === "enroll" ? "Enrolling..." : "Enroll"}</button>
            </>
          ) : (
            <>
              <p className="helper-copy">Live camera with auto-recognition. Your name will appear when recognized.</p>
              <CameraPanel 
                onDetectionChange={(det) => {
                  setLiveDetection(det);
                  const embKey = det?.embedding ? det.embedding.slice(0, 4).join(",") : "";
                  if (det?.hasFace && det.embedding && !isIdentifying && embKey !== lastIdentifiedFaceRef.current) {
                    const emb = det.embedding;
                    lastIdentifiedFaceRef.current = embKey;
                    setIdentifyResult(null);
                    setTimeout(async () => {
                      setIsIdentifying(true);
                      try {
                        const result = await recognize(emb);
                        if (result.matched) setIdentifyResult({ name: result.name!, similarity: result.similarity });
                        else setIdentifyResult(null);
                      } catch (e) { setIdentifyResult(null); }
                      finally {
                        setIsIdentifying(false);
                        setTimeout(() => { lastIdentifiedFaceRef.current = ""; }, 3000);
                      }
                    }, 1000);
                  }
                }}
                recognizedName={identifyResult?.name}
                isRecognizing={isIdentifying}
              />
              <div style={{ marginTop: "1rem", fontSize: "0.875rem" }}>
                {liveDetection?.hasFace ? <span style={{ color: "#22c55e" }}>Face detected</span> : <span style={{ color: "#6b7280" }}>No face detected</span>}
                {isIdentifying && <span style={{ color: "#3b82f6", marginLeft: "1rem" }}>Recognizing...</span>}
              </div>
              {identifyResult && (
                <div style={{ marginTop: "1rem", padding: "1rem", borderRadius: "8px", backgroundColor: "#dcfce7", border: "2px solid #22c55e" }}>
                  <div style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#166534" }}>{identifyResult.name}</div>
                  <div style={{ fontSize: "0.875rem", color: "#15803d" }}>Confidence: {(identifyResult.similarity * 100).toFixed(1)}%</div>
                </div>
              )}
            </>
          )}
        </section>
      ) : null}

      <section className="panel">
        <div className="panel-header"><div><p className="eyebrow">Run</p><h3>Commands</h3></div></div>
        {isLocalRecognition ? (
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button type="button" onClick={() => handleCommand("enroll")} disabled={busyCommand === "enroll"} style={{ padding: "0.75rem 1rem", backgroundColor: "#3b82f6", color: "white", border: "none", borderRadius: "4px" }}>Enroll</button>
          </div>
        ) : <p style={{ color: "#6b7280" }}>Select a target to see commands</p>}
      </section>
    </section>
  );
}