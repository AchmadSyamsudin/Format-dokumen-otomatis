"""
tests/test_majority_value.py
============================
Unit test untuk memvalidasi fungsi _majority_value() dan _aggregate_style()
pada services/rule_based_extractor.py, khususnya penanganan nilai None dan
pencegahan outlier memenangkan voting (kasus right_indent_cm=293).
"""

import pytest
from services.rule_based_extractor import _majority_value, _aggregate_style


def test_majority_value_six_none_one_293_without_treat_none():
    """
    Kasus spesifik dari instruksi:
    6 sampel None + 1 sampel bernilai 293.
    Nilai non-None (293) hanya merepresentasikan 1/7 (~14%) dari total sampel.
    Dengan ambang batas proporsi default 50%, nilai 293 TIDAK boleh menang.
    Hasil yang diharapkan adalah None, BUKAN 293.
    """
    samples = [None, None, None, None, None, None, 293]
    result = _majority_value(samples)
    assert result is None
    assert result != 293


def test_majority_value_six_none_one_293_with_treat_none_zero():
    """
    Kasus spesifik untuk properti indentasi:
    Jika None di-treat sebagai eksplisit 0 (default Word style),
    maka 0 muncul 6 kali dan 293 muncul 1 kali.
    Hasil yang diharapkan adalah 0 (atau 0.0), BUKAN 293.
    """
    samples = [None, None, None, None, None, None, 293]
    result = _majority_value(samples, treat_none_as=0)
    assert result == 0
    assert result != 293


def test_majority_value_clear_majority():
    """
    Kasus normal: Mayoritas sampel bernilai 12.0
    """
    samples = [12.0, 12.0, 12.0, 12.0, 14.0]
    result = _majority_value(samples)
    assert result == 12.0


def test_majority_value_non_none_majority_with_some_none():
    """
    Kasus: 4 sampel 'Times New Roman' dan 2 sampel None (total 6 sampel).
    4/6 = 66.7% (>= 50%), sehingga 'Times New Roman' harus menang.
    """
    samples = ["Times New Roman", "Times New Roman", "Times New Roman", "Times New Roman", None, None]
    result = _majority_value(samples)
    assert result == "Times New Roman"


def test_majority_value_all_none():
    """
    Kasus: Semua sampel bernilai None.
    """
    samples = [None, None, None, None]
    assert _majority_value(samples) is None
    assert _majority_value(samples, treat_none_as=0.0) == 0.0


def test_majority_value_empty():
    """
    Kasus: List kosong.
    """
    assert _majority_value([]) is None
    assert _majority_value([], treat_none_as=0.0) == 0.0


def test_aggregate_style_prevents_indent_outlier():
    """
    Verifikasi bahwa _aggregate_style() menghasilkan right_indent_cm bernilai 0.0
    (atau None) dan TIDAK 293 ketika ada 6 paragraf None dan 1 paragraf outlier 293.
    """
    samples = [
        {"font_size_pt": 12.0, "bold": True, "right_indent_cm": None},
        {"font_size_pt": 12.0, "bold": True, "right_indent_cm": None},
        {"font_size_pt": 12.0, "bold": True, "right_indent_cm": None},
        {"font_size_pt": 12.0, "bold": True, "right_indent_cm": None},
        {"font_size_pt": 12.0, "bold": True, "right_indent_cm": None},
        {"font_size_pt": 12.0, "bold": True, "right_indent_cm": None},
        {"font_size_pt": 14.0, "bold": True, "right_indent_cm": 293.0},
    ]
    style = _aggregate_style(samples)
    assert style["right_indent_cm"] != 293.0
    assert style["right_indent_cm"] in (0.0, 0, None)
    assert style["font_size_pt"] == 12.0
    assert style["bold"] is True
