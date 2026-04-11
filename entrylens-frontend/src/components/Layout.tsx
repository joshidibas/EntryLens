import { NavLink, Outlet } from "react-router-dom";
import { useEffect, useState } from "react";
import { apiFetch } from "../api/client";

type Status = "checking" | "online" | "offline" | "planned";

const navItems = [
  { to: "/live", label: "Live" },
  { to: "/attendance", label: "Attendance" },
  { to: "/identities", label: "Identities" },
  { to: "/enroll", label: "Enroll" },
  { to: "/labs", label: "Labs" },
];

export default function Layout() {
  const [apiStatus, setApiStatus] = useState<Status>("checking");
  const [wsStatus] = useState<Status>("planned");

  useEffect(() => {
    let active = true;

    apiFetch("/health")
      .then(() => {
        if (active) {
          setApiStatus("online");
        }
      })
      .catch(() => {
        if (active) {
          setApiStatus("offline");
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">Operator Console</p>
          <h1>EntryLens</h1>
          <p className="sidebar-copy">
            Bootstrap shell for live monitoring, attendance review, and enrollment workflows.
          </p>
        </div>

        <nav className="nav-list" aria-label="Primary navigation">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div>
            <p className="eyebrow">System Status</p>
            <h2>Runnable UI Bootstrap</h2>
          </div>
          <div className="status-group">
            <StatusPill label="API" status={apiStatus} />
            <StatusPill label="WebSocket" status={wsStatus} />
          </div>
        </header>

        <Outlet />
      </main>
    </div>
  );
}

function StatusPill({ label, status }: { label: string; status: Status }) {
  return (
    <div className={`status-pill ${status}`}>
      <span>{label}</span>
      <strong>{status}</strong>
    </div>
  );
}
