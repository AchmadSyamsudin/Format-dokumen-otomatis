/**
 * pages/Home.jsx
 * ===============
 * Landing page utama — menjelaskan fitur dan mengarahkan ke dua mode.
 */

import { Link } from "react-router-dom";
import {
  Wand2, BookOpen, Cpu, FileCheck, ArrowRight,
  Layers, Zap, Lock
} from "lucide-react";

const FEATURES = [
  {
    icon: Layers,
    title: "Dua Layer Pipeline",
    desc: "Rule-based parsing + IndoBERT classifier bekerja secara independen untuk akurasi maksimal.",
    color: "var(--clr-primary-light)",
    glow: "var(--clr-primary-glow)",
  },
  {
    icon: Zap,
    title: "Adaptive Learning",
    desc: "Unggah dokumen contoh — sistem belajar aturan format dan menerapkannya ke dokumen lain.",
    color: "var(--clr-accent)",
    glow: "var(--clr-accent-glow)",
  },
  {
    icon: Lock,
    title: "100% Lokal / Offline",
    desc: "Semua inferensi AI berjalan di mesin Anda. Tidak ada data yang dikirim ke cloud.",
    color: "var(--clr-success)",
    glow: "rgba(34,211,160,0.2)",
  },
];

const MODES = [
  {
    to: "/standard",
    icon: BookOpen,
    badge: "Preset Template",
    title: "Standard Mode",
    description:
      "Pilih template bawaan (berdasarkan pedoman institusi) dan terapkan langsung ke dokumen Anda tanpa perlu contoh.",
    cta: "Gunakan Standard Mode",
    gradient: "linear-gradient(135deg, #6c63ff, #4d44dd)",
    glow: "var(--clr-primary-glow)",
  },
  {
    to: "/adaptive",
    icon: Cpu,
    badge: "AI Powered",
    title: "Adaptive Mode",
    description:
      "Unggah dokumen contoh yang sudah diformat dengan benar. Sistem ekstrak aturan format-nya dan terapkan ke dokumen target.",
    cta: "Gunakan Adaptive Mode",
    gradient: "linear-gradient(135deg, #00d4ff, #007fa6)",
    glow: "var(--clr-accent-glow)",
  },
];

export default function Home() {
  return (
    <div className="page">
      {/* ─── Hero ─── */}
      <section
        style={{
          textAlign: "center",
          padding: "var(--space-16) 0 var(--space-12)",
          position: "relative",
        }}
      >
        {/* Background glow */}
        <div
          aria-hidden="true"
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -60%)",
            width: "600px",
            height: "400px",
            background:
              "radial-gradient(ellipse, rgba(108,99,255,0.12) 0%, transparent 70%)",
            pointerEvents: "none",
            zIndex: 0,
          }}
        />

        <div className="container" style={{ position: "relative", zIndex: 1 }}>
          {/* Badge */}
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "var(--space-2)",
              background: "var(--clr-primary-glow)",
              border: "1px solid rgba(108,99,255,0.4)",
              borderRadius: "var(--radius-full)",
              padding: "var(--space-2) var(--space-4)",
              fontSize: "0.8rem",
              fontWeight: 600,
              color: "var(--clr-primary-light)",
              marginBottom: "var(--space-6)",
            }}
            className="animate-fade-in"
          >
            <Wand2 size={14} />
            Tugas Akhir — D3 Manajemen Informatika
          </div>

          {/* Headline */}
          <h1
            className="page-title gradient-text animate-fade-in delay-100"
            style={{ fontSize: "clamp(2rem, 5vw, 3.5rem)", maxWidth: "800px", margin: "0 auto var(--space-6)" }}
          >
            Format Dokumen Akademik Otomatis dengan AI
          </h1>

          <p
            className="page-subtitle animate-fade-in delay-200"
            style={{ maxWidth: "580px" }}
          >
            Hybrid Rule-Based + IndoBERT untuk klasifikasi struktur dan penerapan
            aturan format dokumen karya ilmiah berbasis template adaptif.
          </p>

          {/* CTAs */}
          <div
            className="animate-fade-in delay-300"
            style={{
              display: "flex",
              gap: "var(--space-4)",
              justifyContent: "center",
              marginTop: "var(--space-8)",
              flexWrap: "wrap",
            }}
          >
            <Link to="/standard" className="btn btn-primary btn-lg">
              <BookOpen size={18} />
              Standard Mode
            </Link>
            <Link to="/adaptive" className="btn btn-ghost btn-lg">
              <Cpu size={18} />
              Adaptive Mode
              <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>

      {/* ─── Features ─── */}
      <section style={{ padding: "0 0 var(--space-16)" }}>
        <div className="container">
          <div className="grid grid-3" style={{ gap: "var(--space-6)" }}>
            {FEATURES.map(({ icon: Icon, title, desc, color, glow }, i) => (
              <div
                key={title}
                className={`card animate-fade-in delay-${(i + 1) * 100}`}
                style={{ padding: "var(--space-6)" }}
              >
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: "var(--radius-lg)",
                    background: `radial-gradient(circle, ${glow} 0%, transparent 70%)`,
                    border: `1px solid ${color}30`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    marginBottom: "var(--space-4)",
                  }}
                >
                  <Icon size={22} color={color} />
                </div>
                <h3 className="font-semibold text-base" style={{ marginBottom: "var(--space-2)" }}>
                  {title}
                </h3>
                <p className="text-sm text-muted">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Mode Cards ─── */}
      <section style={{ padding: "0 0 var(--space-16)" }}>
        <div className="container">
          <div style={{ textAlign: "center", marginBottom: "var(--space-10)" }}>
            <h2 className="font-bold text-2xl" style={{ marginBottom: "var(--space-3)" }}>
              Pilih Mode Pemrosesan
            </h2>
            <p className="text-muted text-sm">
              Keduanya menggunakan pipeline yang sama — IndoBERT + Rule-Based — dengan
              sumber aturan format yang berbeda.
            </p>
          </div>

          <div className="grid grid-2" style={{ gap: "var(--space-6)" }}>
            {MODES.map(({ to, icon: Icon, badge, title, description, cta, gradient, glow }) => (
              <div
                key={to}
                className="card"
                style={{
                  padding: "var(--space-8)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "var(--space-5)",
                }}
              >
                {/* Icon */}
                <div
                  style={{
                    width: 56,
                    height: 56,
                    borderRadius: "var(--radius-lg)",
                    background: gradient,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    boxShadow: `0 8px 24px ${glow}`,
                  }}
                >
                  <Icon size={26} color="#fff" />
                </div>

                {/* Badge */}
                <div>
                  <span className="badge badge-primary" style={{ marginBottom: "var(--space-2)" }}>
                    {badge}
                  </span>
                  <h3 className="font-bold text-xl" style={{ marginTop: "var(--space-2)" }}>
                    {title}
                  </h3>
                </div>

                <p className="text-muted text-sm" style={{ flex: 1, lineHeight: 1.7 }}>
                  {description}
                </p>

                <Link
                  to={to}
                  className="btn btn-ghost"
                  style={{ alignSelf: "flex-start" }}
                >
                  {cta}
                  <ArrowRight size={16} />
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Pipeline Diagram ─── */}
      <section style={{ padding: "0 0 var(--space-16)" }}>
        <div className="container-sm">
          <div className="card" style={{ padding: "var(--space-8)" }}>
            <h3
              className="font-bold text-lg"
              style={{ textAlign: "center", marginBottom: "var(--space-6)" }}
            >
              Arsitektur Pipeline
            </h3>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--space-3)",
                overflowX: "auto",
                paddingBottom: "var(--space-2)",
              }}
            >
              {[
                { icon: "📄", label: "Upload .docx" },
                { icon: "🤖", label: "IndoBERT\nClassifier", highlight: true },
                { icon: "📋", label: "Label\nParagraf" },
                { icon: "⚙️", label: "Rule-Based\nFormatter", highlight: true },
                { icon: "✅", label: "Dokumen\nFormatted" },
              ].map((step, i, arr) => (
                <div
                  key={i}
                  style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", flexShrink: 0 }}
                >
                  <div
                    style={{
                      textAlign: "center",
                      padding: "var(--space-4)",
                      borderRadius: "var(--radius-lg)",
                      background: step.highlight
                        ? "rgba(108,99,255,0.1)"
                        : "var(--clr-surface-2)",
                      border: step.highlight
                        ? "1px solid rgba(108,99,255,0.3)"
                        : "1px solid var(--clr-border)",
                      minWidth: "90px",
                    }}
                  >
                    <div style={{ fontSize: "1.5rem", marginBottom: "var(--space-2)" }}>
                      {step.icon}
                    </div>
                    <p
                      className="text-xs font-medium"
                      style={{
                        whiteSpace: "pre-line",
                        lineHeight: 1.4,
                        color: step.highlight
                          ? "var(--clr-primary-light)"
                          : "var(--clr-text-muted)",
                      }}
                    >
                      {step.label}
                    </p>
                  </div>
                  {i < arr.length - 1 && (
                    <ArrowRight size={16} color="var(--clr-text-faint)" />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
