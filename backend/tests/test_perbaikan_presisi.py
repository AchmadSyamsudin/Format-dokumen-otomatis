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
