"""
routers/documents.py
======================
Endpoint API untuk pemrosesan dokumen (upload, format, download).

Endpoint:
    POST /api/documents/format/standard   — Format dengan template preset
    POST /api/documents/format/adaptive   — Adaptive mode (contoh + target)
    GET  /api/documents/{task_id}/status  — Cek status task
    GET  /api/documents/{task_id}/download— Download hasil formatting
"""

import logging
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import aiofiles

from config import settings
from models.database import FormattingTask, TemplateConfig, get_db
from services.rule_based_extractor import extract_template_config
from services.rule_based_formatter import format_with_preset, format_with_adaptive
from services.structure_classifier import get_classifier
from services.document_validation import validate_page_count
from utils.docx_utils import generate_output_filename

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


# -------------------------------------------------------------------------
# Response Schemas (Pydantic)
# -------------------------------------------------------------------------

class TaskStatusResponse(BaseModel):
    task_id: int
    status:  str         # pending | processing | done | failed
    mode:    str         # standard | adaptive
    original_filename: str
    output_available:  bool
    error_msg: Optional[str] = None


class FormatResponse(BaseModel):
    task_id:  int
    status:   str
    message:  str


# -------------------------------------------------------------------------
# Helper: Simpan file upload ke storage
# -------------------------------------------------------------------------

async def _save_upload(upload: UploadFile, directory: Path) -> Path:
    """Simpan UploadFile ke direktori, kembalikan Path file yang disimpan."""
    directory.mkdir(parents=True, exist_ok=True)
    # Gunakan UUID agar nama file unik dan aman
    safe_name = f"{uuid.uuid4().hex}_{upload.filename}"
    dest = directory / safe_name
    async with aiofiles.open(dest, "wb") as f:
        content = await upload.read()
        await f.write(content)
    logger.info("File upload disimpan ke: %s", dest)
    return dest


# -------------------------------------------------------------------------
# POST /api/documents/format/standard
# -------------------------------------------------------------------------

@router.post("/format/standard", response_model=FormatResponse)
async def format_standard(
    target_file: UploadFile = File(..., description="Dokumen .docx yang akan diformat"),
    template_id: int        = Form(..., description="ID template preset dari database"),
    db: AsyncSession        = Depends(get_db),
):
    """
    Format dokumen menggunakan template preset yang sudah ada di database.

    Flow:
        1. Upload dokumen target → simpan ke UPLOAD_DIR
        2. Load TemplateConfig dari database berdasarkan template_id
        3. Klasifikasi paragraf dengan IndoBERT (atau heuristik)
        4. Terapkan aturan format → simpan ke OUTPUT_DIR
        5. Simpan task ke database, kembalikan task_id
    """
    # Validasi ekstensi
    if not target_file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Hanya file .docx yang diterima.")

    # 1. Simpan file upload
    input_path = await _save_upload(target_file, settings.UPLOAD_DIR)

    # 2. Load template dari DB
    result = await db.execute(select(TemplateConfig).where(TemplateConfig.id == template_id))
    template = result.scalar_one_or_none()
    if template is None:
        input_path.unlink(missing_ok=True)  # Hapus file yang sudah diupload
        raise HTTPException(status_code=404, detail=f"Template ID {template_id} tidak ditemukan.")

    template_config = template.get_config()

    # 3. Buat task record (status: processing)
    task = FormattingTask(
        original_filename=target_file.filename,
        input_path=str(input_path),
        template_id=template_id,
        status="processing",
        mode="standard",
    )
    db.add(task)
    await db.flush()  # Dapatkan task.id sebelum commit

    try:
        # 4. Klasifikasi paragraf (IndoBERT atau heuristik)
        classifier = get_classifier(
            model_path=settings.INDOBERT_MODEL_PATH,
            base_model=settings.INDOBERT_BASE_MODEL,
        )
        labelled = classifier.classify_document(input_path)

        # 5. Format dokumen
        output_name = generate_output_filename(target_file.filename)
        output_path = settings.OUTPUT_DIR / output_name
        format_with_preset(input_path, output_path, template_config, labelled)
        validation = validate_page_count(input_path, output_path)

        # 6. Update task status → done
        task.output_path = str(output_path)
        task.status      = "done"
        logger.info("Task #%d selesai: %s", task.id, output_path)

    except Exception as exc:
        task.status    = "failed"
        task.error_msg = str(exc)
        logger.error("Task #%d gagal: %s", task.id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Gagal memformat dokumen: {exc}")

    return FormatResponse(
        task_id=task.id,
        status=task.status,
        message=(
            "Dokumen berhasil diformat."
            if validation.get("status") != "warning"
            else f"Dokumen berhasil diformat, tetapi perlu pengecekan: {validation['warning']}"
        ) if task.status == "done" else "Formatting gagal.",
    )


# -------------------------------------------------------------------------
# POST /api/documents/format/adaptive
# -------------------------------------------------------------------------

@router.post("/format/adaptive", response_model=FormatResponse)
async def format_adaptive(
    example_file: UploadFile = File(..., description="Dokumen .docx contoh (sudah diformat dengan benar)"),
    target_file:  UploadFile = File(..., description="Dokumen .docx yang akan diformat"),
    template_name: str       = Form(default="Template Adaptif", description="Nama untuk template yang diekstrak"),
    save_template: bool      = Form(default=True, description="Simpan template ke database untuk digunakan kembali"),
    db: AsyncSession         = Depends(get_db),
):
    """
    Format dokumen menggunakan aturan yang diekstrak dari dokumen contoh (Adaptive Mode).

    Flow:
        1. Upload dokumen contoh + target → simpan ke UPLOAD_DIR
        2. Klasifikasi paragraf dokumen CONTOH dengan IndoBERT
        3. Ekstrak TemplateConfig dari dokumen contoh
        4. (Opsional) Simpan TemplateConfig ke database
        5. Klasifikasi paragraf dokumen TARGET dengan IndoBERT
        6. Terapkan aturan ke dokumen target → simpan ke OUTPUT_DIR
        7. Simpan task, kembalikan task_id
    """
    # Validasi ekstensi
    for f in [example_file, target_file]:
        if not f.filename.endswith(".docx"):
            raise HTTPException(status_code=400, detail=f"File '{f.filename}' harus berformat .docx.")

    # 1. Simpan file upload
    example_path = await _save_upload(example_file, settings.UPLOAD_DIR)
    target_path  = await _save_upload(target_file,  settings.UPLOAD_DIR)

    # Buat task record
    task = FormattingTask(
        original_filename=target_file.filename,
        input_path=str(target_path),
        status="processing",
        mode="adaptive",
    )
    db.add(task)
    await db.flush()

    try:
        classifier = get_classifier(
            model_path=settings.INDOBERT_MODEL_PATH,
            base_model=settings.INDOBERT_BASE_MODEL,
        )

        # 2. Klasifikasi dokumen contoh
        logger.info("Mengklasifikasikan dokumen contoh: %s", example_file.filename)
        example_labels = classifier.classify_document(example_path)

        # 3. Ekstrak TemplateConfig dari dokumen contoh
        template_config = extract_template_config(
            doc_path=example_path,
            labelled_paragraphs=example_labels,
            template_name=template_name,
        )

        # 4. Simpan template ke DB (jika diminta)
        if save_template:
            new_template = TemplateConfig(
                name=template_name,
                description=f"Diekstrak dari: {example_file.filename}",
                is_preset=False,
            )
            new_template.set_config(template_config)
            db.add(new_template)
            await db.flush()
            task.template_id = new_template.id
            logger.info("Template baru disimpan ke DB dengan ID: %d", new_template.id)

        # 5. Klasifikasi dokumen target
        logger.info("Mengklasifikasikan dokumen target: %s", target_file.filename)
        target_labels = classifier.classify_document(target_path)

        # 6. Format dokumen target
        output_name = generate_output_filename(target_file.filename)
        output_path = settings.OUTPUT_DIR / output_name
        format_with_adaptive(target_path, output_path, template_config, target_labels)
        validation = validate_page_count(target_path, output_path)

        # 7. Update task
        task.output_path = str(output_path)
        task.status      = "done"
        logger.info("Adaptive task #%d selesai: %s", task.id, output_path)

    except Exception as exc:
        task.status    = "failed"
        task.error_msg = str(exc)
        logger.error("Adaptive task #%d gagal: %s", task.id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Gagal memformat dokumen: {exc}")

    return FormatResponse(
        task_id=task.id,
        status=task.status,
        message=(
            "Dokumen berhasil diformat menggunakan aturan adaptif."
            if validation.get("status") != "warning"
            else (
                "Dokumen berhasil diformat, tetapi perlu pengecekan: "
                f"{validation['warning']}"
            )
        ) if task.status == "done" else "Formatting gagal.",
    )


# -------------------------------------------------------------------------
# GET /api/documents/{task_id}/status
# -------------------------------------------------------------------------

@router.get("/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Cek status pemrosesan dokumen berdasarkan task_id."""
    result = await db.execute(select(FormattingTask).where(FormattingTask.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task ID {task_id} tidak ditemukan.")

    return TaskStatusResponse(
        task_id=task.id,
        status=task.status,
        mode=task.mode,
        original_filename=task.original_filename,
        output_available=task.status == "done" and task.output_path is not None,
        error_msg=task.error_msg,
    )


# -------------------------------------------------------------------------
# GET /api/documents/{task_id}/download
# -------------------------------------------------------------------------

@router.get("/{task_id}/download")
async def download_result(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Download dokumen hasil formatting.
    Hanya tersedia jika status task = "done".
    """
    result = await db.execute(select(FormattingTask).where(FormattingTask.id == task_id))
    task = result.scalar_one_or_none()

    if task is None:
        raise HTTPException(status_code=404, detail="Task tidak ditemukan.")
    if task.status != "done":
        raise HTTPException(status_code=400, detail=f"Task belum selesai. Status: {task.status}")
    if not task.output_path or not Path(task.output_path).exists():
        raise HTTPException(status_code=404, detail="File output tidak ditemukan.")

    output_path = Path(task.output_path)
    download_name = f"formatted_{task.original_filename}"

    return FileResponse(
        path=str(output_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=download_name,
    )
