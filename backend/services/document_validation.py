"""Validasi pasca-formatting berbasis render PDF."""

import logging
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def _render_to_pdf(docx_path: Path, output_dir: Path) -> Path:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice is None:
        raise RuntimeError("LibreOffice (soffice) tidak ditemukan di PATH.")
    output_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(output_dir), str(docx_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "LibreOffice gagal merender dokumen.")
    pdf_path = output_dir / f"{docx_path.stem}.pdf"
    if not pdf_path.exists():
        raise RuntimeError(f"PDF hasil render tidak ditemukan: {pdf_path}")
    return pdf_path


def _count_pdf_pages(pdf_path: Path) -> int:
    data = pdf_path.read_bytes()
    pages = len(re.findall(rb"/Type\s*/Page\b", data))
    if pages < 1:
        raise RuntimeError(f"Tidak dapat membaca jumlah halaman PDF: {pdf_path}")
    return pages


def validate_page_count(
    original_docx: Path,
    formatted_docx: Path,
    threshold: float = 0.20,
) -> dict:
    """Render dua DOCX dan tandai perubahan jumlah halaman yang signifikan."""
    try:
        with tempfile.TemporaryDirectory(prefix="docx_validation_") as temp_dir:
            temp_path = Path(temp_dir)
            original_pdf = _render_to_pdf(original_docx, temp_path / "original")
            formatted_pdf = _render_to_pdf(formatted_docx, temp_path / "formatted")
            original_pages = _count_pdf_pages(original_pdf)
            formatted_pages = _count_pdf_pages(formatted_pdf)
    except (OSError, RuntimeError) as exc:
        logger.warning("Validasi halaman dilewati: %s", exc)
        return {"status": "unavailable", "warning": str(exc)}

    relative_delta = abs(formatted_pages - original_pages) / max(original_pages, 1)
    suspicious = relative_delta > threshold
    result = {
        "status": "warning" if suspicious else "ok",
        "original_pages": original_pages,
        "formatted_pages": formatted_pages,
        "relative_delta": round(relative_delta, 4),
    }
    if suspicious:
        result["warning"] = (
            f"Selisih halaman {relative_delta:.1%} melewati ambang {threshold:.0%}; "
            "periksa overflow akibat spacing atau indentasi."
        )
        logger.warning("%s", result["warning"])
    else:
        logger.info(
            "Validasi halaman OK: target=%d, hasil=%d, selisih=%.1f%%",
            original_pages, formatted_pages, relative_delta * 100,
        )
    return result
