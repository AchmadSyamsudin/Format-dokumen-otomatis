/**
 * pages/AdaptiveMode.jsx
 * ========================
 * Adaptive Learning Mode:
 *   1. Upload dokumen contoh (sudah diformat dengan benar)
 *   2. Upload dokumen target
 *   3. (Opsional) Beri nama template
 *   4. Klik "Format" → sistem ekstrak + format
 *   5. Download hasil
 */

import { useState } from "react";
import { toast } from "react-hot-toast";
import { Cpu, Wand2, Info } from "lucide-react";

import FileUploader from "../components/FileUploader";
import ProgressTracker from "../components/ProgressTracker";
import ResultPreview from "../components/ResultPreview";
import { formatAdaptive, getDownloadUrl } from "../services/api";

export default function AdaptiveMode() {
  const [exampleFile,  setExampleFile]  = useState(null);
  const [targetFile,   setTargetFile]   = useState(null);
  const [templateName, setTemplateName] = useState("");
  const [saveTemplate, setSaveTemplate] = useState(true);

  const [status,    setStatus]    = useState("idle");
  const [uploadPct, setUploadPct] = useState(0);
  const [taskId,    setTaskId]    = useState(null);
  const [errorMsg,  setErrorMsg]  = useState(null);

  const canSubmit = exampleFile && targetFile && status === "idle";
  const isProcessing = status === "uploading" || status === "processing";

  const handleFormat = async () => {
    if (!canSubmit) return;

    setStatus("uploading");
    setUploadPct(0);
    setErrorMsg(null);

    const name = templateName.trim() || `Template dari ${exampleFile.name}`;

    try {
      const result = await formatAdaptive(
        exampleFile,
        targetFile,
        name,
        saveTemplate,
        (pct) => {
          setUploadPct(pct);
          if (pct === 100) setStatus("processing");
        }
      );

      setTaskId(result.task_id);
      setStatus(result.status === "done" ? "done" : "failed");

      if (result.status === "done" && saveTemplate) {
        toast.success(`Template "${name}" disimpan untuk penggunaan berikutnya.`);
      }
    } catch (err) {
      setErrorMsg(err.message || "Gagal memformat dokumen.");
      setStatus("failed");
      toast.error("Formatting gagal: " + err.message);
    }
  };

  const handleDownload = () => {
    if (!taskId) return;
    window.location.href = getDownloadUrl(taskId);
    toast.success("Download dimulai!");
  };

  const handleReset = () => {
    setExampleFile(null);
    setTargetFile(null);
    setTemplateName("");
    setSaveTemplate(true);
    setStatus("idle");
    setUploadPct(0);
    setTaskId(null);
    setErrorMsg(null);
  };

  return (
    <div className="page">
      <div className="container-sm">
        {/* Page header */}
        <div className="page-header">
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "var(--space-2)",
              background: "var(--clr-accent-glow)",
              border: "1px solid rgba(0,212,255,0.4)",
              borderRadius: "var(--radius-full)",
              padding: "var(--space-2) var(--space-4)",
              fontSize: "0.8rem",
              fontWeight: 600,
              color: "var(--clr-accent)",
              marginBottom: "var(--space-5)",
            }}
          >
            <Cpu size={14} />
            Adaptive Learning Mode
          </div>
          <h1 className="page-title" style={{ fontSize: "2rem" }}>
            Format dari <span className="gradient-text">Dokumen Contoh</span>
          </h1>
          <p className="page-subtitle" style={{ fontSize: "0.95rem" }}>
            Sistem akan belajar aturan format dari dokumen contoh Anda menggunakan
            IndoBERT + Rule-Based Extractor, lalu menerapkannya ke dokumen target.
          </p>
        </div>

        {/* Info banner */}
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: "var(--space-3)",
            padding: "var(--space-4)",
            background: "rgba(0,212,255,0.06)",
            border: "1px solid rgba(0,212,255,0.2)",
            borderRadius: "var(--radius-lg)",
            marginBottom: "var(--space-6)",
          }}
          className="animate-fade-in"
        >
          <Info size={18} color="var(--clr-accent)" style={{ flexShrink: 0, marginTop: 2 }} />
          <p className="text-sm" style={{ color: "var(--clr-text-muted)", lineHeight: 1.7 }}>
            <strong style={{ color: "var(--clr-accent)" }}>Cara kerja:</strong> IndoBERT
            mengklasifikasikan setiap paragraf di dokumen contoh (judul bab, sub-bab, isi, dll.),
            lalu rule-based extractor mengukur properti format tiap paragraf tersebut.
            Aturan yang diekstrak disimpan sebagai template JSON dan diterapkan ke dokumen target.
          </p>
        </div>

        {/* Main form */}
        <div
          className="card animate-fade-in"
          style={{ display: "flex", flexDirection: "column", gap: "var(--space-6)" }}
        >
          {/* Step 1: Dokumen contoh */}
          <div>
            <StepLabel step={1} done={Boolean(exampleFile)} label="Upload Dokumen Contoh" />
            <p
              className="text-xs text-muted"
              style={{ marginBottom: "var(--space-3)", marginTop: "var(--space-1)" }}
            >
              Dokumen yang sudah diformat dengan benar sesuai pedoman institusi.
            </p>
            <FileUploader
              file={exampleFile}
              onFileChange={setExampleFile}
              disabled={isProcessing}
              description="Upload dokumen contoh yang sudah diformat dengan benar"
            />
          </div>

          <hr style={{ border: "none", borderTop: "1px solid var(--clr-border)" }} />

          {/* Step 2: Dokumen target */}
          <div>
            <StepLabel step={2} done={Boolean(targetFile)} label="Upload Dokumen Target" />
            <p
              className="text-xs text-muted"
              style={{ marginBottom: "var(--space-3)", marginTop: "var(--space-1)" }}
            >
              Dokumen yang akan diformat mengikuti aturan dari dokumen contoh.
            </p>
            <FileUploader
              file={targetFile}
              onFileChange={setTargetFile}
              disabled={isProcessing}
              description="Upload dokumen yang ingin diformat ulang"
            />
          </div>

          <hr style={{ border: "none", borderTop: "1px solid var(--clr-border)" }} />

          {/* Step 3: Nama template (opsional) */}
          <div>
            <StepLabel step={3} done={false} label="Konfigurasi Template (Opsional)" />
            <div
              style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)", marginTop: "var(--space-3)" }}
            >
              <div className="form-group">
                <label className="label" htmlFor="template-name">
                  Nama Template
                </label>
                <input
                  id="template-name"
                  className="input"
                  type="text"
                  placeholder={
                    exampleFile
                      ? `Template dari ${exampleFile.name}`
                      : "Contoh: Template Skripsi PENS 2024"
                  }
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  disabled={isProcessing}
                  maxLength={200}
                />
              </div>

              {/* Toggle simpan template */}
              <label
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "var(--space-3)",
                  cursor: isProcessing ? "not-allowed" : "pointer",
                  userSelect: "none",
                }}
              >
                <div
                  onClick={() => !isProcessing && setSaveTemplate((v) => !v)}
                  style={{
                    width: 40,
                    height: 22,
                    borderRadius: "var(--radius-full)",
                    background: saveTemplate
                      ? "var(--clr-primary)"
                      : "var(--clr-surface-2)",
                    border: "1px solid var(--clr-border)",
                    position: "relative",
                    transition: "background 0.2s",
                    cursor: isProcessing ? "not-allowed" : "pointer",
                  }}
                >
                  <div
                    style={{
                      position: "absolute",
                      top: 2,
                      left: saveTemplate ? 20 : 2,
                      width: 16,
                      height: 16,
                      borderRadius: "50%",
                      background: "#fff",
                      transition: "left 0.2s",
                    }}
                  />
                </div>
                <div>
                  <p className="text-sm font-medium">Simpan template untuk digunakan kembali</p>
                  <p className="text-xs text-muted">
                    Template akan tersedia di Standard Mode tanpa perlu upload ulang dokumen contoh
                  </p>
                </div>
              </label>
            </div>
          </div>

          <hr style={{ border: "none", borderTop: "1px solid var(--clr-border)" }} />

          {/* Submit */}
          <button
            className="btn btn-accent btn-lg"
            onClick={handleFormat}
            disabled={!canSubmit}
            id="btn-format-adaptive"
          >
            {isProcessing ? (
              <>
                <span className="animate-spin" style={{ display: "inline-block" }}>⟳</span>
                Memproses...
              </>
            ) : (
              <>
                <Wand2 size={18} />
                Ekstrak & Format
              </>
            )}
          </button>

          {!canSubmit && status === "idle" && (
            <p className="text-xs text-muted" style={{ textAlign: "center" }}>
              {!exampleFile && !targetFile
                ? "Upload dokumen contoh dan dokumen target untuk melanjutkan."
                : !exampleFile
                ? "Upload dokumen contoh terlebih dahulu."
                : "Upload dokumen target terlebih dahulu."}
            </p>
          )}
        </div>

        {/* Progress */}
        <div style={{ marginTop: "var(--space-6)" }}>
          <ProgressTracker
            status={status}
            uploadProgress={uploadPct}
            taskId={taskId}
            errorMsg={errorMsg}
            onDownload={handleDownload}
            onReset={handleReset}
          />
        </div>

        {/* Result */}
        <div style={{ marginTop: "var(--space-4)" }}>
          <ResultPreview taskId={taskId} visible={status === "done"} />
        </div>
      </div>
    </div>
  );
}

/* ─── Step Label Helper Component ─── */
function StepLabel({ step, done, label }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", marginBottom: "var(--space-2)" }}>
      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: "var(--radius-full)",
          background: done
            ? "linear-gradient(135deg, var(--clr-primary), var(--clr-accent))"
            : "var(--clr-surface-2)",
          border: "1px solid var(--clr-border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "0.75rem",
          fontWeight: 700,
          color: done ? "#fff" : "var(--clr-text-faint)",
          flexShrink: 0,
        }}
      >
        {done ? "✓" : step}
      </div>
      <span className="font-semibold text-sm">{label}</span>
    </div>
  );
}
