"""
services/rule_based_extractor.py
==================================
LAYER 1 — Rule-Based Extractor (Deterministic, tanpa AI)

Modul ini bertanggung jawab untuk mengekstrak aturan format dari dokumen
.docx yang sudah diformat dengan benar (dokumen contoh).

Output utama:
    TemplateConfig (dict) — sesuai template_config_schema.json

Pipeline:
    1. Baca dokumen .docx menggunakan python-docx
    2. Baca margin halaman dari section
    3. Per paragraf: ambil label struktural (dari IndoBERT atau input manual)
       dan ekstrak properti format (font, size, spacing, alignment, dll.)
    4. Agregasi properti per label → tentukan nilai yang paling dominan (modus)
    5. Susun dan kembalikan TemplateConfig dict

PENTING: Modul ini TIDAK melakukan klasifikasi. Ia menerima label paragraf
         sebagai input, atau menebaknya menggunakan heuristik sederhana
         (mode pengembangan / fallback). Klasifikasi semantik sesungguhnya
         adalah tugas structure_classifier.py (Layer 2).
"""

import logging
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

from docx import Document

from utils.docx_utils import (
    open_docx,
    get_paragraph_text,
    is_paragraph_empty,
    get_effective_font_size,
    get_effective_font_name,
    get_effective_bold,
    get_alignment_str,
    get_line_spacing,
    get_line_spacing_rule,
    get_line_spacing_pt,
    get_space_before_after_pt,
    get_first_line_indent_cm,
    get_left_right_indent_cm,
    get_tab_stops,
    get_document_margins,
    has_numbering,
    STRUCTURAL_LABELS,
    SPECIAL_STRUCTURAL_LABELS,
)

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Type Aliases
# -------------------------------------------------------------------------

# Label → list properti per paragraf
LabelledSamples = dict[str, list[dict]]

# Konfigurasi format final
TemplateConfig = dict


# -------------------------------------------------------------------------
# Heuristic Labeler (Fallback — bukan AI)
# -------------------------------------------------------------------------

def _heuristic_label(paragraph) -> Optional[str]:
    """
    Tebak label struktural paragraf menggunakan aturan deterministik sederhana.

    CATATAN: Ini BUKAN pengganti IndoBERT. Ini hanya fallback untuk:
    (a) mode development sebelum model fine-tuned tersedia
    (b) paragraf yang terlalu ambigu untuk model

    Heuristik berdasarkan:
    - Ukuran font (heading biasanya lebih besar)
    - Bold status
    - Alignment (judul bab biasanya CENTER)
    - Panjang teks (judul singkat, isi panjang)
    - Numbering XML (daftar_poin)
    - Teks diawali kata kunci seperti "BAB", "Tabel", "Gambar"

    Args:
        paragraph: docx.text.paragraph.Paragraph

    Returns:
        Label string, atau None jika tidak bisa ditentukan
    """
    text = get_paragraph_text(paragraph)
    if not text:
        return None

    text_upper = text.upper().strip()
    font_size  = get_effective_font_size(paragraph)
    bold       = get_effective_bold(paragraph)
    alignment  = get_alignment_str(paragraph)

    if text_upper in {"LEMBAR PENGESAHAN", "LEMBAR PENGESAHAN:"}:
        return "pengesahan_heading"
    if "DOSEN PEMBIMBING LAPANGAN" in text_upper and "MAHASISWA" in text_upper:
        return "pengesahan_jabatan"
    if any(term in text_upper for term in ("NIP.", "NIM.", "TTD")):
        return "pengesahan_tanda_tangan"
    if any(term in text_upper for term in (
        "MENYETUJUI", "MENGETAHUI", "PEMBIMBING", "PENGUJI",
        "KETUA PROGRAM STUDI", "DEKAN",
    )):
        return "pengesahan_label"

    # --- Judul Bab ---
    # "BAB I", "BAB II", dll. — biasanya bold, center, font besar, ALL CAPS
    if (
        text_upper.startswith("BAB ")
        or (alignment == "CENTER" and bold and font_size and font_size >= 14)
        or (len(text) < 60 and bold and alignment == "CENTER")
    ):
        return "judul_bab"

    # --- Caption Tabel ---
    if text_upper.startswith("TABEL ") or text_upper.startswith("TABLE "):
        return "caption_tabel"

    # --- Caption Gambar ---
    if text_upper.startswith("GAMBAR ") or text_upper.startswith("FIGURE "):
        return "caption_gambar"

    if len(text) < 140 and any(term in text_upper for term in (
        "PROGRAM STUDI", "FAKULTAS", "UNIVERSITAS", "INSTITUT",
        "NAMA", "NIM", "TAHUN ",
    )):
        return "cover_identitas"
    if alignment == "CENTER" and len(text) < 160 and (
        text.isupper() or (bold and font_size and font_size >= 14)
    ):
        return "cover_judul"

    # --- Abstrak ---
    if "ABSTRAK" in text_upper or "ABSTRACT" in text_upper:
        if len(text) < 30:
            return "judul_bab"  # Judul halaman abstrak

    # --- Daftar Poin (list/bullet/numbered) ---
    if has_numbering(paragraph):
        return "daftar_poin"

    # --- Sub-Bab ---
    # Bold, pendek, tidak center
    if bold and font_size and 11 <= font_size <= 13 and len(text) < 80 and alignment != "CENTER":
        return "sub_bab"

    # --- Isi (default) ---
    if len(text) > 30:
        return "isi"

    return "isi"  # Default fallback


# -------------------------------------------------------------------------
# Extractor Utama
# -------------------------------------------------------------------------

def extract_paragraph_properties(paragraph) -> dict:
    """
    Ekstrak semua properti format dari satu paragraf.

    Menggunakan fungsi helper dari docx_utils yang membaca python-docx API
    secara proper (bukan regex / teks mentah).

    Args:
        paragraph: docx.text.paragraph.Paragraph

    Returns:
        Dict berisi properti format paragraf
    """
    space_before, space_after = get_space_before_after_pt(paragraph)

    left_indent_cm, right_indent_cm = get_left_right_indent_cm(paragraph)
    return {
        "font_family":          get_effective_font_name(paragraph),
        "font_size_pt":         get_effective_font_size(paragraph),
        "bold":                 get_effective_bold(paragraph),
        "alignment":            get_alignment_str(paragraph),
        "line_spacing":         get_line_spacing(paragraph),
        "line_spacing_rule":    get_line_spacing_rule(paragraph),
        "line_spacing_pt":      get_line_spacing_pt(paragraph),
        "space_before_pt":      space_before,
        "space_after_pt":       space_after,
        "first_line_indent_cm": get_first_line_indent_cm(paragraph),
        "left_indent_cm":       left_indent_cm,
        "right_indent_cm":      right_indent_cm,
        "tab_stops":             get_tab_stops(paragraph),
    }


def _majority_value(
    values: list,
    exclude: tuple = (),
    min_ratio: float = 0.5,
    treat_none_as: Optional[object] = None,
) -> Optional[object]:
    """
    Kembalikan nilai yang paling sering muncul dari sebuah list (modus),
    dengan mempertimbangkan proporsi terhadap TOTAL sampel (termasuk None).

    Args:
        values: List nilai
        exclude: Tuple nilai yang diabaikan
        min_ratio: Proporsi minimum dari total sampel agar nilai non-None menang (default 0.5)
        treat_none_as: Jika diisi, nilai None dianggap bernilai ini saat voting (misal 0.0 untuk indent)

    Returns:
        Nilai modus jika mencapai ambang batas, atau None / treat_none_as
    """
    if not values:
        return treat_none_as

    total_count = len(values)

    # Jika treat_none_as diberikan, transformasikan None ke nilai default tersebut
    if treat_none_as is not None:
        transformed = [treat_none_as if v is None else v for v in values]
        filtered = [v for v in transformed if v not in exclude]
        if not filtered:
            return treat_none_as
        counter = Counter(filtered)
        winner, count = counter.most_common(1)[0]
        if count / total_count >= min_ratio:
            return winner
        return treat_none_as

    # Jika treat_none_as is None:
    # Hanya nilai non-None yang valid untuk voting
    non_none = [v for v in values if v is not None and v not in exclude]
    if not non_none:
        return None

    counter = Counter(non_none)
    winner, count = counter.most_common(1)[0]

    # Ambang batas dihitung terhadap TOTAL sampel (termasuk sampel yang bernilai None)
    if count / total_count >= min_ratio:
        return winner

    return None


def _aggregate_style(samples: list[dict]) -> dict:
    """
    Agregasi properti format dari banyak sampel paragraf berlabel sama.

    Strategi: ambil nilai modus (nilai terbanyak) untuk setiap properti.
    Ini robust terhadap outlier/paragraf yang menyimpang.

    Args:
        samples: List dict properti paragraf (dari extract_paragraph_properties)

    Returns:
        Dict style yang sudah diagregasi (representatif untuk label ini)
    """
    if not samples:
        return {}

    keys = [
        "font_family", "font_size_pt", "bold",
        "alignment", "line_spacing",
        "line_spacing_rule", "line_spacing_pt",
        "space_before_pt", "space_after_pt",
        "first_line_indent_cm", "left_indent_cm", "right_indent_cm",
        "tab_stops",
    ]

    aggregated = {}
    for key in keys:
        values = [s.get(key) for s in samples]
        if key == "tab_stops":
            canonical = [
                tuple(
                    (item.get("position_cm"), item.get("alignment"), item.get("leader"))
                    for item in value
                )
                for value in values
                if value
            ]
            selected = _majority_value(canonical, min_ratio=0.5)
            aggregated[key] = (
                [
                    {
                        "position_cm": position,
                        "alignment": alignment,
                        "leader": leader,
                    }
                    for position, alignment, leader in selected
                ]
                if selected is not None
                else None
            )
        elif key in {"left_indent_cm", "right_indent_cm"}:
            # Untuk indent kiri/kanan, default Word style adalah 0.0 jika tidak ada override
            aggregated[key] = _majority_value(values, min_ratio=0.5, treat_none_as=0.0)
        else:
            aggregated[key] = _majority_value(values, min_ratio=0.5)

    # Round nilai numerik agar lebih bersih
    for num_key in ("font_size_pt", "line_spacing", "space_before_pt",
                    "space_after_pt", "first_line_indent_cm", "left_indent_cm", "right_indent_cm"):
        if aggregated.get(num_key) is not None:
            aggregated[num_key] = round(aggregated[num_key], 2)

    return aggregated


def extract_template_config(
    doc_path: Path,
    labelled_paragraphs: Optional[dict[int, str]] = None,
    template_name: str = "Template Diekstrak",
    description: str = "",
) -> TemplateConfig:
    """
    Fungsi utama: Ekstrak TemplateConfig dari dokumen .docx.

    Args:
        doc_path: Path ke file .docx dokumen contoh
        labelled_paragraphs: Dict {indeks_paragraf: label_struktural} dari IndoBERT.
            Jika None → gunakan heuristik fallback (mode dev).
        template_name: Nama template untuk disimpan ke database
        description: Deskripsi singkat template

    Returns:
        TemplateConfig dict sesuai template_config_schema.json

    Contoh penggunaan:
        config = extract_template_config(
            doc_path=Path("contoh_skripsi.docx"),
            labelled_paragraphs={0: "judul_bab", 1: "isi", 5: "sub_bab", ...}
        )
    """
    logger.info("Memulai ekstraksi template dari: %s", doc_path)

    doc: Document = open_docx(doc_path)

    # --- Margin Halaman ---
    margins = get_document_margins(doc)
    logger.debug("Margin halaman: %s", margins)

    # --- Ekstrak properti per paragraf, dikelompokkan per label ---
    # samples_by_label: label → list[dict properti]
    samples_by_label: LabelledSamples = defaultdict(list)

    using_heuristic = labelled_paragraphs is None
    if using_heuristic:
        logger.warning(
            "labelled_paragraphs tidak disediakan — menggunakan heuristik fallback. "
            "Hasil mungkin kurang akurat. Gunakan IndoBERT classifier untuk hasil optimal."
        )

    for idx, para in enumerate(doc.paragraphs):
        if is_paragraph_empty(para):
            continue  # Lewati paragraf kosong

        # Tentukan label
        if using_heuristic:
            label = _heuristic_label(para)
        else:
            label = labelled_paragraphs.get(idx)

        if label is None:
            logger.debug("Paragraf #%d tidak berlabel, dilewati.", idx)
            continue

        if label not in (*STRUCTURAL_LABELS, *SPECIAL_STRUCTURAL_LABELS):
            logger.warning("Label tidak dikenal '%s' pada paragraf #%d, dilewati.", label, idx)
            continue

        # Ekstrak properti
        props = extract_paragraph_properties(para)
        props["_text_sample"] = get_paragraph_text(para)[:80]  # Simpan cuplikan untuk debug
        samples_by_label[label].append(props)
        logger.debug("Paragraf #%d → label=%s | props=%s", idx, label, props)

    # --- Agregasi: satu style dict per label ---
    styles: dict[str, dict] = {}
    for label in (*STRUCTURAL_LABELS, *SPECIAL_STRUCTURAL_LABELS):
        samples = samples_by_label.get(label, [])
        if samples:
            styles[label] = _aggregate_style(samples)
            logger.info(
                "Label '%s': %d sampel ditemukan, style diagregasi: %s",
                label, len(samples), styles[label]
            )
        else:
            logger.debug("Label '%s': tidak ada sampel ditemukan.", label)

    # --- Hitung default_line_spacing dari paragraf "isi" ---
    default_line_spacing = 1.5  # Nilai default umum untuk dokumen akademik Indonesia
    if "isi" in styles and styles["isi"].get("line_spacing"):
        default_line_spacing = styles["isi"]["line_spacing"]

    # --- Susun TemplateConfig final ---
    config: TemplateConfig = {
        "version": "1.0",
        "name": template_name,
        "description": description or f"Diekstrak dari: {doc_path.name}",
        "margins": margins,
        "default_line_spacing": default_line_spacing,
        "styles": styles,
        "_meta": {
            "source_file": doc_path.name,
            "used_heuristic": using_heuristic,
            "total_paragraphs": len(doc.paragraphs),
            "labelled_paragraphs_count": sum(len(v) for v in samples_by_label.values()),
        },
    }

    logger.info(
        "Ekstraksi selesai. %d label berhasil diekstrak dari %d paragraf.",
        len(styles),
        config["_meta"]["labelled_paragraphs_count"],
    )
    return config
