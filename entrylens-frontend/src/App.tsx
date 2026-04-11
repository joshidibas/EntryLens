import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import AttendancePage from "./pages/AttendancePage";
import LabsPage from "./pages/LabsPage";
import EnrollPage from "./pages/EnrollPage";
import LivePage from "./pages/LivePage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/live" replace />} />
        <Route path="/live" element={<LivePage />} />
        <Route path="/attendance" element={<AttendancePage />} />
        <Route path="/enroll" element={<EnrollPage />} />
        <Route path="/labs" element={<LabsPage />} />
      </Route>
    </Routes>
  );
}
