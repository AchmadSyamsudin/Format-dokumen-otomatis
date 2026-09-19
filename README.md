# DocFormatAI — AI Document Formatting Agent

**Judul Skripsi:** Hybrid Rule-Based dan IndoBERT untuk Klasifikasi Struktur dan Penerapan Aturan Format Dokumen Karya Ilmiah Berbasis Data Template Adaptif

---

## Struktur Proyek

```
PROJEK/
├── backend/              # FastAPI + python-docx + IndoBERT
│   ├── main.py           # Entry point
│   ├── config.py         # Konfigurasi (baca dari .env)
│   ├── requirements.txt
│   ├── .env.example      # Template env vars (salin ke .env)
│   ├── models/           # SQLAlchemy database models
│   ├── routers/          # API endpoints (documents, templates)
│   ├── services/         # Business logic
│   │   ├── rule_based_extractor.py   # LAYER 1: Ekstrak aturan format
│   │   ├── rule_based_formatter.py   # LAYER 1: Terapkan aturan format
│   │   └── structure_classifier.py  # LAYER 2: IndoBERT classifier
│   ├── utils/            # Shared helpers (docx_utils)
│   └── schemas/          # JSON Schema dokumentasi
│
├── frontend/             # React + Vite
│   └── src/
│       ├── pages/        # Home, StandardMode, AdaptiveMode
│       ├── components/   # FileUploader, TemplateSelector, ProgressTracker, ResultPreview
│       └── services/     # api.js (axios calls)
│
├── data/
│   └── labeled_dataset/  # Dataset untuk IndoBERT fine-tuning
│       ├── train.jsonl   # Training data (format: {text, label})
│       └── README.md
│
├── notebooks/
│   └── indobert_finetuning.ipynb  # Notebook fine-tuning IndoBERT
│
└── copilot-instructions.md
```

---

## Quick Start

### Backend

```bash
cd backend

# 1. Salin dan konfigurasi .env
cp .env.example .env

# 2. Buat virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Jalankan server
uvicorn main:app --reload --port 8000
```

Backend tersedia di: http://localhost:8000
Swagger UI: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install     # (sudah dilakukan saat setup)
npm run dev
```

Frontend tersedia di: http://localhost:5173

---

## API Endpoints

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/` | Health check |
| GET | `/health` | Status IndoBERT |
| GET | `/api/templates/` | List semua template |
| POST | `/api/templates/extract` | Ekstrak template dari dokumen |
| GET | `/api/templates/{id}` | Detail template |
| DELETE | `/api/templates/{id}` | Hapus template |
| POST | `/api/documents/format/standard` | Format (Standard Mode) |
| POST | `/api/documents/format/adaptive` | Format (Adaptive Mode) |
| GET | `/api/documents/{id}/status` | Status task |
| GET | `/api/documents/{id}/download` | Download hasil |

---

## Arsitektur Pipeline

```
Dokumen .docx
    │
    ▼
[LAYER 2: IndoBERT Classifier]
  indobenchmark/indobert-base-p1 (fine-tuned)
  → Label setiap paragraf: judul_bab | sub_bab | isi | ...
    │
    ▼
[LAYER 1: Rule-Based Formatter]
  python-docx API (paragraph.style, run.font, paragraph_format)
  → Terapkan TemplateConfig ke setiap paragraf berdasarkan labelnya
    │
    ▼
Dokumen .docx (Formatted)
```

**PENTING:** Kedua layer TERPISAH dan dievaluasi secara independen di skripsi:
- Layer 1: Akurasi format (seberapa tepat aturan diterapkan)
- Layer 2: Accuracy & F1-score klasifikasi IndoBERT

---

## IndoBERT Fine-Tuning

1. Kumpulkan data → labeli → tambahkan ke `data/labeled_dataset/train.jsonl`
2. Buka `notebooks/indobert_finetuning.ipynb`
3. Jalankan semua cell
4. Model tersimpan di `backend/models/indobert_finetuned/`
5. Restart backend → model akan otomatis dimuat

**Tanpa model fine-tuned:** sistem tetap berjalan menggunakan heuristik fallback
(rule-based heuristic untuk klasifikasi sementara).

---

## Labels Struktural

| Label | Contoh |
|-------|--------|
| `judul_bab` | "BAB I PENDAHULUAN" |
| `sub_bab` | "1.1 Latar Belakang" |
| `sub_sub_bab` | "1.1.1 Perkembangan Teknologi" |
| `isi` | "Perkembangan teknologi informasi yang..." |
| `abstrak` | "Penelitian ini membahas tentang..." |
| `caption_tabel` | "Tabel 1. Distribusi Dataset..." |
| `caption_gambar` | "Gambar 1. Arsitektur Sistem..." |
| `daftar_poin` | "- Font: Times New Roman, 12pt" |
| `daftar_pustaka` | "Devlin, J., Chang, M. W., ..." |

---

## Catatan Pengembangan

- Semua inferensi AI berjalan **lokal/offline** — tidak ada cloud API calls
- `python-docx` API yang proper digunakan (bukan regex pada teks mentah)
- Rule-based dan AI layer **tidak boleh di-merge** (evaluasi terpisah di skripsi)
- IndoBERT adalah classifier (fixed label set), bukan generative LLM
