import CameraPanel from "../components/CameraPanel";
import LiveFeed from "../components/LiveFeed";
import { useRecognitionSession } from "../hooks/useRecognitionSession";

export default function LivePage() {
  const { liveDetection, identifyResult, isIdentifying, handleDetectionChange, runRecognition } = useRecognitionSession();

  return (
    <section className="page-grid">
      <CameraPanel
        onDetectionChange={handleDetectionChange}
        onRecognize={runRecognition}
        recognizedName={identifyResult?.matched ? identifyResult.name ?? undefined : undefined}
        isRecognizing={isIdentifying}
      />
      <LiveFeed
        detection={liveDetection}
        identifyResult={
          identifyResult?.matched && identifyResult.name
            ? { name: identifyResult.name, similarity: identifyResult.similarity }
            : null
        }
        isIdentifying={isIdentifying}
      />
    </section>
  );
}
