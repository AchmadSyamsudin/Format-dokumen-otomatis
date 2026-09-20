"""
utils/docx_utils.py
====================
Fungsi-fungsi helper bersama untuk pemrosesan file .docx.

Modul ini menyediakan utilitas low-level yang digunakan oleh
rule_based_extractor, rule_based_formatter, dan routers.

CATATAN: Semua operasi di sini menggunakan python-docx API yang proper
(paragraph.style, run.font, paragraph_format) — BUKAN regex atau
string-matching pada teks mentah.
"""

import hashlib
import logging
import uuid
from pathlib import Path
from typing import Optional

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Konstanta
# -------------------------------------------------------------------------

# Mapping nama alignment ke enum python-docx
ALIGNMENT_MAP: dict[str, WD_ALIGN_PARAGRAPH] = {
    "LEFT":    WD_ALIGN_PARAGRAPH.LEFT,
    "CENTER":  WD_ALIGN_PARAGRAPH.CENTER,
    "RIGHT":   WD_ALIGN_PARAGRAPH.RIGHT,
    "JUSTIFY": WD_ALIGN_PARAGRAPH.JUSTIFY,
}

# Mapping balik: enum → string
ALIGNMENT_REVERSE_MAP: dict[WD_ALIGN_PARAGRAPH, str] = {
    v: k for k, v in ALIGNMENT_MAP.items()
}

# Label struktural yang dikenal oleh sistem
STRUCTURAL_LABELS = [
    "judul_bab",
    "sub_bab",
    "sub_sub_bab",
    "isi",
    "abstrak",
    "caption_tabel",
    "caption_gambar",
    "daftar_poin",
    "daftar_pustaka",
]

SPECIAL_STRUCTURAL_LABELS = [
    "cover_judul",
    "cover_identitas",
    "pengesahan_heading",
    "pengesahan_jabatan",
    "pengesahan_label",
    "pengesahan_tanda_tangan",
]


# -------------------------------------------------------------------------
# File Utilities
# -------------------------------------------------------------------------

def open_docx(file_path: Path) -> Document:
    """
    Buka file .docx dan kembalikan objek Document.

    Args:
        file_path: Path ke file .docx

    Returns:
        Objek docx.Document

    Raises:
        FileNotFoundError: Jika file tidak ditemukan
        ValueError: Jika file bukan format .docx yang valid
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {file_path}")
    if file_path.suffix.lower() != ".docx":
        raise ValueError(f"File harus berformat .docx, bukan: {file_path.suffix}")
    try:
        return Document(str(file_path))
    except Exception as exc:
        raise ValueError(f"Gagal membuka file .docx: {exc}") from exc


def save_docx(doc: Document, output_path: Path) -> Path:
    """
    Simpan objek Document ke file .docx.

    Args:
        doc: Objek docx.Document
        output_path: Path tujuan penyimpanan

    Returns:
        Path file yang disimpan
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    logger.info("Dokumen disimpan ke: %s", output_path)
    return output_path


def generate_output_filename(original_name: str) -> str:
    """
    Buat nama file output berdasarkan nama file input.
    Contoh: 'laporan.docx' → 'laporan_formatted_<uid8>.docx'

    Args:
        original_name: Nama file asli (dengan atau tanpa ekstensi)

    Returns:
        String nama file output
    """
    stem = Path(original_name).stem
    uid = uuid.uuid4().hex[:8]
    return f"{stem}_formatted_{uid}.docx"


def compute_file_hash(file_path: Path) -> str:
    """
    Hitung SHA-256 hash dari file (untuk deduplikasi / integritas).

    Args:
        file_path: Path ke file

    Returns:
        String hex SHA-256
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


# -------------------------------------------------------------------------
# Paragraph Utilities
# -------------------------------------------------------------------------

def get_paragraph_text(paragraph) -> str:
    """
    Ambil teks bersih dari paragraf (gabungan semua run).

    Args:
        paragraph: docx.text.paragraph.Paragraph

    Returns:
        String teks paragraf
    """
    return "".join(run.text for run in paragraph.runs).strip()


def is_paragraph_empty(paragraph) -> bool:
    """
    Cek apakah paragraf kosong (tidak ada teks yang berarti).

    Args:
        paragraph: docx.text.paragraph.Paragraph

    Returns:
        True jika paragraf kosong
    """
    return get_paragraph_text(paragraph) == ""


def get_effective_font_size(paragraph) -> Optional[float]:
    """
    Ambil ukuran font efektif dari paragraf (dalam poin).
    Prioritas: run.font.size → paragraph.style.font.size → None

    Alasan tidak langsung ambil dari style: paragraph bisa override style.

    Args:
        paragraph: docx.text.paragraph.Paragraph

    Returns:
        Ukuran font dalam poin, atau None jika tidak terdefinisi
    """
    # Cek setiap run dalam paragraf
    for run in paragraph.runs:
        if run.font.size is not None:
            return run.font.size.pt  # Konversi dari EMU ke poin

    # Fallback ke style paragraf
    if paragraph.style and paragraph.style.font.size is not None:
        return paragraph.style.font.size.pt

    return None


def get_effective_font_name(paragraph) -> Optional[str]:
    """
    Ambil nama font efektif dari paragraf.
    Prioritas: run.font.name → paragraph.style.font.name → None

    Args:
        paragraph: docx.text.paragraph.Paragraph

    Returns:
        String nama font, atau None
    """
    for run in paragraph.runs:
        if run.font.name:
            return run.font.name

    if paragraph.style and paragraph.style.font.name:
        return paragraph.style.font.name

    return None


def get_effective_bold(paragraph) -> Optional[bool]:
    """
    Ambil status bold efektif dari paragraf.

    Args:
        paragraph: docx.text.paragraph.Paragraph

    Returns:
        True/False/None
    """
    for run in paragraph.runs:
        if run.bold is not None:
            return run.bold

    if paragraph.style and paragraph.style.font.bold is not None:
        return paragraph.style.font.bold

    return None


def get_alignment_str(paragraph) -> Optional[str]:
    """
    Ambil alignment paragraf sebagai string ("LEFT", "CENTER", "RIGHT", "JUSTIFY").

    Args:
        paragraph: docx.text.paragraph.Paragraph

    Returns:
        String alignment, atau None jika tidak terdefinisi
    """
    alignment = paragraph.alignment
    if alignment is None and paragraph.style:
        alignment = paragraph.style.paragraph_format.alignment

    return ALIGNMENT_REVERSE_MAP.get(alignment, None)


def get_line_spacing(paragraph) -> Optional[float]:
    """
    Ambil jarak baris paragraf.

    Line spacing bisa berupa:
    - WD_LINE_SPACING.MULTIPLE → nilai dalam `line_spacing` = faktor (e.g. 1.5)
    - WD_LINE_SPACING.EXACTLY / AT_LEAST → nilai dalam Pt

    Args:
        paragraph: docx.text.paragraph.Paragraph

    Returns:
        Faktor line spacing (float), atau None
    """
    pf = paragraph.paragraph_format

    # Coba dari paragraph_format langsung
    if pf.line_spacing is not None:
        ls = pf.line_spacing
        # Jika berupa Pt (EMU), konversi ke faktor berdasarkan 12pt standar
        # Untuk MULTIPLE, python-docx mengembalikan float langsung
        if isinstance(ls, float):
            return ls
        # Jika EMU (int besar), ini berarti mode EXACTLY/AT_LEAST
        if isinstance(ls, int) and ls > 1000:
            # Konversi EMU → poin, kemudian bagi 12pt (baseline)
            return round(ls / 914400 / 12, 2)  # 914400 EMU per inch, 72pt per inch

    # Fallback ke style
    if paragraph.style:
        pf_style = paragraph.style.paragraph_format
        if pf_style.line_spacing is not None:
            ls = pf_style.line_spacing
            if isinstance(ls, float):
                return ls

    return None


def get_line_spacing_rule(paragraph) -> Optional[str]:
    """Ambil mode line spacing sebagai nama enum Word."""
    rule = paragraph.paragraph_format.line_spacing_rule
    if rule is None:
        return None
    return getattr(rule, "name", str(rule).split(" ", 1)[0]).upper()


def get_line_spacing_pt(paragraph) -> Optional[float]:
    """Ambil line spacing absolut dalam poin untuk EXACTLY atau AT_LEAST."""
    rule = get_line_spacing_rule(paragraph)
    value = paragraph.paragraph_format.line_spacing
    if rule in {"EXACTLY", "AT_LEAST"} and value is not None and hasattr(value, "pt"):
        return round(value.pt, 2)
    return None


def get_space_before_after_pt(paragraph) -> tuple[Optional[float], Optional[float]]:
    """
    Ambil space before dan space after paragraf dalam poin.

    Returns:
        Tuple (space_before_pt, space_after_pt)
    """
    pf = paragraph.paragraph_format

    def to_pt(val) -> Optional[float]:
        if val is None:
            return None
        if hasattr(val, "pt"):
            return val.pt
        return None

    before = to_pt(pf.space_before)
    after  = to_pt(pf.space_after)

    # Fallback ke style
    if paragraph.style:
        pf_style = paragraph.style.paragraph_format
        if before is None:
            before = to_pt(pf_style.space_before)
        if after is None:
            after = to_pt(pf_style.space_after)

    return before, after


def get_first_line_indent_cm(paragraph) -> Optional[float]:
    """
    Ambil indentasi baris pertama dalam cm.

    Args:
        paragraph: docx.text.paragraph.Paragraph

    Returns:
        Indentasi dalam cm, atau None
    """
    pf = paragraph.paragraph_format
    indent = pf.first_line_indent

    if indent is None and paragraph.style:
        indent = paragraph.style.paragraph_format.first_line_indent

    if indent is not None:
        if hasattr(indent, "cm"):
            return round(indent.cm, 3)

    return None


def get_left_right_indent_cm(paragraph) -> tuple[Optional[float], Optional[float]]:
    """Ambil indentasi kiri dan kanan langsung dari paragraf."""
    pf = paragraph.paragraph_format

    def to_cm(value) -> Optional[float]:
        return round(value.cm, 3) if value is not None and hasattr(value, "cm") else None

    return to_cm(pf.left_indent), to_cm(pf.right_indent)


def get_hanging_indent_cm(paragraph) -> Optional[float]:
    """
    Deteksi dan kembalikan nilai hanging indent paragraf dalam cm.

    Dalam OOXML, hanging indent direpresentasikan sebagai atribut ``w:hanging``
    di elemen ``<w:ind>``. python-docx memetakan ini ke ``first_line_indent``
    dengan nilai **negatif** (misalnya -Cm(1.5)).

    Fungsi ini membaca langsung dari XML untuk mendapatkan nilai ``w:hanging``
    (bukan ``w:firstLine``), sehingga tidak ada ambiguitas tanda.

    Returns:
        Nilai hanging indent dalam cm (float positif), atau None jika paragraf
        tidak menggunakan pola hanging indent.
    """
    # Coba baca dari paragraf (override level)
    pPr = paragraph._p.find(qn("w:pPr"))
    if pPr is not None:
        ind = pPr.find(qn("w:ind"))
        if ind is not None:
            hanging_val = ind.get(qn("w:hanging"))
            if hanging_val is not None:
                try:
                    # Nilai dalam twips (1 cm = 567 twips)
                    return round(int(hanging_val) / 567, 3)
                except (ValueError, TypeError):
                    pass

    # Fallback: cek dari style paragraf (misal Heading2, Heading3)
    if paragraph.style:
        style_elm = paragraph.style.element
        pPr_style = style_elm.find(qn("w:pPr"))
        if pPr_style is not None:
            ind = pPr_style.find(qn("w:ind"))
            if ind is not None:
                hanging_val = ind.get(qn("w:hanging"))
                if hanging_val is not None:
                    try:
                        return round(int(hanging_val) / 567, 3)
                    except (ValueError, TypeError):
                        pass

    return None


def get_left_indent_for_hanging(paragraph) -> Optional[float]:
    """
    Ambil nilai ``w:left`` yang menyertai pola hanging indent dari XML.

    Saat paragraf menggunakan ``w:hanging``, nilai ``w:left`` di XML adalah
    total lebar inden (posisi teks baris ke-2+), bukan sekedar offset tambahan.
    python-docx API mengembalikan nilai ini via ``pf.left_indent``.

    Returns:
        Nilai left indent dalam cm (float), atau None.
    """
    # Baca dari paragraf level dulu (override)
    pPr = paragraph._p.find(qn("w:pPr"))
    if pPr is not None:
        ind = pPr.find(qn("w:ind"))
        if ind is not None:
            left_val = ind.get(qn("w:left"))
            if left_val is not None:
                try:
                    return round(int(left_val) / 567, 3)
                except (ValueError, TypeError):
                    pass

    # Fallback ke style
    if paragraph.style:
        style_elm = paragraph.style.element
        pPr_style = style_elm.find(qn("w:pPr"))
        if pPr_style is not None:
            ind = pPr_style.find(qn("w:ind"))
            if ind is not None:
                left_val = ind.get(qn("w:left"))
                if left_val is not None:
                    try:
                        return round(int(left_val) / 567, 3)
                    except (ValueError, TypeError):
                        pass

    return None


def get_tab_stops(paragraph) -> list[dict]:
    """Ambil tab stop eksplisit paragraf dalam format serializable."""
    stops = []
    for tab in paragraph.paragraph_format.tab_stops:
        stops.append({
            "position_cm": round(tab.position.cm, 3),
            "alignment": getattr(tab.alignment, "name", str(tab.alignment).split(" ", 1)[0]),
            "leader": getattr(tab.leader, "name", str(tab.leader).split(" ", 1)[0]),
        })
    return stops


# -------------------------------------------------------------------------
# Document-Level Utilities
# -------------------------------------------------------------------------

def get_document_margins(doc: Document) -> dict[str, float]:
    """
    Ambil margin halaman pertama dokumen dalam cm.

    Args:
        doc: docx.Document

    Returns:
        Dict dengan keys: top_cm, bottom_cm, left_cm, right_cm
    """
    try:
        section = doc.sections[0]
        return {
            "top_cm":    round(section.top_margin.cm, 2),
            "bottom_cm": round(section.bottom_margin.cm, 2),
            "left_cm":   round(section.left_margin.cm, 2),
            "right_cm":  round(section.right_margin.cm, 2),
        }
    except (IndexError, AttributeError) as exc:
        logger.warning("Gagal membaca margin dokumen: %s", exc)
        return {"top_cm": 4.0, "bottom_cm": 3.0, "left_cm": 4.0, "right_cm": 3.0}


def set_document_margins(doc: Document, margins: dict[str, float]) -> None:
    """
    Set margin halaman dokumen dalam cm.

    Args:
        doc: docx.Document
        margins: Dict dengan keys top_cm, bottom_cm, left_cm, right_cm
    """
    for section in doc.sections:
        section.top_margin    = Cm(margins.get("top_cm", 4.0))
        section.bottom_margin = Cm(margins.get("bottom_cm", 3.0))
        section.left_margin   = Cm(margins.get("left_cm", 4.0))
        section.right_margin  = Cm(margins.get("right_cm", 3.0))
    logger.debug("Margin diset: %s", margins)


def has_numbering(paragraph) -> bool:
    """
    Cek apakah paragraf memiliki numbering/list XML element.

    Args:
        paragraph: docx.text.paragraph.Paragraph

    Returns:
        True jika paragraf adalah item list
    """
    pPr = paragraph._p.find(qn("w:pPr"))
    if pPr is not None:
        numPr = pPr.find(qn("w:numPr"))
        return numPr is not None
    return False
