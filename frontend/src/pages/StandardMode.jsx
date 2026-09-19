/**
 * pages/StandardMode.jsx
 * ========================
 * Standard Template Mode:
 *   1. Pilih template preset
 *   2. Upload dokumen target
 *   3. Klik "Format" → progress
 *   4. Download hasil
 */

import { useState } from "react";
import { toast } from "react-hot-toast";
import { BookOpen, Wand2 } from "lucide-react";

import FileUploader from "../components/FileUploader";
import TemplateSelector from "../components/TemplateSelector";
import ProgressTracker from "../components/ProgressTracker";
import ResultPreview from "../components/ResultPreview";
import { formatStandard, getDownloadUrl } from "../services/api";

export default function StandardMode() {
  const [targetFile,   setTargetFile]   = useState(null);
  const [templateId,   setTemplateId]   = useState(null);
  const [status,       setStatus]       = useState("idle"); // idle|uploading|processing|done|failed
  const [uploadPct,    setUploadPct]    = useState(0);
  const [taskId,       setTaskId]       = useState(null);
  const [errorMsg,     setErrorMsg]     = useState(null);

  const canSubmit = targetFile && templateId && status === "idle";

  const handleFormat = async () => {
    if (!canSubmit) return;

    setStatus("uploading");
    setUploadPct(0);
    setErrorMsg(null);

    try {
      const result = await formatStandard(targetFile, templateId, (pct) => {
        setUploadPct(pct);
        if (pct === 100) setStatus("processing");
      });

      setTaskId(result.task_id);
      setStatus(result.status === "done" ? "done" : "failed");
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
    setTargetFile(null);
    setTemplateId(null);
    setStatus("idle");
    setUploadPct(0);
    setTaskId(null);
    setErrorMsg(null);
  };

  const isProcessing = status === "uploading" || status === "processing";

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
              background: "var(--clr-primary-glow)",
              border: "1px solid rgba(108,99,255,0.4)",
              borderRadius: "var(--radius-full)",
              padding: "var(--space-2) var(--space-4)",
              fontSize: "0.8rem",
              fontWeight: 600,
              color: "var(--clr-primary-light)",
              marginBottom: "var(--space-5)",
            }}
          >
            <BookOpen size={14} />
            Standard Template Mode
          </div>
          <h1 className="page-title" style={{ fontSize: "2rem" }}>
            Format dengan <span className="gradient-text">Template Preset</span>
          </h1>
          <p className="page-subtitle" style={{ fontSize: "0.95rem" }}>
            Pilih template bawaan sesuai pedoman institusi, unggah dokumen Anda,
            dan dapatkan hasil yang terformat dalam hitungan detik.
          </p>
        </div>

        {/* Main form card */}
        <div
          className="card animate-fade-in"
          style={{ display: "flex", flexDirection: "column", gap: "var(--space-6)" }}
        >
          {/* Step 1: Pilih template */}
          <div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--space-3)",
                marginBottom: "var(--space-4)",
              }}
            >
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: "var(--radius-full)",
                  background: templateId
                    ? "linear-gradient(135deg, var(--clr-primary), var(--clr-accent))"
                    : "var(--clr-surface-2)",
                  border: "1px solid var(--clr-border)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  color: templateId ? "#fff" : "var(--clr-text-faint)",
                }}
              >
                1
              </div>
              <span className="font-semibold text-sm">Pilih Template</span>
            </div>
            <TemplateSelector
              selectedId={templateId}
              onSelect={setTemplateId}
              disabled={isProcessing}
            />
          </div>

          <hr style={{ border: "none", borderTop: "1px solid var(--clr-border)" }} />

          {/* Step 2: Upload target */}
          <div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--space-3)",
                marginBottom: "var(--space-4)",
              }}
            >
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: "var(--radius-full)",
                  background: targetFile
                    ? "linear-gradient(135deg, var(--clr-primary), var(--clr-accent))"
                    : "var(--clr-surface-2)",
                  border: "1px solid var(--clr-border)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  color: targetFile ? "#fff" : "var(--clr-text-faint)",
                }}
              >
                2
              </div>
              <span className="font-semibold text-sm">Upload Dokumen Target</span>
            </div>
            <FileUploader
              label="Dokumen yang akan diformat"
              file={targetFile}
              onFileChange={setTargetFile}
              disabled={isProcessing}
              description="Seret & lepas file .docx Anda di sini, atau klik untuk memilih"
            />
          </div>

          <hr style={{ border: "none", borderTop: "1px solid var(--clr-border)" }} />

          {/* Submit button */}
          <button
            className="btn btn-primary btn-lg"
            onClick={handleFormat}
            disabled={!canSubmit}
            id="btn-format-standard"
          >
            {isProcessing ? (
              <>
                <span className="animate-spin" style={{ display: "inline-block" }}>⟳</span>
                Sedang Memproses...
              </>
            ) : (
              <>
                <Wand2 size={18} />
                Format Dokumen
              </>
            )}
          </button>

          {/* Validation hint */}
          {!canSubmit && status === "idle" && (
            <p className="text-xs text-muted" style={{ textAlign: "center" }}>
              {!templateId && !targetFile
                ? "Pilih template dan upload dokumen untuk melanjutkan."
                : !templateId
                ? "Pilih template terlebih dahulu."
                : "Upload dokumen target terlebih dahulu."}
            </p>
          )}
        </div>

        {/* Progress tracker */}
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

        {/* Result preview */}
        <div style={{ marginTop: "var(--space-4)" }}>
          <ResultPreview taskId={taskId} visible={status === "done"} />
        </div>
      </div>
    </div>
  );
}
