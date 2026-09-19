/**
 * App.jsx — Root component dengan routing dan navbar
 */

import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { BookOpen, Cpu, Home as HomeIcon } from "lucide-react";

import Home         from "./pages/Home";
import StandardMode from "./pages/StandardMode";
import AdaptiveMode from "./pages/AdaptiveMode";

function Navbar() {
  return (
    <nav className="navbar">
      <div className="container">
        <div className="navbar-inner">
          {/* Logo */}
          <NavLink to="/" className="navbar-logo">
            <div className="logo-icon">📄</div>
            <span>DocFormat<span style={{ color: "var(--clr-primary-light)" }}>AI</span></span>
          </NavLink>

          {/* Navigation links */}
          <div className="navbar-nav">
            <NavLink
              to="/"
              end
              className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
            >
              <HomeIcon size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "middle" }} />
              Beranda
            </NavLink>
            <NavLink
              to="/standard"
              className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
            >
              <BookOpen size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "middle" }} />
              Standard
            </NavLink>
            <NavLink
              to="/adaptive"
              className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
            >
              <Cpu size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "middle" }} />
              Adaptive
            </NavLink>
          </div>

          {/* Backend status indicator */}
          <BackendStatus />
        </div>
      </div>
    </nav>
  );
}

import { useEffect, useState } from "react";
import { healthCheck } from "./services/api";

function BackendStatus() {
  const [status, setStatus] = useState("checking"); // checking | online | offline

  useEffect(() => {
    healthCheck()
      .then((data) => setStatus(data.indobert_loaded ? "model-loaded" : "online"))
      .catch(() => setStatus("offline"));
  }, []);

  const configs = {
    checking:     { color: "var(--clr-warning)", label: "Menghubungkan..." },
    online:       { color: "var(--clr-info)",    label: "Backend Online" },
    "model-loaded":{ color: "var(--clr-success)", label: "IndoBERT Loaded" },
    offline:      { color: "var(--clr-error)",   label: "Backend Offline" },
  };

  const cfg = configs[status] || configs.offline;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "var(--space-2)",
        padding: "var(--space-2) var(--space-3)",
        borderRadius: "var(--radius-full)",
        background: "var(--clr-surface)",
        border: "1px solid var(--clr-border)",
        fontSize: "0.75rem",
        fontWeight: 500,
        color: "var(--clr-text-muted)",
      }}
    >
      <div
        style={{
          width: 7,
          height: 7,
          borderRadius: "50%",
          background: cfg.color,
          boxShadow: `0 0 6px ${cfg.color}`,
          animation: status === "checking" ? "pulse-glow 1.5s infinite" : "none",
        }}
      />
      <span>{cfg.label}</span>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "var(--clr-surface)",
            color: "var(--clr-text)",
            border: "1px solid var(--clr-border)",
            borderRadius: "var(--radius-md)",
            fontFamily: "var(--font-sans)",
            fontSize: "0.875rem",
          },
          success: {
            iconTheme: { primary: "var(--clr-success)", secondary: "var(--clr-bg)" },
          },
          error: {
            iconTheme: { primary: "var(--clr-error)", secondary: "var(--clr-bg)" },
          },
        }}
      />

      <Navbar />

      <Routes>
        <Route path="/"          element={<Home />}         />
        <Route path="/standard"  element={<StandardMode />} />
        <Route path="/adaptive"  element={<AdaptiveMode />} />
      </Routes>

      {/* Footer */}
      <footer
        style={{
          borderTop: "1px solid var(--clr-border)",
          padding: "var(--space-6) 0",
          textAlign: "center",
        }}
      >
        <div className="container">
          <p className="text-xs text-faint">
            DocFormatAI — Tugas Akhir D3 Manajemen Informatika |{" "}
            <span className="text-primary">Hybrid Rule-Based + IndoBERT</span> |
            Semua inferensi berjalan lokal/offline.
          </p>
        </div>
      </footer>
    </BrowserRouter>
  );
}
