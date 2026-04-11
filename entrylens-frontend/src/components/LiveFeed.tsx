import type { DetectionSnapshot } from "../types";
import type { DetectionLogDetail } from "../api/detectionLogs";

const placeholderEvents = [
  { id: "evt-001", label: "Recognition event stream is still pending", meta: "WebSocket work can layer on top of the live detector later." },
  { id: "evt-002", label: "Current live mode is browser-side face detection", meta: "This gives us real camera feedback before backend attendance events are wired." },
];

export default function LiveFeed({
  detection,
  identifyResult,
  isIdentifying,
  recentLog,
  logError,
}: {
  detection: DetectionSnapshot | null;
  identifyResult: { name: string; similarity: number } | null;
  isIdentifying: boolean;
  recentLog: DetectionLogDetail | null;
  logError: string;
}) {
  const detectedFaces = detection?.detectedFaces ?? 0;
  const sampleLandmarks = detection?.sampleLandmarks ?? [];

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Feed</p>
          <h3>Recent Activity</h3>
        </div>
        <span className="panel-tag">
          {isIdentifying
            ? "Identifying"
            : identifyResult
              ? "Match found"
              : detection?.hasFace
                ? "Face visible"
                : "Watching feed"}
        </span>
      </div>

      <div className="progress-list">
        <article className={`progress-item ${detection?.hasFace ? "success" : "running"}`}>
          <strong>Live detector</strong>
          <span>{detection ? `MediaPipe is reading the camera feed and sees ${detectedFaces} face(s).` : "Start the camera to begin live analysis."}</span>
        </article>
        <article className={`progress-item ${isIdentifying || identifyResult ? "success" : ""}`}>
          <strong>Recognition</strong>
          <span>
            {isIdentifying
              ? (
                <>
                  <span className="inline-activity">
                    <span className="inline-activity-spinner" aria-hidden="true" />
                    Identifying
                  </span>
                  {" "}
                  EntryLens is matching the current face against enrolled profiles.
                </>
              )
              : identifyResult
                ? `Recognized ${identifyResult.name} with ${(identifyResult.similarity * 100).toFixed(1)}% confidence.`
                : "Recognition is idle until a face is visible and ready for a lookup."}
          </span>
        </article>
        <article className={`progress-item ${logError ? "error" : recentLog ? "success" : ""}`}>
          <strong>Detection logging</strong>
          <span>
            {logError
              ? logError
              : recentLog
                ? `Latest log is ${recentLog.review_status} for ${recentLog.current_identity?.display_name ?? "Unknown"}${recentLog.auto_similarity != null ? ` at ${(recentLog.auto_similarity * 100).toFixed(1)}% similarity.` : "."}`
                : "Live feed will save a review log after each completed recognition pass."}
          </span>
        </article>
        <article className="progress-item">
          <strong>Frame summary</strong>
          <span>{detection ? `${detection.frameWidth} x ${detection.frameHeight} video frame, ${detection.firstFaceLandmarkCount} landmarks on the first face.` : "No frame metrics yet."}</span>
        </article>
      </div>

      <div className="feed-list">
        {placeholderEvents.map((event) => (
          <article className="feed-item" key={event.id}>
            <strong>{event.label}</strong>
            <span>{event.meta}</span>
          </article>
        ))}
      </div>

      <div className="lab-summary">
        <strong>Sample landmarks</strong>
        {sampleLandmarks.length > 0 ? (
          <pre className="code-panel">{JSON.stringify(sampleLandmarks, null, 2)}</pre>
        ) : (
          <p>No landmark sample yet. Put a face in frame after starting the camera.</p>
        )}
      </div>
    </section>
  );
}
