"""
utils/__init__.py
"""

from .docx_utils import (
    open_docx,
    save_docx,
    generate_output_filename,
    get_paragraph_text,
    is_paragraph_empty,
    get_effective_font_size,
    get_effective_font_name,
    get_effective_bold,
    get_alignment_str,
    get_line_spacing,
    get_space_before_after_pt,
    get_first_line_indent_cm,
    get_document_margins,
    set_document_margins,
    has_numbering,
    STRUCTURAL_LABELS,
    ALIGNMENT_MAP,
)

__all__ = [
    "open_docx", "save_docx", "generate_output_filename",
    "get_paragraph_text", "is_paragraph_empty",
    "get_effective_font_size", "get_effective_font_name", "get_effective_bold",
    "get_alignment_str", "get_line_spacing", "get_space_before_after_pt",
    "get_first_line_indent_cm", "get_document_margins", "set_document_margins",
    "has_numbering", "STRUCTURAL_LABELS", "ALIGNMENT_MAP",
]
