/**
 * components/ProgressTracker.jsx
 * ================================
 * Menampilkan status & progress pemrosesan dokumen.
 *
 * Props:
 *   status       ('idle'|'uploading'|'processing'|'done'|'failed')
 *   uploadProgress (0-100, angka)
 *   taskId       (number|null)
 *   errorMsg     (string|null)
 *   onDownload   () → void — Dipanggil saat tombol download diklik
 *   onReset      () → void — Dipanggil saat tombol "Mulai lagi" diklik
 */

import { CheckCircle, XCircle, Loader2, Upload, FileDown, RotateCcw } from "lucide-react";

const STEPS = [
  { key: "uploading",   label: "Mengupload dokumen" },
  { key: "processing",  label: "Menganalisis & memformat" },
  { key: "done",        label: "Selesai" },
];

function StepIcon({ active, done, failed }) {
  if (failed)
    return <XCircle size={20} color="var(--clr-error)" />;
  if (done)
    return <CheckCircle size={20} color="var(--clr-success)" />;
  if (active)
    return <Loader2 size={20} color="var(--clr-primary-light)" className="animate-spin" />;
  return (
    <div
      style={{
        width: 20,
        height: 20,
        borderRadius: "50%",
        border: "2px solid var(--clr-border)",
      }}
    />
  );
}

export default function ProgressTracker({
  status,
  uploadProgress = 0,
  taskId,
  errorMsg,
  onDownload,
  onReset,
}) {
  if (status === "idle") return null;

  const stepIndex = STEPS.findIndex((s) => s.key === status);
  const isFailed  = status === "failed";
  const isDone    = status === "done";

  return (
    <div
      className="card animate-fade-in"
      style={{
        borderColor: isFailed
          ? "rgba(248,113,113,0.3)"
          : isDone
          ? "rgba(34,211,160,0.3)"
          : "var(--clr-border)",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "var(--space-5)",
        }}
      >
        <h3 className="font-semibold text-base">Status Pemrosesan</h3>
        {taskId && (
          <span className="text-xs text-muted">
            Task #{taskId}
          </span>
        )}
      </div>

      {/* Upload progress bar (saat uploading) */}
      {status === "uploading" && (
        <div style={{ marginBottom: "var(--space-5)" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              marginBottom: "var(--space-2)",
            }}
          >
            <span className="text-xs text-muted">Upload progress</span>
            <span className="text-xs font-semibold text-primary">{uploadProgress}%</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${uploadProgress}%` }} />
          </div>
        </div>
      )}

      {/* Processing animation */}
      {status === "processing" && (
        <div style={{ marginBottom: "var(--space-5)" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "var(--space-3)",
              padding: "var(--space-4)",
              background: "rgba(108,99,255,0.08)",
              borderRadius: "var(--radius-md)",
              marginBottom: "var(--space-3)",
            }}
          >
            <Loader2 size={18} color="var(--clr-primary-light)" className="animate-spin" />
            <div>
              <p className="text-sm font-medium">IndoBERT mengklasifikasikan paragraf...</p>
              <p className="text-xs text-muted">
                Memformat dokumen sesuai template yang dipilih
              </p>
            </div>
          </div>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: "100%", animation: "shimmer 1.5s linear infinite" }}
            />
          </div>
        </div>
      )}

      {/* Steps */}
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
        {STEPS.map((step, i) => {
          const isActive = i === stepIndex && !isFailed;
          const isDoneStep = i < stepIndex || isDone;
          const isThisFailed = isFailed && i === stepIndex;

          return (
            <div
              key={step.key}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--space-3)",
                opacity: i > stepIndex && !isFailed ? 0.4 : 1,
                transition: "opacity 0.3s",
              }}
            >
              <StepIcon
                active={isActive}
                done={isDoneStep}
                failed={isThisFailed}
              />
              <span
                className="text-sm"
                style={{
                  color: isDoneStep
                    ? "var(--clr-success)"
                    : isActive
                    ? "var(--clr-text)"
                    : isThisFailed
                    ? "var(--clr-error)"
                    : "var(--clr-text-muted)",
                  fontWeight: isActive || isDoneStep ? 500 : 400,
                }}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Error message */}
      {isFailed && errorMsg && (
        <div
          style={{
            marginTop: "var(--space-4)",
            padding: "var(--space-4)",
            background: "rgba(248,113,113,0.08)",
            border: "1px solid rgba(248,113,113,0.2)",
            borderRadius: "var(--radius-md)",
          }}
        >
          <p className="text-sm text-error">{errorMsg}</p>
        </div>
      )}

      {/* Actions */}
      {(isDone || isFailed) && (
        <div
          style={{
            display: "flex",
            gap: "var(--space-3)",
            marginTop: "var(--space-5)",
          }}
        >
          {isDone && onDownload && (
            <button className="btn btn-accent" onClick={onDownload} style={{ flex: 1 }}>
              <FileDown size={16} />
              Download Hasil
            </button>
          )}
          {onReset && (
            <button
              className="btn btn-ghost"
              onClick={onReset}
              style={{ flex: isDone ? "0 0 auto" : 1 }}
            >
              <RotateCcw size={16} />
              Mulai Lagi
            </button>
          )}
        </div>
      )}
    </div>
  );
}
