"""
services/rule_based_formatter.py
==================================
LAYER 1 — Rule-Based Formatter (Deterministic, tanpa AI)

Modul ini bertanggung jawab untuk menerapkan TemplateConfig ke dokumen target.

Pipeline:
    1. Buka dokumen target (.docx)
    2. Terapkan margin halaman sesuai TemplateConfig
    3. Per paragraf: dapatkan label struktural dari IndoBERT (atau heuristik)
    4. Temukan aturan format untuk label tersebut di TemplateConfig
    5. Terapkan aturan ke paragraf menggunakan python-docx API
    6. Simpan dokumen hasil ke output_path

PENTING:
    - Modul ini TIDAK mengubah konten/teks dokumen, hanya format/style-nya.
    - Setiap perubahan menggunakan python-docx API yang proper:
      paragraph.paragraph_format, run.font, section.margin — BUKAN XML manual.
    - Paragraf tanpa label (None) atau label tidak ada di config → DILEWATI
      (format asli paragraf dipertahankan).
"""

import logging
from pathlib import Path
from typing import Optional

from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_LINE_SPACING
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml.ns import qn

from utils.docx_utils import (
    open_docx,
    save_docx,
    get_paragraph_text,
    is_paragraph_empty,
    set_document_margins,
    ALIGNMENT_MAP,
)

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# Core: Terapkan style ke satu paragraf
# -------------------------------------------------------------------------

def apply_style_to_paragraph(paragraph, style_config: dict) -> None:
    """
    Terapkan satu style config ke satu paragraf.

    Mengubah properti format paragraf menggunakan python-docx API yang proper.
    Hanya properti yang terdefinisi (tidak None) di style_config yang diubah.

    Args:
        paragraph: docx.text.paragraph.Paragraph — paragraf target
        style_config: Dict berisi properti format sesuai ParagraphStyle schema
    """
    p_pr = paragraph._p.get_or_add_pPr()
    numbering = p_pr.find(qn("w:numPr"))
    for child in list(p_pr):
        if child is not numbering:
            p_pr.remove(child)
    pf = paragraph.paragraph_format

    # --- Alignment ---
    alignment_str = style_config.get("alignment")
    if alignment_str and alignment_str in ALIGNMENT_MAP:
        pf.alignment = ALIGNMENT_MAP[alignment_str]
        logger.debug("  alignment → %s", alignment_str)

    # --- Line Spacing ---
    line_spacing_rule = style_config.get("line_spacing_rule")
    line_spacing = style_config.get("line_spacing")
    line_spacing_pt = style_config.get("line_spacing_pt")
    if line_spacing_rule == "EXACTLY" and line_spacing_pt is not None:
        pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        pf.line_spacing = Pt(line_spacing_pt)
    elif line_spacing_rule == "AT_LEAST" and line_spacing_pt is not None:
        pf.line_spacing_rule = WD_LINE_SPACING.AT_LEAST
        pf.line_spacing = Pt(line_spacing_pt)
    elif line_spacing is not None:
        pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        pf.line_spacing = line_spacing

    # --- Space Before / After ---
    space_before_pt = style_config.get("space_before_pt")
    if space_before_pt is not None:
        pf.space_before = Pt(space_before_pt)
        logger.debug("  space_before → %.1f pt", space_before_pt)

    space_after_pt = style_config.get("space_after_pt")
    if space_after_pt is not None:
        pf.space_after = Pt(space_after_pt)
        logger.debug("  space_after → %.1f pt", space_after_pt)

    # --- First Line Indent ---
    first_line_indent_cm = style_config.get("first_line_indent_cm")
    if first_line_indent_cm is not None:
        pf.first_line_indent = Cm(first_line_indent_cm)

    # --- Left Indent ---
    left_indent_cm = style_config.get("left_indent_cm")
    if left_indent_cm is not None:
        pf.left_indent = Cm(left_indent_cm)

    right_indent_cm = style_config.get("right_indent_cm")
    if right_indent_cm is not None:
        pf.right_indent = Cm(right_indent_cm)

    tab_stops = style_config.get("tab_stops")
    if tab_stops:
        alignment_map = {
            "LEFT": WD_TAB_ALIGNMENT.LEFT,
            "CENTER": WD_TAB_ALIGNMENT.CENTER,
            "RIGHT": WD_TAB_ALIGNMENT.RIGHT,
            "DECIMAL": WD_TAB_ALIGNMENT.DECIMAL,
            "BAR": WD_TAB_ALIGNMENT.BAR,
            "LIST": WD_TAB_ALIGNMENT.LIST,
        }
        leader_map = {
            "SPACES": WD_TAB_LEADER.SPACES,
            "DOTS": WD_TAB_LEADER.DOTS,
            "DASHES": WD_TAB_LEADER.DASHES,
            "LINES": WD_TAB_LEADER.LINES,
            "HEAVY": WD_TAB_LEADER.HEAVY,
            "MIDDLE_DOT": WD_TAB_LEADER.MIDDLE_DOT,
        }
        for tab in tab_stops:
            position_cm = tab.get("position_cm")
            if position_cm is None:
                continue
            pf.tab_stops.add_tab_stop(
                Cm(position_cm),
                alignment=alignment_map.get(tab.get("alignment", "LEFT"), WD_TAB_ALIGNMENT.LEFT),
                leader=leader_map.get(tab.get("leader", "SPACES"), WD_TAB_LEADER.SPACES),
            )

    # --- Font properties (per run) ---
    # Harus diterapkan ke setiap run karena run bisa override paragraph style
    font_family  = style_config.get("font_family")
    font_size_pt = style_config.get("font_size_pt")
    bold         = style_config.get("bold")
    italic       = style_config.get("italic")
    underline    = style_config.get("underline")
    all_caps     = style_config.get("all_caps")

    for run in paragraph.runs:
        if font_family:
            run.font.name = font_family
            logger.debug("  run.font.name → %s", font_family)

        if font_size_pt is not None:
            run.font.size = Pt(font_size_pt)
            logger.debug("  run.font.size → %.1f pt", font_size_pt)

        if bold is not None:
            run.bold = bold

        if italic is not None:
            run.italic = italic

        if underline is not None:
            run.underline = underline

        if all_caps is not None:
            run.font.all_caps = all_caps


# -------------------------------------------------------------------------
# Core: Format seluruh dokumen
# -------------------------------------------------------------------------

def format_document(
    input_path: Path,
    output_path: Path,
    template_config: dict,
    labelled_paragraphs: Optional[dict[int, str]] = None,
) -> Path:
    """
    Fungsi utama: Terapkan TemplateConfig ke dokumen target dan simpan hasilnya.

    Args:
        input_path: Path ke dokumen .docx yang akan diformat
        output_path: Path tujuan untuk dokumen yang sudah diformat
        template_config: Dict TemplateConfig sesuai template_config_schema.json
        labelled_paragraphs: Dict {indeks_paragraf: label_struktural}.
            Berasal dari IndoBERT classifier (structure_classifier.py).
            Jika None → gunakan heuristik fallback (mode dev).

    Returns:
        Path ke file output yang sudah disimpan

    Raises:
        FileNotFoundError: Jika input_path tidak ditemukan
        KeyError: Jika template_config tidak memiliki key yang diperlukan
    """
    logger.info("Memulai formatting: %s → %s", input_path, output_path)

    doc: Document = open_docx(input_path)

    # --- 1. Terapkan Margin Halaman ---
    margins = template_config.get("margins", {})
    if margins:
        set_document_margins(doc, margins)
        logger.info("Margin diterapkan: %s", margins)

    # --- 2. Siapkan style dict dari config ---
    styles: dict[str, dict] = template_config.get("styles", {})
    default_line_spacing = template_config.get("default_line_spacing", 1.5)

    # Logging debug (2): Cek apakah key "pengesahan_heading" ada di styles dict hasil ekstraksi
    has_pengesahan_heading = "pengesahan_heading" in styles
    logger.info(
        "[DEBUG PENGESAHAN] (2) Apakah key 'pengesahan_heading' ada di styles dict FILE REFERENSI? %s (Total style keys: %d, keys: %s)",
        has_pengesahan_heading,
        len(styles),
        list(styles.keys()),
    )

    # Inject default_line_spacing ke style "isi" jika belum ada
    if "isi" in styles and styles["isi"].get("line_spacing") is None:
        styles["isi"]["line_spacing"] = default_line_spacing

    # --- 3. Tentukan apakah menggunakan heuristik ---
    using_heuristic = labelled_paragraphs is None
    if using_heuristic:
        logger.warning(
            "labelled_paragraphs tidak diberikan — menggunakan heuristik fallback. "
            "Gunakan IndoBERT classifier untuk hasil yang lebih akurat."
        )
        # Import di sini untuk menghindari circular import
        from services.rule_based_extractor import _heuristic_label

    # --- 4. Iterasi dan format setiap paragraf ---
    stats = {"formatted": 0, "skipped_empty": 0, "skipped_no_label": 0, "skipped_no_style": 0}

    for idx, para in enumerate(doc.paragraphs):
        para_text = get_paragraph_text(para)

        # Lewati paragraf kosong
        if is_paragraph_empty(para):
            stats["skipped_empty"] += 1
            continue

        # Dapatkan label paragraf
        if using_heuristic:
            label = _heuristic_label(para)
        else:
            label = labelled_paragraphs.get(idx)

        # Logging debug (1): Cek label yang ter-assign untuk tiap paragraf yang mengandung "LEMBAR PENGESAHAN"
        if "LEMBAR PENGESAHAN" in para_text.upper():
            logger.info(
                "[DEBUG PENGESAHAN] (1) Paragraf #%d mengandung 'LEMBAR PENGESAHAN'. Teks: %r | Assigned label: %r | Ada di styles: %s",
                idx,
                para_text.strip(),
                label,
                (label in styles) if label else False,
            )

        if label is None:
            stats["skipped_no_label"] += 1
            logger.debug("Paragraf #%d: tidak berlabel, dilewati.", idx)
            continue

        # Cari style di config
        style_config = styles.get(label)
        if style_config is None:
            # Penanganan khusus: Jika label pengesahan_heading tapi tidak ada style spesifik,
            # tetap berikan page_break_before & keep_with_next, serta fallback ke style judul_bab
            if label == "pengesahan_heading":
                logger.info(
                    "[DEBUG PENGESAHAN] Paragraf #%d [%s] tidak ada di styles. Menerapkan page_break_before & keep_with_next dengan fallback ke judul_bab.",
                    idx, label
                )
                if "judul_bab" in styles:
                    apply_style_to_paragraph(para, styles["judul_bab"])
                para.paragraph_format.page_break_before = True
                para.paragraph_format.keep_with_next = True
                next_idx = idx + 1
                if next_idx < len(doc.paragraphs) and is_paragraph_empty(doc.paragraphs[next_idx]):
                    doc.paragraphs[next_idx].paragraph_format.keep_with_next = True
                stats["formatted"] += 1
                continue

            stats["skipped_no_style"] += 1
            logger.debug(
                "Paragraf #%d: label '%s' tidak ada di config, dilewati.",
                idx, label
            )
            continue

        # Terapkan style
        text_preview = para_text[:50]
        logger.debug("Paragraf #%d [%s]: '%s...'", idx, label, text_preview)
        apply_style_to_paragraph(para, style_config)
        if label == "pengesahan_heading":
            para.paragraph_format.page_break_before = True
            para.paragraph_format.keep_with_next = True
            next_idx = idx + 1
            if next_idx < len(doc.paragraphs) and is_paragraph_empty(doc.paragraphs[next_idx]):
                doc.paragraphs[next_idx].paragraph_format.keep_with_next = True
        stats["formatted"] += 1

    logger.info(
        "Formatting selesai. Stats: %d diformat | %d kosong | "
        "%d tanpa label | %d tanpa style di config",
        stats["formatted"],
        stats["skipped_empty"],
        stats["skipped_no_label"],
        stats["skipped_no_style"],
    )

    # --- 5. Simpan dokumen hasil ---
    return save_docx(doc, output_path)


# -------------------------------------------------------------------------
# Convenience: Standard Mode
# -------------------------------------------------------------------------

def format_with_preset(
    input_path: Path,
    output_path: Path,
    preset_config: dict,
    labelled_paragraphs: Optional[dict[int, str]] = None,
) -> Path:
    """
    Shortcut untuk Standard Template Mode.
    Memanggil format_document dengan preset config yang sudah tersedia.

    Args:
        input_path: Path dokumen target
        output_path: Path output
        preset_config: TemplateConfig preset bawaan sistem
        labelled_paragraphs: Label dari IndoBERT (opsional)

    Returns:
        Path output yang sudah disimpan
    """
    logger.info(
        "Standard mode: menerapkan preset '%s' ke %s",
        preset_config.get("name", "Unnamed"),
        input_path.name,
    )
    return format_document(input_path, output_path, preset_config, labelled_paragraphs)


def format_with_adaptive(
    input_path: Path,
    output_path: Path,
    extracted_config: dict,
    labelled_paragraphs: Optional[dict[int, str]] = None,
) -> Path:
    """
    Shortcut untuk Adaptive Learning Mode.
    Memanggil format_document dengan config yang diekstrak dari dokumen contoh.

    Args:
        input_path: Path dokumen target
        output_path: Path output
        extracted_config: TemplateConfig hasil ekstraksi (dari rule_based_extractor)
        labelled_paragraphs: Label dari IndoBERT (opsional)

    Returns:
        Path output yang sudah disimpan
    """
    logger.info(
        "Adaptive mode: menerapkan config '%s' ke %s",
        extracted_config.get("name", "Unnamed"),
        input_path.name,
    )
    return format_document(input_path, output_path, extracted_config, labelled_paragraphs)
