"""
routers/templates.py
=======================
Endpoint API untuk manajemen template konfigurasi format.

Endpoint:
    GET    /api/templates/              — List semua template (preset + user)
    POST   /api/templates/extract       — Ekstrak template dari dokumen contoh
    GET    /api/templates/{id}          — Detail satu template
    DELETE /api/templates/{id}          — Hapus template (non-preset)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import settings
from models.database import TemplateConfig, get_db
from services.rule_based_extractor import extract_template_config
from services.structure_classifier import get_classifier
from routers.documents import _save_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/templates", tags=["templates"])


# -------------------------------------------------------------------------
# Response Schemas
# -------------------------------------------------------------------------

class TemplateListItem(BaseModel):
    id:          int
    name:        str
    description: Optional[str]
    is_preset:   bool


class TemplateDetailResponse(BaseModel):
    id:          int
    name:        str
    description: Optional[str]
    is_preset:   bool
    config:      dict  # TemplateConfig dict lengkap


class ExtractResponse(BaseModel):
    template_id:   int
    name:          str
    config_preview: dict
    message:        str


# -------------------------------------------------------------------------
# GET /api/templates/
# -------------------------------------------------------------------------

@router.get("/", response_model=list[TemplateListItem])
async def list_templates(db: AsyncSession = Depends(get_db)):
    """
    Kembalikan semua template yang tersedia:
    - Template preset bawaan sistem (is_preset=True)
    - Template yang diekstrak oleh user (is_preset=False)
    """
    result = await db.execute(select(TemplateConfig))
    templates = result.scalars().all()
    return [
        TemplateListItem(
            id=t.id,
            name=t.name,
            description=t.description,
            is_preset=t.is_preset,
        )
        for t in templates
    ]


# -------------------------------------------------------------------------
# POST /api/templates/extract
# -------------------------------------------------------------------------

@router.post("/extract", response_model=ExtractResponse)
async def extract_template(
    example_file:  UploadFile = File(..., description="Dokumen .docx contoh yang sudah diformat dengan benar"),
    template_name: str        = Form(default="Template Baru", description="Nama untuk template ini"),
    description:   str        = Form(default="", description="Deskripsi singkat sumber template"),
    db: AsyncSession          = Depends(get_db),
):
    """
    Ekstrak TemplateConfig dari dokumen contoh dan simpan ke database.

    Digunakan oleh Adaptive Mode untuk membuat template baru dari dokumen contoh.
    Template yang tersimpan dapat digunakan kembali untuk dokumen berikutnya.
    """
    if not example_file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="File harus berformat .docx.")

    # Simpan file upload
    doc_path = await _save_upload(example_file, settings.UPLOAD_DIR)

    try:
        # Klasifikasikan paragraf dokumen contoh (IndoBERT atau heuristik)
        classifier = get_classifier(
            model_path=settings.INDOBERT_MODEL_PATH,
            base_model=settings.INDOBERT_BASE_MODEL,
        )
        labelled = classifier.classify_document(doc_path)

        # Ekstrak TemplateConfig
        config = extract_template_config(
            doc_path=doc_path,
            labelled_paragraphs=labelled,
            template_name=template_name,
            description=description,
        )

        # Simpan ke database
        template = TemplateConfig(
            name=template_name,
            description=description or f"Diekstrak dari: {example_file.filename}",
            is_preset=False,
        )
        template.set_config(config)
        db.add(template)
        await db.flush()

        logger.info(
            "Template '%s' berhasil diekstrak dan disimpan (ID: %d)",
            template_name, template.id
        )

        # Kembalikan preview config (tanpa _meta untuk kebersihan response)
        config_preview = {k: v for k, v in config.items() if not k.startswith("_")}

        return ExtractResponse(
            template_id=template.id,
            name=template_name,
            config_preview=config_preview,
            message=f"Template '{template_name}' berhasil diekstrak dari '{example_file.filename}'.",
        )

    except Exception as exc:
        logger.error("Gagal mengekstrak template: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Gagal mengekstrak template: {exc}")


# -------------------------------------------------------------------------
# GET /api/templates/{id}
# -------------------------------------------------------------------------

@router.get("/{template_id}", response_model=TemplateDetailResponse)
async def get_template(template_id: int, db: AsyncSession = Depends(get_db)):
    """Dapatkan detail satu template termasuk config JSON lengkap."""
    result = await db.execute(
        select(TemplateConfig).where(TemplateConfig.id == template_id)
    )
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=404, detail=f"Template ID {template_id} tidak ditemukan.")

    return TemplateDetailResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        is_preset=template.is_preset,
        config=template.get_config(),
    )


# -------------------------------------------------------------------------
# DELETE /api/templates/{id}
# -------------------------------------------------------------------------

@router.delete("/{template_id}")
async def delete_template(template_id: int, db: AsyncSession = Depends(get_db)):
    """
    Hapus template dari database.
    Template preset (is_preset=True) tidak dapat dihapus.
    """
    result = await db.execute(
        select(TemplateConfig).where(TemplateConfig.id == template_id)
    )
    template = result.scalar_one_or_none()

    if template is None:
        raise HTTPException(status_code=404, detail="Template tidak ditemukan.")
    if template.is_preset:
        raise HTTPException(status_code=403, detail="Template preset tidak dapat dihapus.")

    await db.delete(template)
    return {"message": f"Template ID {template_id} berhasil dihapus."}
