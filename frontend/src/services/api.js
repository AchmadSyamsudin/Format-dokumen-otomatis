/**
 * src/services/api.js
 * ====================
 * Fungsi-fungsi untuk berkomunikasi dengan backend FastAPI.
 * Semua request menggunakan axios dengan base URL dari .env.
 */

import axios from "axios";

// Base URL backend (bisa diubah via .env di frontend)
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000, // 2 menit (untuk dokumen besar / model inferensi)
});

// -------------------------------------------------------------------------
// Request Interceptor — Log request
// -------------------------------------------------------------------------
api.interceptors.request.use((config) => {
  console.debug(`[API] ${config.method?.toUpperCase()} ${config.url}`);
  return config;
});

// -------------------------------------------------------------------------
// Response Interceptor — Normalisasi error
// -------------------------------------------------------------------------
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      "Terjadi kesalahan yang tidak diketahui.";
    return Promise.reject(new Error(message));
  }
);

// -------------------------------------------------------------------------
// Templates API
// -------------------------------------------------------------------------

/**
 * Ambil daftar semua template (preset + user-created).
 * @returns {Promise<Array>} List template [{id, name, description, is_preset}]
 */
export async function listTemplates() {
  const res = await api.get("/api/templates/");
  return res.data;
}

/**
 * Ambil detail template berdasarkan ID (termasuk config lengkap).
 * @param {number} templateId
 * @returns {Promise<Object>} {id, name, description, is_preset, config}
 */
export async function getTemplate(templateId) {
  const res = await api.get(`/api/templates/${templateId}`);
  return res.data;
}

/**
 * Ekstrak template dari dokumen contoh dan simpan ke database.
 * @param {File} exampleFile - File .docx yang sudah diformat dengan benar
 * @param {string} templateName - Nama untuk template baru
 * @param {string} description - Deskripsi singkat
 * @returns {Promise<Object>} {template_id, name, config_preview, message}
 */
export async function extractTemplate(exampleFile, templateName, description = "") {
  const formData = new FormData();
  formData.append("example_file", exampleFile);
  formData.append("template_name", templateName);
  formData.append("description", description);

  const res = await api.post("/api/templates/extract", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

/**
 * Hapus template dari database.
 * @param {number} templateId
 * @returns {Promise<Object>} {message}
 */
export async function deleteTemplate(templateId) {
  const res = await api.delete(`/api/templates/${templateId}`);
  return res.data;
}

// -------------------------------------------------------------------------
// Documents API
// -------------------------------------------------------------------------

/**
 * Format dokumen menggunakan template preset (Standard Mode).
 * @param {File} targetFile - File .docx yang akan diformat
 * @param {number} templateId - ID template preset
 * @param {function} [onProgress] - Callback progress upload (opsional)
 * @returns {Promise<Object>} {task_id, status, message}
 */
export async function formatStandard(targetFile, templateId, onProgress) {
  const formData = new FormData();
  formData.append("target_file", targetFile);
  formData.append("template_id", templateId);

  const res = await api.post("/api/documents/format/standard", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded * 100) / e.total));
      }
    },
  });
  return res.data;
}

/**
 * Format dokumen menggunakan aturan dari dokumen contoh (Adaptive Mode).
 * @param {File} exampleFile - Dokumen contoh yang sudah diformat dengan benar
 * @param {File} targetFile  - Dokumen yang akan diformat
 * @param {string} templateName - Nama template yang akan disimpan
 * @param {boolean} saveTemplate - Simpan template ke database
 * @param {function} [onProgress] - Callback progress upload
 * @returns {Promise<Object>} {task_id, status, message}
 */
export async function formatAdaptive(
  exampleFile,
  targetFile,
  templateName = "Template Adaptif",
  saveTemplate = true,
  onProgress
) {
  const formData = new FormData();
  formData.append("example_file", exampleFile);
  formData.append("target_file", targetFile);
  formData.append("template_name", templateName);
  formData.append("save_template", saveTemplate);

  const res = await api.post("/api/documents/format/adaptive", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded * 100) / e.total));
      }
    },
  });
  return res.data;
}

/**
 * Cek status pemrosesan task.
 * @param {number} taskId
 * @returns {Promise<Object>} {task_id, status, mode, original_filename, output_available, error_msg}
 */
export async function getTaskStatus(taskId) {
  const res = await api.get(`/api/documents/${taskId}/status`);
  return res.data;
}

/**
 * Dapatkan URL download untuk hasil formatting.
 * @param {number} taskId
 * @returns {string} URL download langsung
 */
export function getDownloadUrl(taskId) {
  return `${BASE_URL}/api/documents/${taskId}/download`;
}

/**
 * Cek kesehatan backend.
 * @returns {Promise<Object>} {status, indobert_loaded, debug_mode}
 */
export async function healthCheck() {
  const res = await api.get("/health");
  return res.data;
}

export default api;
