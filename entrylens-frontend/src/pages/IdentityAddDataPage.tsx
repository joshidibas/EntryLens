import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import CameraPanel from "../components/CameraPanel";
import {
  addEmbeddingToIdentity,
  getIdentity,
  getIdentitySampleImageUrl,
  listEmbeddingsForIdentity,
  promoteEmbedding,
  setProfileSample,
  type IdentityDetail,
  type IdentitySampleSummary,
} from "../api/identities";
import { useRecognitionSession } from "../hooks/useRecognitionSession";

export default function IdentityAddDataPage() {
  const navigate = useNavigate();
  const { identityId } = useParams();
  const [identityDetail, setIdentityDetail] = useState<IdentityDetail | null>(null);
  const [samples, setSamples] = useState<IdentitySampleSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [addBusy, setAddBusy] = useState(false);
  const [promoteBusy, setPromoteBusy] = useState(false);
  const {
    liveDetection,
    identifyResult,
    candidateMatches,
    isIdentifying,
    handleDetectionChange,
    runRecognition,
  } = useRecognitionSession({
    includeCandidates: true,
    onError: (message) => setError(message),
  });

  const profileSample = useMemo(
    () =>
      samples.find((sample) => sample.id === identityDetail?.profile_sample_id) ??
      samples.find((sample) => sample.is_profile_source) ??
      samples.find((sample) => sample.is_reference) ??
      samples[0] ??
      null,
    [identityDetail, samples],
  );

  const profileImageUrl = useMemo(
    () => getIdentitySampleImageUrl(profileSample?.image_path),
    [profileSample],
  );

  const recognitionState = useMemo(() => {
    if (!identifyResult) {
      return {
        tone: "idle",
        title: "Recognition test pending",
        description: "Keep a face in frame to test whether the live camera feed resolves to this identity.",
      };
    }

    if (identifyResult.matched && identifyResult.identityId === identityId) {
      return {
        tone: "match",
        title: "Camera feed matches this identity",
        description: `${identifyResult.name ?? "This identity"} matched with ${(identifyResult.similarity * 100).toFixed(1)}% confidence.`,
      };
    }

    if (identifyResult.matched && identifyResult.identityId !== identityId) {
      return {
        tone: "warning",
        title: "Camera feed matched a different identity",
        description: `${identifyResult.name ?? "Another identity"} matched with ${(identifyResult.similarity * 100).toFixed(1)}% confidence. Review before adding this as a new sample.`,
      };
    }

    return {
      tone: "unknown",
      title: "Camera feed is currently unknown",
      description: "No stored identity matched this face. You can still add the current frame as another reference sample for this person if that is intentional.",
    };
  }, [identifyResult, identityId]);

  useEffect(() => {
    let active = true;

    async function loadPage() {
      if (!identityId) {
        setError("Identity id is missing.");
        setLoading(false);
        return;
      }

      setLoading(true);
      setError("");
      try {
        const [detail, sampleItems] = await Promise.all([
          getIdentity(identityId),
          listEmbeddingsForIdentity(identityId),
        ]);
        if (!active) {
          return;
        }
        setIdentityDetail(detail);
        setSamples(sampleItems);
      } catch (err) {
        if (!active) {
          return;
        }
        setError(err instanceof Error ? err.message : "Could not load the add-data page.");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadPage();
    return () => {
      active = false;
    };
  }, [identityId]);

  async function refreshIdentityState(targetIdentityId: string) {
    const [detail, sampleItems] = await Promise.all([
      getIdentity(targetIdentityId),
      listEmbeddingsForIdentity(targetIdentityId),
    ]);
    setIdentityDetail(detail);
    setSamples(sampleItems);
  }

  async function handleAddSample() {
    if (!identityId || !liveDetection?.embedding) {
      setError("Keep a face visible in the camera before adding a sample.");
      return;
    }

    setAddBusy(true);
    setError("");
    setSuccess("");
    try {
      const result = await addEmbeddingToIdentity(
        identityId,
        liveDetection.embedding,
        identifyResult?.similarity,
        liveDetection.imageDataUrl,
      );
      await refreshIdentityState(identityId);
      setSuccess(result.message || "Added a new live-camera sample.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add the current live sample.");
    } finally {
      setAddBusy(false);
    }
  }

  async function handleAddAndPromote(profileMode: "reference" | "profile") {
    if (!identityId || !liveDetection?.embedding) {
      setError("Keep a face visible in the camera before adding a sample.");
      return;
    }

    setPromoteBusy(true);
    setError("");
    setSuccess("");
    try {
      await addEmbeddingToIdentity(
        identityId,
        liveDetection.embedding,
        identifyResult?.similarity,
        liveDetection.imageDataUrl,
      );
      const updatedSamples = await listEmbeddingsForIdentity(identityId);
      const newestSample = updatedSamples[0];
      if (!newestSample) {
        throw new Error("The new sample was stored, but it could not be loaded back.");
      }

      if (profileMode === "reference") {
        await promoteEmbedding(identityId, newestSample.id);
      } else {
        await setProfileSample(identityId, newestSample.id);
      }

      await refreshIdentityState(identityId);
      setSuccess(
        profileMode === "reference"
          ? "Added the live sample and promoted it as the preferred reference."
          : "Added the live sample and set it as the profile source.",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add and promote the current live sample.");
    } finally {
      setPromoteBusy(false);
    }
  }

  if (loading) {
    return (
      <section className="people-layout">
        <section className="panel">
          <p>Loading identity add-data workspace...</p>
        </section>
      </section>
    );
  }

  if (!identityDetail || !identityId) {
    return (
      <section className="people-layout">
        <section className="panel">
          <p className="error-banner">{error || "This identity could not be found."}</p>
          <div className="lab-actions">
            <button type="button" onClick={() => navigate("/identities")}>
              Back To Directory
            </button>
          </div>
        </section>
      </section>
    );
  }

  return (
    <section className="people-layout">
      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Identity Data</p>
            <h3>Add Data From Live Camera</h3>
          </div>
          <div className="table-action-group">
            <button type="button" className="ghost-button" onClick={() => navigate(`/identities/${identityId}`)}>
              Back To Samples
            </button>
            <button type="button" className="ghost-button" onClick={() => navigate("/identities")}>
              Directory
            </button>
          </div>
        </div>

        {error ? <p className="error-banner">{error}</p> : null}
        {success ? <p className="success-banner">{success}</p> : null}

        <section className="identity-add-data-shell">
          <section className="identity-add-data-sidebar">
            <div className="people-detail-header">
              <div>
                <strong>{identityDetail.display_name}</strong>
                <span>{identityDetail.identity_type}</span>
              </div>
              <span className="panel-tag">{identityDetail.sample_count} samples</span>
            </div>

            <section className="identity-profile-card">
              <div>
                <p className="eyebrow">Target Identity</p>
                <h4>Current Main Picture</h4>
                <p className="helper-copy">
                  Use this preview to compare the live face against the person you are trying to enrich.
                </p>
              </div>
              {profileImageUrl ? (
                <img
                  src={profileImageUrl}
                  alt={`${identityDetail.display_name} current profile`}
                  className="identity-profile-image"
                />
              ) : (
                <div className="identity-profile-placeholder">No profile image stored yet.</div>
              )}
            </section>

            <section className={`recognition-result-card ${recognitionState.tone}`}>
              <p className="eyebrow">Recognition Check</p>
              <h4>{recognitionState.title}</h4>
              <p>{recognitionState.description}</p>
            </section>

            {candidateMatches.length > 0 ? (
              <section className="candidate-list-card">
                <p className="eyebrow">Closest Matches</p>
                <div className="candidate-list">
                  {candidateMatches.slice(0, 3).map((candidate) => (
                    <article key={candidate.identity_id} className="candidate-item">
                      <strong>{candidate.display_name}</strong>
                      <span>
                        {candidate.identity_type} · {(candidate.similarity * 100).toFixed(1)}% · {candidate.sample_count} samples
                      </span>
                    </article>
                  ))}
                </div>
              </section>
            ) : null}

            <section className="identity-add-actions">
              <button
                type="button"
                onClick={() => void handleAddSample()}
                disabled={!liveDetection?.embedding || addBusy || promoteBusy}
              >
                {addBusy ? "Adding Sample..." : "Add Live Sample"}
              </button>
              <button
                type="button"
                className="ghost-button"
                onClick={() => void handleAddAndPromote("reference")}
                disabled={!liveDetection?.embedding || addBusy || promoteBusy}
              >
                {promoteBusy ? "Working..." : "Add And Set As Reference"}
              </button>
              <button
                type="button"
                className="ghost-button"
                onClick={() => void handleAddAndPromote("profile")}
                disabled={!liveDetection?.embedding || addBusy || promoteBusy}
              >
                {promoteBusy ? "Working..." : "Add And Set As Profile"}
              </button>
            </section>
          </section>

          <section className="identity-add-data-main">
            <CameraPanel
              onDetectionChange={handleDetectionChange}
              onRecognize={runRecognition}
              recognizedName={identifyResult?.matched ? identifyResult.name ?? undefined : undefined}
              isRecognizing={isIdentifying}
            />

            <section className="identity-camera-summary">
              <div className="status-card">
                <strong>Face In Frame</strong>
                <span>{liveDetection?.hasFace ? `${liveDetection.detectedFaces} detected` : "No face detected"}</span>
              </div>
              <div className="status-card">
                <strong>Embedding</strong>
                <span>{liveDetection?.embedding ? "Ready to store" : "Waiting for a stable face"}</span>
              </div>
              <div className="status-card">
                <strong>Sample Image</strong>
                <span>{liveDetection?.imageDataUrl ? "Live frame captured" : "No frame captured yet"}</span>
              </div>
            </section>

            <section className="identity-live-help panel">
              <div className="panel-header">
                <div>
                  <p className="eyebrow">Workflow</p>
                  <h3>How To Use This Page</h3>
                </div>
              </div>
              <div className="progress-list">
                <div className="progress-item">
                  <strong>1. Compare the target picture to the live camera.</strong>
                  <span>Make sure the correct person is in frame before storing another sample.</span>
                </div>
                <div className="progress-item">
                  <strong>2. Watch the recognition result.</strong>
                  <span>If the live camera resolves to another identity, that is a signal to stop and review before adding more data.</span>
                </div>
                <div className="progress-item">
                  <strong>3. Add a new live sample.</strong>
                  <span>Use the action buttons to append a sample, or immediately set the new sample as reference or profile.</span>
                </div>
              </div>
            </section>
          </section>
        </section>
      </section>
    </section>
  );
}
