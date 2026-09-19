/**
 * components/TemplateSelector.jsx
 * =================================
 * Komponen untuk memilih template preset dari daftar yang diambil dari API.
 *
 * Props:
 *   selectedId    (number|null) — ID template yang dipilih
 *   onSelect      (number|null) → void — Callback saat template dipilih
 *   disabled      (boolean)
 */

import { useEffect, useState } from "react";
import { listTemplates } from "../services/api";
import { LayoutTemplate, Star, User, ChevronDown, RefreshCw } from "lucide-react";

export default function TemplateSelector({ selectedId, onSelect, disabled = false }) {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(null);

  const fetchTemplates = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listTemplates();
      setTemplates(data);
    } catch (err) {
      setError("Gagal memuat template. Pastikan backend berjalan.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTemplates(); }, []);

  const selected = templates.find((t) => t.id === selectedId);

  return (
    <div className="form-group">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span className="label">Pilih Template Format</span>
        <button
          className="btn btn-ghost btn-sm"
          onClick={fetchTemplates}
          disabled={loading}
          title="Refresh daftar template"
          style={{ padding: "var(--space-1) var(--space-2)" }}
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      {loading && (
        <div
          style={{
            padding: "var(--space-4)",
            textAlign: "center",
            color: "var(--clr-text-muted)",
            fontSize: "0.875rem",
          }}
        >
          Memuat template...
        </div>
      )}

      {error && (
        <div
          className="badge badge-error"
          style={{ justifyContent: "center", padding: "var(--space-3)" }}
        >
          {error}
        </div>
      )}

      {!loading && !error && (
        <>
          {templates.length === 0 ? (
            <div
              style={{
                padding: "var(--space-6)",
                textAlign: "center",
                color: "var(--clr-text-muted)",
                fontSize: "0.875rem",
                background: "var(--clr-surface)",
                borderRadius: "var(--radius-lg)",
                border: "1px solid var(--clr-border)",
              }}
            >
              <LayoutTemplate size={24} style={{ margin: "0 auto var(--space-2)" }} />
              Belum ada template. Tambahkan melalui Adaptive Mode.
            </div>
          ) : (
            <div
              style={{
                display: "grid",
                gap: "var(--space-3)",
                maxHeight: "280px",
                overflowY: "auto",
              }}
            >
              {templates.map((t) => (
                <button
                  key={t.id}
                  onClick={() => onSelect(selectedId === t.id ? null : t.id)}
                  disabled={disabled}
                  className={`card ${selectedId === t.id ? "card-glow" : ""}`}
                  style={{
                    cursor: disabled ? "not-allowed" : "pointer",
                    textAlign: "left",
                    padding: "var(--space-4)",
                    display: "flex",
                    alignItems: "center",
                    gap: "var(--space-3)",
                    background:
                      selectedId === t.id
                        ? "rgba(108,99,255,0.12)"
                        : "var(--clr-surface)",
                    borderColor:
                      selectedId === t.id
                        ? "rgba(108,99,255,0.5)"
                        : "var(--clr-border)",
                    transition: "all 0.2s ease",
                    border: "1px solid",
                  }}
                >
                  {/* Icon */}
                  <div
                    style={{
                      width: 36,
                      height: 36,
                      borderRadius: "var(--radius-md)",
                      background: t.is_preset
                        ? "linear-gradient(135deg, var(--clr-primary), var(--clr-accent))"
                        : "var(--clr-surface-2)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                    }}
                  >
                    {t.is_preset ? (
                      <Star size={16} color="#fff" />
                    ) : (
                      <User size={16} color="var(--clr-text-muted)" />
                    )}
                  </div>

                  {/* Info */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p className="font-semibold text-sm" style={{ marginBottom: 2 }}>
                      {t.name}
                    </p>
                    {t.description && (
                      <p
                        className="text-xs text-muted"
                        style={{
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {t.description}
                      </p>
                    )}
                  </div>

                  {/* Badge */}
                  <span className={`badge ${t.is_preset ? "badge-primary" : "badge-info"}`}>
                    {t.is_preset ? "Preset" : "Custom"}
                  </span>
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
