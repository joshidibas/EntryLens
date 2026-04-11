import { useState } from "react";
import CameraPanel from "../components/CameraPanel";
import LiveFeed from "../components/LiveFeed";
import type { DetectionSnapshot } from "../types";

export default function LivePage() {
  const [detection, setDetection] = useState<DetectionSnapshot | null>(null);

  return (
    <section className="page-grid">
      <CameraPanel onDetectionChange={setDetection} />
      <LiveFeed detection={detection} />
    </section>
  );
}
