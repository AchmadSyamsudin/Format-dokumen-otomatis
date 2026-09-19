"""
main.py
========
Entry point aplikasi FastAPI — AI Document Formatting Agent

Menjalankan server dengan:
    uvicorn main:app --reload --port 8000

Endpoint:
    GET  /          — Health check / info aplikasi
    GET  /docs      — Swagger UI (auto-generated)
    GET  /redoc     — ReDoc UI
    ...  /api/...   — Endpoint bisnis (lihat routers/)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models.database import init_db
from routers.documents import router as documents_router
from routers.templates import router as templates_router
from services.structure_classifier import get_classifier

# -------------------------------------------------------------------------
# Logging setup
# -------------------------------------------------------------------------

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# Lifespan: startup & shutdown events
# -------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager untuk FastAPI.
    Kode sebelum `yield` dijalankan saat startup.
    Kode setelah `yield` dijalankan saat shutdown.
    """
    logger.info("=" * 60)
    logger.info("  %s v%s — Starting up...", settings.APP_NAME, settings.APP_VERSION)
    logger.info("=" * 60)

    # 1. Buat direktori storage
    settings.ensure_directories()
    logger.info("Storage directories siap.")

    # 2. Inisialisasi database (buat tabel jika belum ada)
    await init_db()
    logger.info("Database diinisialisasi.")

    # 3. Load IndoBERT model (lazy — heuristik fallback jika model belum ada)
    classifier = get_classifier(
        model_path=settings.INDOBERT_MODEL_PATH,
        base_model=settings.INDOBERT_BASE_MODEL,
    )
    if classifier.is_loaded:
        logger.info("IndoBERT model berhasil dimuat dari: %s", settings.INDOBERT_MODEL_PATH)
    else:
        logger.warning(
            "IndoBERT model TIDAK dimuat (path: %s). "
            "Menggunakan heuristik fallback. "
            "Fine-tune model terlebih dahulu menggunakan notebooks/indobert_finetuning.ipynb",
            settings.INDOBERT_MODEL_PATH,
        )

    logger.info("Aplikasi siap. Swagger UI: http://localhost:8000/docs")
    logger.info("-" * 60)

    yield  # ← Aplikasi berjalan

    # Shutdown
    logger.info("Shutting down %s...", settings.APP_NAME)


# -------------------------------------------------------------------------
# FastAPI App Instance
# -------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## AI Document Formatting Agent

Aplikasi web untuk memformat dokumen akademik Indonesia (.docx) secara otomatis.

### Dua Mode Pemrosesan:
1. **Standard Mode** — Pilih template preset dan terapkan ke dokumen
2. **Adaptive Mode** — Upload dokumen contoh + target; sistem belajar dari contoh

### Dua Layer Pipeline (terpisah):
- **Layer 1 (Rule-Based)**: Ekstrak & terapkan aturan format menggunakan `python-docx`
- **Layer 2 (IndoBERT)**: Klasifikasi struktural paragraf menggunakan model fine-tuned

> Catatan: Semua inferensi berjalan **lokal/offline** — tidak ada API call ke cloud AI.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# -------------------------------------------------------------------------
# CORS Middleware
# -------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------------
# Routers
# -------------------------------------------------------------------------

app.include_router(documents_router)
app.include_router(templates_router)


# -------------------------------------------------------------------------
# Root Endpoint
# -------------------------------------------------------------------------

@app.get("/", tags=["health"])
async def root():
    """Health check — kembalikan info aplikasi."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "format_standard": "POST /api/documents/format/standard",
            "format_adaptive": "POST /api/documents/format/adaptive",
            "list_templates":  "GET  /api/templates/",
            "extract_template": "POST /api/templates/extract",
        },
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Cek status komponen utama aplikasi."""
    from services.structure_classifier import _classifier_instance
    return {
        "status": "healthy",
        "indobert_loaded": _classifier_instance.is_loaded if _classifier_instance else False,
        "debug_mode": settings.DEBUG,
    }
