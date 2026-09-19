/**
 * components/FileUploader.jsx
 * ============================
 * Komponen drag-and-drop file uploader untuk file .docx.
 * Menampilkan nama file yang dipilih dan tombol hapus.
 *
 * Props:
 *   label       (string) — Label yang ditampilkan di atas dropzone
 *   file        (File|null) — File yang sudah dipilih (controlled)
 *   onFileChange(File|null) — Callback saat file berubah
 *   disabled    (boolean) — Nonaktifkan interaksi
 *   description (string) — Teks helper di dalam dropzone
 */

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { FileText, Upload, X, CheckCircle } from "lucide-react";

export default function FileUploader({
  label,
  file,
  onFileChange,
  disabled = false,
  description = "Seret & lepas file .docx ke sini, atau klik untuk memilih",
}) {
  const onDrop = useCallback(
    (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        onFileChange(acceptedFiles[0]);
      }
    },
    [onFileChange]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    maxFiles: 1,
    disabled,
  });

  const hasFile = Boolean(file);

  return (
    <div className="form-group">
      {label && <span className="label">{label}</span>}

      {hasFile ? (
        /* File sudah dipilih — tampilkan info file */
        <div
          className="dropzone has-file"
          style={{ gap: "var(--space-3)", padding: "var(--space-6) var(--space-8)" }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "var(--space-3)",
              width: "100%",
              justifyContent: "space-between",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
              <div className="dropzone-icon" style={{ background: "rgba(34,211,160,0.15)" }}>
                <CheckCircle size={22} color="var(--clr-success)" />
              </div>
              <div style={{ textAlign: "left" }}>
                <p
                  className="font-semibold text-sm"
                  style={{ color: "var(--clr-success)", marginBottom: "2px" }}
                >
                  {file.name}
                </p>
                <p className="text-xs text-muted">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>

            {/* Tombol hapus */}
            {!disabled && (
              <button
                className="btn btn-ghost btn-sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onFileChange(null);
                }}
                title="Hapus file"
                style={{ borderRadius: "var(--radius-full)", padding: "var(--space-2)" }}
              >
                <X size={16} />
              </button>
            )}
          </div>
        </div>
      ) : (
        /* Dropzone kosong */
        <div
          {...getRootProps()}
          className={`dropzone ${isDragActive ? "active" : ""}`}
        >
          <input {...getInputProps()} />
          <div className="dropzone-icon">
            {isDragActive ? <Upload size={24} /> : <FileText size={24} />}
          </div>
          <div>
            <p
              className="font-medium text-sm"
              style={{ color: "var(--clr-text)", marginBottom: "4px" }}
            >
              {isDragActive ? "Lepaskan file di sini..." : description}
            </p>
            <p className="text-xs text-muted">Hanya file .docx yang diterima</p>
          </div>
          {!disabled && (
            <button
              className="btn btn-ghost btn-sm"
              style={{ pointerEvents: "none" }}
              tabIndex={-1}
            >
              <Upload size={14} />
              Pilih File
            </button>
          )}
        </div>
      )}
    </div>
  );
}
