/**
 * components/ResultPreview.jsx
 * ==============================
 * Menampilkan ringkasan hasil klasifikasi struktur dokumen
 * (distribusi label paragraf dari IndoBERT / heuristik).
 *
 * Props:
 *   taskId       (number) — ID task yang selesai
 *   visible      (boolean) — Tampilkan atau tidak
 */

import { useState, useEffect } from "react";
import { getTaskStatus } from "../services/api";
import { BarChart2, FileText } from "lucide-react";

// Warna per label (untuk visualisasi distribusi)
const LABEL_COLORS = {
  judul_bab:      { bg: "rgba(108,99,255,0.15)", text: "var(--clr-primary-light)" },
  sub_bab:        { bg: "rgba(0,212,255,0.12)",  text: "var(--clr-accent)" },
  sub_sub_bab:    { bg: "rgba(96,165,250,0.12)", text: "var(--clr-info)" },
  isi:            { bg: "rgba(255,255,255,0.05)", text: "var(--clr-text-muted)" },
  abstrak:        { bg: "rgba(245,158,11,0.12)", text: "var(--clr-warning)" },
  caption_tabel:  { bg: "rgba(34,211,160,0.12)", text: "var(--clr-success)" },
  caption_gambar: { bg: "rgba(34,211,160,0.12)", text: "var(--clr-success)" },
  daftar_poin:    { bg: "rgba(248,113,113,0.12)", text: "var(--clr-error)" },
  daftar_pustaka: { bg: "rgba(167,139,250,0.12)", text: "#a78bfa" },
};

// Label bahasa Indonesia yang ramah dibaca
const LABEL_DISPLAY = {
  judul_bab:      "Judul Bab",
  sub_bab:        "Sub Bab",
  sub_sub_bab:    "Sub-Sub Bab",
  isi:            "Isi / Paragraf",
  abstrak:        "Abstrak",
  caption_tabel:  "Caption Tabel",
  caption_gambar: "Caption Gambar",
  daftar_poin:    "Daftar / List",
  daftar_pustaka: "Daftar Pustaka",
};

export default function ResultPreview({ taskId, visible }) {
  const [task, setTask] = useState(null);

  useEffect(() => {
    if (visible && taskId) {
      getTaskStatus(taskId)
        .then(setTask)
        .catch(() => {});
    }
  }, [visible, taskId]);

  if (!visible || !task) return null;

  return (
    <div className="card animate-fade-in delay-100">
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-3)",
          marginBottom: "var(--space-5)",
        }}
      >
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: "var(--radius-md)",
            background: "linear-gradient(135deg, var(--clr-primary), var(--clr-accent))",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <BarChart2 size={18} color="#fff" />
        </div>
        <div>
          <h3 className="font-semibold text-base">Hasil Pemrosesan</h3>
          <p className="text-xs text-muted">
            {task.original_filename}
          </p>
        </div>
      </div>

      {/* Status badge */}
      <div style={{ display: "flex", gap: "var(--space-3)", marginBottom: "var(--space-5)" }}>
        <span className={`badge ${task.status === "done" ? "badge-success" : "badge-error"}`}>
          {task.status === "done" ? "✓ Selesai" : "✗ Gagal"}
        </span>
        <span className="badge badge-info">
          Mode: {task.mode === "standard" ? "Standard" : "Adaptive"}
        </span>
      </div>

      {/* Info card */}
      <div
        style={{
          padding: "var(--space-4)",
          background: "var(--clr-surface-2)",
          borderRadius: "var(--radius-md)",
          marginBottom: "var(--space-4)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
          <FileText size={14} color="var(--clr-text-muted)" />
          <span className="text-sm text-muted">File asli:</span>
          <span className="text-sm font-medium" style={{ wordBreak: "break-all" }}>
            {task.original_filename}
          </span>
        </div>
      </div>

      {/* Label distribution (placeholder — akan diisi dari API nanti) */}
      <div>
        <p className="text-xs text-muted" style={{ marginBottom: "var(--space-3)" }}>
          Kategori struktural yang terdeteksi:
        </p>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-2)" }}>
          {Object.entries(LABEL_DISPLAY).map(([key, display]) => {
            const colors = LABEL_COLORS[key] || {};
            return (
              <span
                key={key}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  padding: "4px 10px",
                  borderRadius: "var(--radius-full)",
                  fontSize: "0.75rem",
                  fontWeight: 500,
                  background: colors.bg || "var(--clr-surface-2)",
                  color: colors.text || "var(--clr-text-muted)",
                }}
              >
                {display}
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
}
