"""
services/structure_classifier.py
====================================
LAYER 2 — IndoBERT Structure Classifier

Modul ini bertanggung jawab untuk mengklasifikasikan setiap paragraf
dokumen ke dalam satu label struktural menggunakan model IndoBERT
yang sudah di-fine-tune.

Label yang didukung:
    judul_bab | sub_bab | sub_sub_bab | isi | abstrak |
    caption_tabel | caption_gambar | daftar_poin | daftar_pustaka

Arsitektur:
    - Model: IndoBERT (encoder-only) → BertForSequenceClassification
    - Bukan generative LLM — ini adalah classifier dengan output label tetap
    - Inference 100% lokal/offline — TIDAK ada API call ke cloud AI

Dua mode operasi:
    1. MODEL_LOADED = True  → Inferensi menggunakan model IndoBERT fine-tuned
    2. MODEL_LOADED = False → Fallback ke heuristik (mode dev / model belum ada)

PENTING untuk skripsi:
    - Layer ini TERPISAH dari rule_based_extractor/formatter
    - Akurasi dan F1-score classifier ini dievaluasi secara independen
    - Jangan merge dengan rule-based layer
"""

import logging
from pathlib import Path
from typing import Optional

from utils.docx_utils import (
    get_paragraph_text,
    is_paragraph_empty,
    STRUCTURAL_LABELS,
    open_docx,
)
from services.rule_based_extractor import _heuristic_label

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Label mapping (indeks ↔ string)
# -------------------------------------------------------------------------

LABEL_LIST = STRUCTURAL_LABELS  # Ordered list — urutan ini HARUS sama dengan training

LABEL2ID: dict[str, int] = {label: i for i, label in enumerate(LABEL_LIST)}
ID2LABEL: dict[int, str] = {i: label for i, label in enumerate(LABEL_LIST)}


# -------------------------------------------------------------------------
# Classifier Class
# -------------------------------------------------------------------------

class StructureClassifier:
    """
    Wrapper untuk model IndoBERT fine-tuned yang mengklasifikasikan
    paragraf dokumen ke label struktural.

    Penggunaan:
        classifier = StructureClassifier(model_path=Path("./models/indobert_finetuned"))
        labels = classifier.classify_document(Path("dokumen.docx"))
        # labels = {0: "judul_bab", 1: "isi", 5: "sub_bab", ...}
    """

    def __init__(self, model_path: Optional[Path] = None, base_model: str = "indobenchmark/indobert-base-p1"):
        """
        Inisialisasi classifier. Coba load model fine-tuned dari disk.
        Jika tidak ada, masuk ke mode heuristik.

        Args:
            model_path: Path ke direktori model fine-tuned (output dari training)
            base_model: Nama model Hugging Face sebagai base (untuk referensi tokenizer)
        """
        self.model_path  = model_path
        self.base_model  = base_model
        self.model       = None
        self.tokenizer   = None
        self.is_loaded   = False
        self._device     = None

        self._try_load_model()

    def _try_load_model(self) -> None:
        """
        Coba muat model fine-tuned dari model_path.
        Jika gagal (file tidak ada, library tidak tersedia, dll.),
        set is_loaded = False dan gunakan heuristik.
        """
        if self.model_path is None or not self.model_path.exists():
            logger.warning(
                "Model IndoBERT tidak ditemukan di '%s'. "
                "Menggunakan heuristik fallback. "
                "Jalankan notebook fine-tuning untuk melatih model.",
                self.model_path,
            )
            return

        try:
            # Import transformers hanya saat model tersedia
            # Ini memastikan backend tetap berjalan meski transformers/torch tidak terinstall
            import torch
            from transformers import BertForSequenceClassification, BertTokenizerFast

            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info("IndoBERT akan berjalan di: %s", self._device)

            self.tokenizer = BertTokenizerFast.from_pretrained(str(self.model_path))
            self.model = BertForSequenceClassification.from_pretrained(
                str(self.model_path),
                num_labels=len(LABEL_LIST),
                id2label=ID2LABEL,
                label2id=LABEL2ID,
            )
            self.model.to(self._device)
            self.model.eval()  # Mode inferensi (non-training)

            self.is_loaded = True
            logger.info(
                "Model IndoBERT berhasil dimuat dari '%s'. Jumlah label: %d",
                self.model_path,
                len(LABEL_LIST),
            )

        except ImportError as exc:
            logger.error(
                "Library 'transformers' atau 'torch' tidak terinstall: %s. "
                "Jalankan: pip install transformers torch. "
                "Menggunakan heuristik fallback.",
                exc,
            )
        except Exception as exc:
            logger.error(
                "Gagal memuat model IndoBERT: %s. Menggunakan heuristik fallback.",
                exc,
            )

    def _predict_single(self, text: str) -> str:
        """
        Klasifikasikan satu teks paragraf menggunakan IndoBERT.

        Args:
            text: Teks paragraf (sudah di-strip)

        Returns:
            Label string
        """
        import torch

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=256,  # Max token IndoBERT; paragraf panjang akan di-truncate
        )
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits  = outputs.logits
            pred_id = int(torch.argmax(logits, dim=-1).item())

        return ID2LABEL[pred_id]

    def _predict_batch(self, texts: list[str], batch_size: int = 16) -> list[str]:
        """
        Klasifikasikan sekumpulan teks dalam batch (lebih efisien untuk dokumen panjang).

        Args:
            texts: List teks paragraf
            batch_size: Jumlah teks per batch

        Returns:
            List label string (urutan sama dengan input)
        """
        import torch

        all_labels = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            inputs = self.tokenizer(
                batch,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=256,
            )
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                pred_ids = torch.argmax(outputs.logits, dim=-1).tolist()

            all_labels.extend([ID2LABEL[pid] for pid in pred_ids])
            logger.debug(
                "Batch %d-%d selesai. Prediksi: %s",
                i, i + len(batch), all_labels[-len(batch):]
            )

        return all_labels

    def classify_document(self, doc_path: Path) -> dict[int, str]:
        """
        Klasifikasikan semua paragraf dalam dokumen .docx.

        Mengembalikan dict {indeks_paragraf: label} yang dapat langsung
        digunakan oleh rule_based_extractor dan rule_based_formatter.

        Args:
            doc_path: Path ke file .docx target

        Returns:
            Dict {int: str} — indeks paragraf → label struktural
            Hanya paragraf non-kosong yang ada di dict ini.

        Contoh output:
            {
                0: "judul_bab",    # "BAB I PENDAHULUAN"
                1: "isi",          # "Latar belakang penelitian ini..."
                5: "sub_bab",      # "1.1 Latar Belakang"
                6: "isi",          # "Perkembangan teknologi..."
                ...
            }
        """
        doc = open_docx(doc_path)

        # Kumpulkan paragraf non-kosong beserta indeksnya
        para_indices = []
        para_texts   = []
        for idx, para in enumerate(doc.paragraphs):
            if not is_paragraph_empty(para):
                para_indices.append(idx)
                para_texts.append(get_paragraph_text(para))

        if not para_texts:
            logger.warning("Dokumen tidak memiliki paragraf non-kosong: %s", doc_path)
            return {}

        logger.info(
            "Mengklasifikasikan %d paragraf dari '%s' menggunakan %s...",
            len(para_texts),
            doc_path.name,
            "IndoBERT model" if self.is_loaded else "heuristik fallback",
        )

        if self.is_loaded:
            # Gunakan IndoBERT model
            labels = self._predict_batch(para_texts)
        else:
            # Fallback heuristik (deterministik, bukan AI)
            labels = self._heuristic_classify_all(doc_path, para_indices)

        # Refinement deterministik untuk elemen cover/pengesahan yang tidak
        # menjadi label baru pada model lama.
        for position, idx in enumerate(para_indices):
            special_label = _heuristic_label(doc.paragraphs[idx])
            if special_label in {
                "cover_judul", "cover_identitas", "pengesahan_heading",
                "pengesahan_jabatan",
                "pengesahan_label", "pengesahan_tanda_tangan",
            }:
                labels[position] = special_label

        result = dict(zip(para_indices, labels))
        logger.info("Klasifikasi selesai. Distribusi label: %s", _count_labels(result))
        return result

    @staticmethod
    def _heuristic_classify_all(doc_path: Path, para_indices: list[int]) -> list[str]:
        """
        Jalankan heuristik untuk semua paragraf pada indeks tertentu.
        Digunakan sebagai fallback ketika model IndoBERT belum tersedia.

        Args:
            doc_path: Path ke dokumen
            para_indices: List indeks paragraf yang akan diklasifikasikan

        Returns:
            List label sesuai urutan para_indices
        """
        doc = open_docx(doc_path)
        labels = []
        for idx in para_indices:
            para  = doc.paragraphs[idx]
            label = _heuristic_label(para, para_index=idx) or "isi"
            labels.append(label)
        return labels


# -------------------------------------------------------------------------
# Helper
# -------------------------------------------------------------------------

def _count_labels(labelled: dict[int, str]) -> dict[str, int]:
    """Hitung distribusi label dari hasil klasifikasi."""
    counts: dict[str, int] = {}
    for label in labelled.values():
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))


# -------------------------------------------------------------------------
# Singleton — diinisialisasi sekali saat startup FastAPI
# -------------------------------------------------------------------------

_classifier_instance: Optional[StructureClassifier] = None


def get_classifier(
    model_path: Optional[Path] = None,
    base_model: str = "indobenchmark/indobert-base-p1",
) -> StructureClassifier:
    """
    Dapatkan singleton instance StructureClassifier.

    Model di-load SEKALI saat pertama kali dipanggil (lazy initialization).
    Ini mencegah model di-load ulang di setiap request.

    Dipanggil dari FastAPI lifespan event (startup) di main.py.

    Args:
        model_path: Path ke model fine-tuned
        base_model: Nama model Hugging Face base

    Returns:
        StructureClassifier instance
    """
    global _classifier_instance
    if _classifier_instance is None:
        logger.info("Menginisialisasi StructureClassifier (singleton)...")
        _classifier_instance = StructureClassifier(
            model_path=model_path,
            base_model=base_model,
        )
    return _classifier_instance
