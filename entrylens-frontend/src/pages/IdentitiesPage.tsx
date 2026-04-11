import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  createIdentity,
  deleteEmbedding,
  deleteIdentity,
  getIdentity,
  getIdentitySampleImageUrl,
  listEmbeddingsForIdentity,
  listIdentities,
  promoteEmbedding,
  setProfileSample,
  updateIdentity,
  type IdentityDetail,
  type IdentitySampleSummary,
  type IdentitySummary,
} from "../api/identities";

const IDENTITY_TYPE_OPTIONS = ["visitor", "staff", "student", "contractor"];
const IDENTITY_STATUS_OPTIONS = ["active", "archived"];

export default function IdentitiesPage() {
  const navigate = useNavigate();
  const { identityId } = useParams();
  const [identities, setIdentities] = useState<IdentitySummary[]>([]);
  const [identityDetail, setIdentityDetail] = useState<IdentityDetail | null>(null);
  const [embeddings, setEmbeddings] = useState<IdentitySampleSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [actionBusyId, setActionBusyId] = useState("");
  const [createName, setCreateName] = useState("");
  const [createType, setCreateType] = useState("visitor");
  const [createStatus, setCreateStatus] = useState("active");
  const [createNotes, setCreateNotes] = useState("");
  const [createBusy, setCreateBusy] = useState(false);
  const [editName, setEditName] = useState("");
  const [editType, setEditType] = useState("visitor");
  const [editStatus, setEditStatus] = useState("active");
  const [editNotes, setEditNotes] = useState("");
  const [editBusy, setEditBusy] = useState(false);
  const [deleteBusy, setDeleteBusy] = useState(false);

  const selectedIdentity = useMemo(
    () => identities.find((identity) => identity.id === identityId) ?? null,
    [identities, identityId],
  );

  const profileSample = useMemo(() => {
    if (!identityDetail) {
      return null;
    }

    return (
      embeddings.find((embedding) => embedding.id === identityDetail.profile_sample_id) ??
      embeddings.find((embedding) => embedding.is_profile_source) ??
      embeddings.find((embedding) => embedding.is_reference) ??
      embeddings[0] ??
      null
    );
  }, [embeddings, identityDetail]);

  const profileImageUrl = useMemo(
    () => getIdentitySampleImageUrl(profileSample?.image_path),
    [profileSample],
  );

  useEffect(() => {
    let active = true;

    async function loadIdentities() {
      setLoading(true);
      setError("");
      try {
        const items = await listIdentities();
        if (!active) {
          return;
        }
        setIdentities(items);
      } catch (err) {
        if (!active) {
          return;
        }
        setError(err instanceof Error ? err.message : "Could not load identities.");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadIdentities();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function loadDetail() {
      if (!identityId) {
        setIdentityDetail(null);
        setEmbeddings([]);
        return;
      }

      setDetailLoading(true);
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
        setEditName(detail.display_name);
        setEditType(detail.identity_type);
        setEditStatus(detail.status);
        setEditNotes(detail.notes ?? "");
        setEmbeddings(sampleItems);
      } catch (err) {
        if (!active) {
          return;
        }
        setError(err instanceof Error ? err.message : "Could not load this identity.");
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
  }, [identityId]);

  async function refreshIdentities() {
    const items = await listIdentities();
    setIdentities(items);
  }

  async function refreshDetail(targetIdentityId: string) {
    const [detail, sampleItems] = await Promise.all([
      getIdentity(targetIdentityId),
      listEmbeddingsForIdentity(targetIdentityId),
    ]);
    setIdentityDetail(detail);
    setEditName(detail.display_name);
    setEditType(detail.identity_type);
    setEditStatus(detail.status);
    setEditNotes(detail.notes ?? "");
    setEmbeddings(sampleItems);
  }

  async function handleCreateIdentity() {
    if (!createName.trim()) {
      setError("Enter an identity name before creating it.");
      return;
    }

    setCreateBusy(true);
    setError("");
    setSuccess("");
    try {
      const created = await createIdentity(createName.trim(), createType, createStatus, createNotes.trim() || null);
      await refreshIdentities();
      setCreateName("");
      setCreateType("visitor");
      setCreateStatus("active");
      setCreateNotes("");
      setSuccess(`Created identity ${created.display_name}.`);
      navigate(`/identities/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create identity.");
    } finally {
      setCreateBusy(false);
    }
  }

  async function handleUpdateIdentity() {
    if (!identityId || !editName.trim()) {
      setError("Identity name is required.");
      return;
    }

    setEditBusy(true);
    setError("");
    setSuccess("");
    try {
      const updated = await updateIdentity(
        identityId,
        editName.trim(),
        editType,
        editStatus,
        editNotes.trim() || null,
      );
      await refreshIdentities();
      setIdentityDetail(updated);
      setSuccess(`Updated identity ${updated.display_name}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update identity.");
    } finally {
      setEditBusy(false);
    }
  }

  async function handleDeleteIdentity() {
    if (!identityId || !identityDetail) {
      return;
    }

    const confirmed = window.confirm(`Delete identity "${identityDetail.display_name}" and all of its samples?`);
    if (!confirmed) {
      return;
    }

    setDeleteBusy(true);
    setError("");
    setSuccess("");
    try {
      await deleteIdentity(identityId);
      await refreshIdentities();
      setSuccess(`Deleted identity ${identityDetail.display_name}.`);
      navigate("/identities");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete identity.");
    } finally {
      setDeleteBusy(false);
    }
  }

  async function handleDeleteSample(embeddingId: string) {
    if (!identityId) {
      return;
    }

    setActionBusyId(embeddingId);
    setError("");
    setSuccess("");
    try {
      await deleteEmbedding(identityId, embeddingId);
      await refreshIdentities();
      await refreshDetail(identityId);
      setSuccess("Deleted sample.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete this sample.");
    } finally {
      setActionBusyId("");
    }
  }

  async function handlePromoteSample(embeddingId: string) {
    if (!identityId) {
      return;
    }

    setActionBusyId(embeddingId);
    setError("");
    setSuccess("");
    try {
      await promoteEmbedding(identityId, embeddingId);
      await refreshDetail(identityId);
      setSuccess("Promoted sample as preferred reference.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not promote this sample.");
    } finally {
      setActionBusyId("");
    }
  }

  async function handleSetProfileSample(embeddingId: string) {
    if (!identityId) {
      return;
    }

    setActionBusyId(embeddingId);
    setError("");
    setSuccess("");
    try {
      await setProfileSample(identityId, embeddingId);
      await refreshDetail(identityId);
      setSuccess("Set sample as profile source.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not set this sample as profile source.");
    } finally {
      setActionBusyId("");
    }
  }

  if (identityId) {
    return (
      <section className="people-layout">
        <section className="panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Identity</p>
              <h3>Identity Details</h3>
            </div>
            <button type="button" className="ghost-button" onClick={() => navigate("/identities")}>
              Back To Directory
            </button>
          </div>

          {error ? <p className="error-banner">{error}</p> : null}
          {success ? <p className="success-banner">{success}</p> : null}

          {detailLoading ? (
            <p>Loading identity details...</p>
          ) : identityDetail ? (
            <>
              <div className="people-detail-header">
                <div>
                  <strong>{identityDetail.display_name}</strong>
                  <span>{identityDetail.identity_type}</span>
                </div>
                <span className="panel-tag">{identityDetail.sample_count} samples</span>
              </div>

              <div className="identity-edit-grid">
                <label>
                  Display Name
                  <input value={editName} onChange={(event) => setEditName(event.target.value)} />
                </label>
                <label>
                  Identity Type
                  <select value={editType} onChange={(event) => setEditType(event.target.value)}>
                    {IDENTITY_TYPE_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Status
                  <select value={editStatus} onChange={(event) => setEditStatus(event.target.value)}>
                    {IDENTITY_STATUS_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Notes
                  <textarea value={editNotes} onChange={(event) => setEditNotes(event.target.value)} rows={3} />
                </label>
              </div>

              <div className="lab-actions">
                <button type="button" onClick={() => void handleUpdateIdentity()} disabled={editBusy || deleteBusy}>
                  {editBusy ? "Saving..." : "Save Identity"}
                </button>
                <button type="button" className="ghost-button" onClick={() => navigate(`/identities/${identityId}/add-data`)}>
                  Add Data From Camera
                </button>
                <button type="button" className="ghost-button" onClick={() => void handleDeleteIdentity()} disabled={editBusy || deleteBusy}>
                  {deleteBusy ? "Deleting..." : "Delete Identity"}
                </button>
              </div>

              <div className="identity-profile-note">
                Profile source sample: {identityDetail.profile_sample_id ?? "No profile sample selected yet"}
              </div>

              <section className="identity-profile-card">
                <div>
                  <p className="eyebrow">Profile Preview</p>
                  <h4>Main Reference Picture</h4>
                  <p className="helper-copy">
                    The current profile image comes from the selected profile sample, then falls back to the preferred reference sample.
                  </p>
                </div>
                {profileImageUrl ? (
                  <img
                    src={profileImageUrl}
                    alt={`${identityDetail.display_name} profile sample`}
                    className="identity-profile-image"
                  />
                ) : (
                  <div className="identity-profile-placeholder">
                    No local sample image stored yet.
                  </div>
                )}
              </section>

              <div className="table-wrap">
                {embeddings.length > 0 ? (
                  <table>
                    <thead>
                      <tr>
                        <th>Sample</th>
                        <th>Preview</th>
                        <th>Kind</th>
                        <th>Source</th>
                        <th>Added On</th>
                        <th>Confidence</th>
                        <th>Reference</th>
                        <th>Profile</th>
                        <th>Sample ID</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {embeddings.map((embedding, index) => (
                        <tr key={embedding.id}>
                          <td>{embeddings.length - index}</td>
                          <td>
                            {getIdentitySampleImageUrl(embedding.image_path) ? (
                              <img
                                src={getIdentitySampleImageUrl(embedding.image_path) ?? undefined}
                                alt={`Sample ${embeddings.length - index}`}
                                className="identity-sample-thumb"
                              />
                            ) : (
                              <span className="identity-sample-thumb-placeholder">No image</span>
                            )}
                          </td>
                          <td>{embedding.sample_kind}</td>
                          <td>{embedding.capture_source ?? "manual"}</td>
                          <td>{embedding.created_at ? new Date(embedding.created_at).toLocaleString() : "Unknown time"}</td>
                          <td>{embedding.capture_confidence != null ? `${(embedding.capture_confidence * 100).toFixed(1)}%` : "Not recorded"}</td>
                          <td>{embedding.is_reference ? "Preferred" : "Standard"}</td>
                          <td>{embedding.is_profile_source ? "Profile" : "Standard"}</td>
                          <td className="sample-id">{embedding.id}</td>
                          <td>
                            <div className="table-action-group">
                              <button
                                type="button"
                                className="table-action-button"
                                onClick={() => void handlePromoteSample(embedding.id)}
                                disabled={actionBusyId !== "" || embedding.is_reference}
                              >
                                {embedding.is_reference ? "Preferred" : actionBusyId === embedding.id ? "Working..." : "Promote"}
                              </button>
                              <button
                                type="button"
                                className="table-action-button"
                                onClick={() => void handleSetProfileSample(embedding.id)}
                                disabled={actionBusyId !== "" || embedding.is_profile_source}
                              >
                                {embedding.is_profile_source ? "Profile" : actionBusyId === embedding.id ? "Working..." : "Set Profile"}
                              </button>
                              <button
                                type="button"
                                className="table-action-button table-action-danger"
                                onClick={() => void handleDeleteSample(embedding.id)}
                                disabled={actionBusyId !== ""}
                              >
                                {actionBusyId === embedding.id ? "Working..." : "Delete"}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p>No stored samples are available for this identity yet.</p>
                )}
              </div>
            </>
          ) : (
            <p>This identity could not be found.</p>
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
            <p className="eyebrow">Identity</p>
            <h3>Identity Directory</h3>
          </div>
          <span className="panel-tag">{identities.length} identities</span>
        </div>

        {error ? <p className="error-banner">{error}</p> : null}
        {success ? <p className="success-banner">{success}</p> : null}

        <div className="identity-edit-grid">
          <label>
            Display Name
            <input value={createName} onChange={(event) => setCreateName(event.target.value)} placeholder="Enter identity name" />
          </label>
          <label>
            Identity Type
            <select value={createType} onChange={(event) => setCreateType(event.target.value)}>
              {IDENTITY_TYPE_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <label>
            Status
            <select value={createStatus} onChange={(event) => setCreateStatus(event.target.value)}>
              {IDENTITY_STATUS_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <label>
            Notes
            <textarea
              value={createNotes}
              onChange={(event) => setCreateNotes(event.target.value)}
              placeholder="Optional admin notes"
              rows={3}
            />
          </label>
        </div>

        <div className="lab-actions">
          <button type="button" onClick={() => void handleCreateIdentity()} disabled={createBusy}>
            {createBusy ? "Creating..." : "Create Identity"}
          </button>
        </div>

        <div className="table-wrap">
          {loading ? (
            <p>Loading identities...</p>
          ) : identities.length > 0 ? (
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Created / Added On</th>
                  <th>Profile</th>
                  <th>Samples</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {identities.map((identity) => (
                  <tr key={identity.id}>
                    <td>{identity.display_name}</td>
                    <td>{identity.identity_type}</td>
                    <td>{identity.status}</td>
                    <td>{identity.created_at ? new Date(identity.created_at).toLocaleString() : "Unknown time"}</td>
                    <td>{identity.profile_sample_id ? "Profile sample set" : "Not set"}</td>
                    <td>{identity.embedding_count}</td>
                    <td>
                      <button
                        type="button"
                        className="table-action-button"
                        onClick={() => navigate(`/identities/${identity.id}`)}
                      >
                        View Samples
                      </button>
                      <button
                        type="button"
                        className="table-action-button"
                        onClick={() => navigate(`/identities/${identity.id}/add-data`)}
                      >
                        Add Data
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No identities yet.</p>
          )}
        </div>

        {selectedIdentity ? <p className="helper-copy">Selected identity: {selectedIdentity.display_name}</p> : null}
      </section>
    </section>
  );
}
