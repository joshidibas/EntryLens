import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  getDetectionLog,
  getDetectionLogImageUrl,
  listDetectionLogs,
  mergeDetectionLogIdentity,
  promoteDetectionLogSample,
  updateDetectionLog,
  type DetectionLogDetail,
  type DetectionLogSummary,
} from "../api/detectionLogs";
import { listIdentities, type IdentitySummary } from "../api/identities";

const IDENTITY_TYPE_OPTIONS = ["unknown", "visitor", "staff", "student", "contractor"];
const IDENTITY_STATUS_OPTIONS = ["pending_review", "active", "archived"];
const REVIEW_STATUS_OPTIONS = ["pending", "auto-tagged", "resolved", "ignored"];

export default function DetectionLogsPage() {
  const navigate = useNavigate();
  const { detectionLogId } = useParams();
  const [logs, setLogs] = useState<DetectionLogSummary[]>([]);
  const [identities, setIdentities] = useState<IdentitySummary[]>([]);
  const [logDetail, setLogDetail] = useState<DetectionLogDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [busyAction, setBusyAction] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [identityType, setIdentityType] = useState("unknown");
  const [identityStatus, setIdentityStatus] = useState("pending_review");
  const [reviewStatus, setReviewStatus] = useState("pending");
  const [reviewNotes, setReviewNotes] = useState("");
  const [mergeTargetId, setMergeTargetId] = useState("");
  const [promoteTargetId, setPromoteTargetId] = useState("");

  const selectedLog = useMemo(
    () => logs.find((item) => item.id === detectionLogId) ?? null,
    [logs, detectionLogId],
  );

  const imageUrl = useMemo(
    () => getDetectionLogImageUrl(logDetail?.image_path),
    [logDetail?.image_path],
  );

  useEffect(() => {
    let active = true;

    async function loadPage() {
      setLoading(true);
      setError("");
      try {
        const [logItems, identityItems] = await Promise.all([listDetectionLogs(), listIdentities()]);
        if (!active) {
          return;
        }
        setLogs(logItems);
        setIdentities(identityItems);
      } catch (err) {
        if (!active) {
          return;
        }
        setError(err instanceof Error ? err.message : "Could not load detection logs.");
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
  }, []);

  useEffect(() => {
    let active = true;

    async function loadDetail() {
      if (!detectionLogId) {
        setLogDetail(null);
        return;
      }

      setDetailLoading(true);
      setError("");
      try {
        const detail = await getDetectionLog(detectionLogId);
        if (!active) {
          return;
        }
        setLogDetail(detail);
        setDisplayName(detail.current_identity?.display_name ?? "");
        setIdentityType(detail.current_identity?.identity_type ?? "unknown");
        setIdentityStatus(detail.current_identity?.status ?? "pending_review");
        setReviewStatus(detail.review_status);
        setReviewNotes(detail.review_notes ?? "");
        setMergeTargetId(detail.auto_identity?.id ?? "");
        setPromoteTargetId(detail.current_identity?.id ?? "");
      } catch (err) {
        if (!active) {
          return;
        }
        setError(err instanceof Error ? err.message : "Could not load this detection log.");
      } finally {
        if (active) {
          setDetailLoading(false);
        }
      }
    }

    void loadDetail();
    return () => {
      active = false;
    };
  }, [detectionLogId]);

  async function refreshLogs() {
    const items = await listDetectionLogs();
    setLogs(items);
  }

  async function refreshDetail(targetLogId: string) {
    const detail = await getDetectionLog(targetLogId);
    setLogDetail(detail);
    setDisplayName(detail.current_identity?.display_name ?? "");
    setIdentityType(detail.current_identity?.identity_type ?? "unknown");
    setIdentityStatus(detail.current_identity?.status ?? "pending_review");
    setReviewStatus(detail.review_status);
    setReviewNotes(detail.review_notes ?? "");
    setMergeTargetId(detail.auto_identity?.id ?? "");
    setPromoteTargetId(detail.current_identity?.id ?? "");
  }

  async function refreshIdentities() {
    const items = await listIdentities();
    setIdentities(items);
  }

  async function handleSaveReviewIdentity() {
    if (!detectionLogId || !displayName.trim()) {
      setError("Enter a name before saving this reviewed identity.");
      return;
    }

    setBusyAction("save");
    setError("");
    setSuccess("");
    try {
      await updateDetectionLog(detectionLogId, {
        display_name: displayName.trim(),
        identity_type: identityType,
        status: identityStatus,
        review_status: reviewStatus,
        review_notes: reviewNotes.trim() || null,
      });
      await Promise.all([refreshLogs(), refreshDetail(detectionLogId), refreshIdentities()]);
      setSuccess("Updated the detection review identity.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save this reviewed identity.");
    } finally {
      setBusyAction("");
    }
  }

  async function handleMergeToExisting() {
    if (!detectionLogId || !mergeTargetId) {
      setError("Choose an existing identity to merge into.");
      return;
    }

    setBusyAction("merge");
    setError("");
    setSuccess("");
    try {
      const result = await mergeDetectionLogIdentity(detectionLogId, mergeTargetId);
      await Promise.all([refreshLogs(), refreshDetail(detectionLogId), refreshIdentities()]);
      setPromoteTargetId(mergeTargetId);
      setSuccess(result.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not merge this review identity.");
    } finally {
      setBusyAction("");
    }
  }

  async function handlePromoteSample(mode: "sample" | "reference" | "profile") {
    if (!detectionLogId) {
      return;
    }

    setBusyAction(mode);
    setError("");
    setSuccess("");
    try {
      const result = await promoteDetectionLogSample(detectionLogId, {
        target_identity_id: promoteTargetId || logDetail?.current_identity?.id || null,
        set_as_reference: mode === "reference",
        set_as_profile: mode === "profile",
      });
      await Promise.all([refreshLogs(), refreshDetail(detectionLogId), refreshIdentities()]);
      setSuccess(result.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not promote this detection frame.");
    } finally {
      setBusyAction("");
    }
  }

  if (detectionLogId) {
    return (
      <section className="people-layout">
        <section className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Detection Log</p>
              <h3>Review Detection</h3>
            </div>
            <div className="table-action-group">
              <button type="button" className="ghost-button" onClick={() => navigate("/detection-logs")}>
                Back To Logs
              </button>
              {logDetail?.current_identity?.id ? (
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => navigate(`/identities/${logDetail.current_identity?.id}`)}
                >
                  Open Identity
                </button>
              ) : null}
            </div>
          </div>

          {error ? <p className="error-banner">{error}</p> : null}
          {success ? <p className="success-banner">{success}</p> : null}

          {detailLoading ? (
            <p>Loading detection log...</p>
          ) : logDetail ? (
            <section className="identity-add-data-shell detection-log-shell">
              <section className="identity-add-data-sidebar">
                <div className="people-detail-header">
                  <div>
                    <strong>{logDetail.current_identity?.display_name ?? "Unknown review identity"}</strong>
                    <span>{logDetail.current_identity?.identity_type ?? "unknown"}</span>
                  </div>
                  <span className="panel-tag">{logDetail.review_status}</span>
                </div>

                <section className="identity-profile-card">
                  <div>
                    <p className="eyebrow">Captured Frame</p>
                    <h4>Detection Snapshot</h4>
                    <p className="helper-copy">
                      Review the stored live-feed frame, then decide whether to keep this unknown identity, merge it, or promote the frame into embeddings.
                    </p>
                  </div>
                  {imageUrl ? (
                    <img src={imageUrl} alt="Detection log frame" className="identity-profile-image" />
                  ) : (
                    <div className="identity-profile-placeholder">No stored frame image for this log.</div>
                  )}
                </section>

                <section className="recognition-result-card warning">
                  <p className="eyebrow">Auto Match</p>
                  <h4>
                    {logDetail.auto_tagged
                      ? `Tagged as ${logDetail.auto_identity?.display_name ?? logDetail.auto_display_name ?? "known identity"}`
                      : logDetail.auto_identity?.display_name || logDetail.auto_display_name
                        ? `Closest suggestion: ${logDetail.auto_identity?.display_name ?? logDetail.auto_display_name}`
                        : "No confident identity match"}
                  </h4>
                  <p>
                    {logDetail.auto_similarity != null
                      ? `Similarity ${(logDetail.auto_similarity * 100).toFixed(1)}%. Only scores at 95% or above are auto-tagged.`
                      : "This frame did not include an auto-match confidence score."}
                  </p>
                </section>

                <section className="identity-camera-summary">
                  <div className="status-card">
                    <strong>Detected At</strong>
                    <span>{logDetail.detected_at ? new Date(logDetail.detected_at).toLocaleString() : "Unknown time"}</span>
                  </div>
                  <div className="status-card">
                    <strong>Camera</strong>
                    <span>{logDetail.camera_id || "Default live feed"}</span>
                  </div>
                  <div className="status-card">
                    <strong>Promoted Sample</strong>
                    <span>{logDetail.promoted_embedding_id ?? "Not promoted yet"}</span>
                  </div>
                </section>
              </section>

              <section className="identity-add-data-main">
                <section className="panel detection-review-panel">
                  <div className="panel-header">
                    <div>
                      <p className="eyebrow">Option A</p>
                      <h3>Name Or Update This Review Identity</h3>
                    </div>
                  </div>
                  <div className="identity-edit-grid">
                    <label>
                      Display Name
                      <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
                    </label>
                    <label>
                      Identity Type
                      <select value={identityType} onChange={(event) => setIdentityType(event.target.value)}>
                        {IDENTITY_TYPE_OPTIONS.map((option) => (
                          <option key={option} value={option}>
                            {option}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Status
                      <select value={identityStatus} onChange={(event) => setIdentityStatus(event.target.value)}>
                        {IDENTITY_STATUS_OPTIONS.map((option) => (
                          <option key={option} value={option}>
                            {option}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Review Status
                      <select value={reviewStatus} onChange={(event) => setReviewStatus(event.target.value)}>
                        {REVIEW_STATUS_OPTIONS.map((option) => (
                          <option key={option} value={option}>
                            {option}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Review Notes
                      <textarea value={reviewNotes} onChange={(event) => setReviewNotes(event.target.value)} rows={4} />
                    </label>
                  </div>
                  <div className="lab-actions">
                    <button type="button" onClick={() => void handleSaveReviewIdentity()} disabled={busyAction !== ""}>
                      {busyAction === "save" ? "Saving..." : "Save Review Identity"}
                    </button>
                  </div>
                </section>

                <section className="panel detection-review-panel">
                  <div className="panel-header">
                    <div>
                      <p className="eyebrow">Option B</p>
                      <h3>Merge Into Existing Identity</h3>
                    </div>
                  </div>
                  <label>
                    Existing Identity
                    <select value={mergeTargetId} onChange={(event) => setMergeTargetId(event.target.value)}>
                      <option value="">Select identity</option>
                      {identities
                        .filter((identity) => identity.id !== logDetail.current_identity?.id)
                        .map((identity) => (
                          <option key={identity.id} value={identity.id}>
                            {identity.display_name} ({identity.identity_type})
                          </option>
                        ))}
                    </select>
                  </label>
                  <div className="lab-actions">
                    <button
                      type="button"
                      className="ghost-button"
                      onClick={() => void handleMergeToExisting()}
                      disabled={!mergeTargetId || busyAction !== ""}
                    >
                      {busyAction === "merge" ? "Merging..." : "Merge And Remove Placeholder"}
                    </button>
                  </div>
                </section>

                <section className="panel detection-review-panel">
                  <div className="panel-header">
                    <div>
                      <p className="eyebrow">Samples</p>
                      <h3>Promote Captured Frame</h3>
                    </div>
                  </div>
                  <label>
                    Save To Identity
                    <select value={promoteTargetId} onChange={(event) => setPromoteTargetId(event.target.value)}>
                      <option value="">Use current review identity</option>
                      {identities.map((identity) => (
                        <option key={identity.id} value={identity.id}>
                          {identity.display_name} ({identity.embedding_count} samples)
                        </option>
                      ))}
                    </select>
                  </label>
                  <div className="lab-actions">
                    <button type="button" onClick={() => void handlePromoteSample("sample")} disabled={busyAction !== ""}>
                      {busyAction === "sample" ? "Promoting..." : "Promote As Sample"}
                    </button>
                    <button
                      type="button"
                      className="ghost-button"
                      onClick={() => void handlePromoteSample("reference")}
                      disabled={busyAction !== ""}
                    >
                      {busyAction === "reference" ? "Promoting..." : "Promote As Reference"}
                    </button>
                    <button
                      type="button"
                      className="ghost-button"
                      onClick={() => void handlePromoteSample("profile")}
                      disabled={busyAction !== ""}
                    >
                      {busyAction === "profile" ? "Promoting..." : "Promote As Profile"}
                    </button>
                  </div>
                </section>
              </section>
            </section>
          ) : (
            <p>This detection log could not be found.</p>
          )}
        </section>
      </section>
    );
  }

  return (
    <section className="people-layout">
      <section className="panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Detection Logs</p>
            <h3>Live Feed Review Queue</h3>
          </div>
          <span className="panel-tag">{logs.length} logs</span>
        </div>

        {error ? <p className="error-banner">{error}</p> : null}
        {success ? <p className="success-banner">{success}</p> : null}

        <div className="table-wrap">
          {loading ? (
            <p>Loading detection logs...</p>
          ) : logs.length > 0 ? (
            <table>
              <thead>
                <tr>
                  <th>Detected</th>
                  <th>Current Identity</th>
                  <th>Auto Suggestion</th>
                  <th>Confidence</th>
                  <th>Status</th>
                  <th>Sample</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td>{log.detected_at ? new Date(log.detected_at).toLocaleString() : "Unknown time"}</td>
                    <td>{log.current_identity?.display_name ?? "Unknown"}</td>
                    <td>{log.auto_identity?.display_name ?? "No suggestion"}</td>
                    <td>{log.auto_similarity != null ? `${(log.auto_similarity * 100).toFixed(1)}%` : "Not scored"}</td>
                    <td>{log.review_status}</td>
                    <td>{log.promoted_embedding_id ? "Promoted" : "Pending"}</td>
                    <td>
                      <button type="button" className="table-action-button" onClick={() => navigate(`/detection-logs/${log.id}`)}>
                        Review
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No detection logs yet. Live feed activity will appear here.</p>
          )}
        </div>

        {selectedLog ? <p className="helper-copy">Selected log: {selectedLog.id}</p> : null}
      </section>
    </section>
  );
}
