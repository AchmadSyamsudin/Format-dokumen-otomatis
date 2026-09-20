"""
tests/test_perbaikan_presisi.py
===============================
Unit test untuk:
1. Perbaikan 1: Deteksi cover_judul untuk teks panjang (>160 karakter) di halaman cover.
2. Perbaikan 2: Agregasi hanging_indent_cm tanpa treat_none_as=0.0.
"""

import pytest
from unittest.mock import MagicMock, patch

from services.rule_based_extractor import _heuristic_label, _aggregate_style


def test_cover_judul_panjang_terdeteksi():
    """
    PERBAIKAN 1:
    Judul laporan dengan panjang > 160 karakter (misal 185 karakter)
    harus terdeteksi sebagai 'cover_judul' dan bukan 'isi' atau 'judul_bab'.
    """
    judul_185 = (
        "IMPLEMENTASI SISTEM MULTI-AGENT BERBASIS MODEL BAHASA INDONESIA INDOROBERTA "
        "UNTUK OTOMATISASI REFORMATTING DOKUMEN KARYA ILMIAH DALAM FORMAT MICROSOFT WORD "
        "MENGGUNAKAN PENDEKATAN HYBRID RULE-BASED DAN MACHINE LEARNING"
    )
    assert len(judul_185) >= 185

    para = MagicMock()
    para._p.pPr = MagicMock()
    para._p.pPr.pStyle = None

    with patch("services.rule_based_extractor.get_paragraph_text", return_value=judul_185), \
         patch("services.rule_based_extractor.get_effective_font_size", return_value=14.0), \
         patch("services.rule_based_extractor.get_effective_bold", return_value=True), \
         patch("services.rule_based_extractor.get_alignment_str", return_value="CENTER"), \
         patch("services.rule_based_extractor.has_numbering", return_value=False):
        label = _heuristic_label(para, para_index=2)
        assert label == "cover_judul"


def test_hanging_indent_cm_agregasi_mayoritas():
    """
    PERBAIKAN 2 (Kasus A):
    Jika sampel sub-bab memiliki hanging_indent_cm, nilai tersebut harus dipertahankan.
    """
    samples = [
        {"font_family": "Times New Roman", "font_size_pt": 12.0, "bold": True, "alignment": "LEFT",
         "hanging_indent_cm": 0.75, "left_indent_cm": 0.75, "right_indent_cm": 0.0},
        {"font_family": "Times New Roman", "font_size_pt": 12.0, "bold": True, "alignment": "LEFT",
         "hanging_indent_cm": 0.75, "left_indent_cm": 0.75, "right_indent_cm": 0.0},
    ]
    style = _aggregate_style(samples)
    assert style.get("hanging_indent_cm") == 0.75


def test_hanging_indent_cm_agregasi_mayoritas_none():
    """
    PERBAIKAN 2 (Kasus B):
    Jika hanya 2 dari 7 sampel yang punya hanging_indent_cm (sisanya None),
    hanging_indent_cm tidak boleh dipaksakan (harus None), dan tidak boleh jadi 0.0.
    """
    samples = [
        {"hanging_indent_cm": 0.75, "left_indent_cm": 0.75},
        {"hanging_indent_cm": 0.75, "left_indent_cm": 0.75},
        {"hanging_indent_cm": None, "left_indent_cm": 0.0},
        {"hanging_indent_cm": None, "left_indent_cm": 0.0},
        {"hanging_indent_cm": None, "left_indent_cm": 0.0},
        {"hanging_indent_cm": None, "left_indent_cm": 0.0},
        {"hanging_indent_cm": None, "left_indent_cm": 0.0},
    ]
    style = _aggregate_style(samples)
    assert style.get("hanging_indent_cm") is None


@pytest.mark.parametrize("text", [
    "Koordinator Program Studi",
    "Koordinator Program Studi Sistem Informasi",
    "Koordinator Prodi Teknik Informatika",
    "Ketua Prodi",
    "Ketua Program Studi",
    "Kaprodi Sistem Informasi",
    "Menyetujui,",
    "Mengetahui,",
    "Dosen Pembimbing",
    "Dosen Penguji",
    "Dekan Fakultas Ilmu Komputer",
])
def test_pengesahan_label_keywords(text):
    """
    PERBAIKAN 1:
    Kata kunci variasi pengesahan seperti 'KOORDINATOR', 'KAPRODI', 'KETUA PRODI',
    harus terdeteksi sebagai 'pengesahan_label' bukan 'isi'.
    """
    para = MagicMock()
    para._p.pPr = MagicMock()
    para._p.pPr.pStyle = None

    with patch("services.rule_based_extractor.get_paragraph_text", return_value=text), \
         patch("services.rule_based_extractor.get_effective_font_size", return_value=12.0), \
         patch("services.rule_based_extractor.get_effective_bold", return_value=False), \
         patch("services.rule_based_extractor.get_alignment_str", return_value="CENTER"), \
         patch("services.rule_based_extractor.has_numbering", return_value=False):
        label = _heuristic_label(para, para_index=40)
        assert label == "pengesahan_label"


def test_hanging_indent_rounding_unifies_split_votes():
    """
    PERBAIKAN 2:
    109 sampel sub_bab: 90 sampel hanging indent yang aslinya terbelah 45/45
    antara 0.7496 (425 twips) dan 0.7513 (426 twips).
    Dengan pembulatan 1 desimal (0.8), semua 90 sampel (82.6%) bersatu dan mencapai
    ambang batas mayoritas (>= 50%), menghasilkan hanging_indent_cm = 0.8.
    """
    from services.rule_based_extractor import extract_paragraph_properties

    # Simulasi 45 sampel dari 425 twips dan 45 sampel dari 426 twips
    samples = []
    # 45 sampel dari 425 twips -> 0.8
    for _ in range(45):
        samples.append({
            "hanging_indent_cm": round(round(425 / 567, 2), 1),
            "left_indent_cm": round(round(425 / 567, 2), 1),
            "right_indent_cm": 0.0,
        })
    # 45 sampel dari 426 twips -> 0.8
    for _ in range(45):
        samples.append({
            "hanging_indent_cm": round(round(426 / 567, 2), 1),
            "left_indent_cm": round(round(426 / 567, 2), 1),
            "right_indent_cm": 0.0,
        })
    # 19 sampel tanpa hanging (None)
    for _ in range(19):
        samples.append({
            "hanging_indent_cm": None,
            "left_indent_cm": 0.0,
            "right_indent_cm": 0.0,
        })

    assert len(samples) == 109
    style = _aggregate_style(samples)
    assert style.get("hanging_indent_cm") == 0.8


def test_extract_paragraph_properties_rounds_to_1dec():
    """
    PERBAIKAN 2:
    Pastikan extract_paragraph_properties membulatkan properti indentasi
    (first_line, hanging, left, right) ke 1 desimal.
    """
    from services.rule_based_extractor import extract_paragraph_properties

    para = MagicMock()
    with patch("services.rule_based_extractor.get_effective_font_name", return_value="Times New Roman"), \
         patch("services.rule_based_extractor.get_effective_font_size", return_value=12.0), \
         patch("services.rule_based_extractor.get_effective_bold", return_value=False), \
         patch("services.rule_based_extractor.get_alignment_str", return_value="LEFT"), \
         patch("services.rule_based_extractor.get_line_spacing", return_value=1.5), \
         patch("services.rule_based_extractor.get_line_spacing_rule", return_value="MULTIPLE"), \
         patch("services.rule_based_extractor.get_line_spacing_pt", return_value=None), \
         patch("services.rule_based_extractor.get_space_before_after_pt", return_value=(0.0, 6.0)), \
         patch("services.rule_based_extractor.get_left_right_indent_cm", return_value=(0.7513, 0.248)), \
         patch("services.rule_based_extractor.get_hanging_indent_cm", return_value=0.7496), \
         patch("services.rule_based_extractor.get_left_indent_for_hanging", return_value=0.7496), \
         patch("services.rule_based_extractor.get_tab_stops", return_value=[]):
        props = extract_paragraph_properties(para)
        assert props["hanging_indent_cm"] == 0.8
        assert props["left_indent_cm"] == 0.8
        assert props["right_indent_cm"] == 0.2
        assert props["first_line_indent_cm"] is None

