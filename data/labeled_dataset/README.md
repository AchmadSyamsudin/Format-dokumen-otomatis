# Dataset Labeled — IndoBERT Fine-Tuning

Direktori ini berisi dataset terlabel untuk fine-tuning model IndoBERT
sebagai classifier struktural paragraf dokumen akademik Indonesia.

## Format Data

File: `train.jsonl`, `val.jsonl`, `test.jsonl`

Setiap baris adalah satu JSON object:
```json
{"text": "...", "label": "judul_bab"}
```

### Label yang Digunakan

| Label           | Deskripsi                                      |
|-----------------|------------------------------------------------|
| `judul_bab`     | Judul bab utama (BAB I, BAB II, dll.)          |
| `sub_bab`       | Sub-bab (1.1 Latar Belakang, dst.)             |
| `sub_sub_bab`   | Sub-sub-bab (1.1.1 ...)                        |
| `isi`           | Paragraf isi/konten utama                      |
| `abstrak`       | Paragraf abstrak / abstract                    |
| `caption_tabel` | Caption / keterangan tabel                     |
| `caption_gambar`| Caption / keterangan gambar                    |
| `daftar_poin`   | Item daftar / bullet list / numbered list      |
| `daftar_pustaka`| Entri daftar pustaka / referensi               |

## Cara Menambah Data

1. Buka dokumen skripsi / laporan akhir yang sudah ada
2. Copy teks per paragraf ke file CSV/JSONL dengan label yang sesuai
3. Atau gunakan script semi-otomatis: `../../scripts/label_helper.py` (jika tersedia)

## Distribusi Target

Minimal **200 sampel per label** untuk fine-tuning yang baik.
Usahakan **balanced** antar label (tidak terlalu timpang).

## Split

- `train.jsonl` — 80% untuk training
- `val.jsonl`   — 10% untuk validasi selama training
- `test.jsonl`  — 10% untuk evaluasi akhir (F1 score per label)

## Evaluasi

Jalankan notebook: `../../notebooks/indobert_finetuning.ipynb`

Metrik yang dilaporkan di skripsi:
- Accuracy keseluruhan
- F1-score per label (macro average)
- Confusion matrix
