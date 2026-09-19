"""
models/database.py
==================
Definisi model SQLAlchemy dan session database (SQLite async via aiosqlite).

Tabel:
- users          : Pengguna aplikasi (dapat diperluas dengan auth nanti)
- template_configs: Konfigurasi format yang disimpan per user
- formatting_tasks: Riwayat tugas pemformatan dokumen
"""

import json
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Boolean
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship

from config import settings

# -------------------------------------------------------------------------
# Base & Engine
# -------------------------------------------------------------------------

class Base(DeclarativeBase):
    """Base class untuk semua model SQLAlchemy."""
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,       # Log SQL query saat DEBUG=True
    connect_args={"check_same_thread": False},  # Diperlukan untuk SQLite
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# -------------------------------------------------------------------------
# Models
# -------------------------------------------------------------------------

class User(Base):
    """
    Tabel pengguna.
    Saat ini hanya berupa identifier sederhana (username/session).
    Dapat dikembangkan dengan autentikasi JWT ke depannya.
    """
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    username   = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relasi
    template_configs = relationship("TemplateConfig", back_populates="user", cascade="all, delete-orphan")
    formatting_tasks = relationship("FormattingTask", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"


class TemplateConfig(Base):
    """
    Konfigurasi format dokumen yang diekstrak dari dokumen contoh
    atau dipilih dari preset template bawaan sistem.

    Kolom `config_json` menyimpan dict sesuai template_config_schema.json
    dalam format string JSON.
    """
    __tablename__ = "template_configs"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null = template global/preset
    name        = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    config_json = Column(Text, nullable=False)   # JSON string sesuai TemplateConfig schema
    is_preset   = Column(Boolean, default=False) # True = template bawaan sistem
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi
    user  = relationship("User", back_populates="template_configs")
    tasks = relationship("FormattingTask", back_populates="template")

    def get_config(self) -> dict:
        """Deserialize config_json ke Python dict."""
        return json.loads(self.config_json)

    def set_config(self, config: dict) -> None:
        """Serialize Python dict ke config_json."""
        self.config_json = json.dumps(config, ensure_ascii=False, indent=2)

    def __repr__(self) -> str:
        return f"<TemplateConfig id={self.id} name={self.name!r} is_preset={self.is_preset}>"


class FormattingTask(Base):
    """
    Riwayat tugas pemformatan dokumen.

    Status lifecycle: pending → processing → done | failed
    """
    __tablename__ = "formatting_tasks"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=True)
    template_id = Column(Integer, ForeignKey("template_configs.id"), nullable=True)

    # Nama file asli yang diupload
    original_filename = Column(String(255), nullable=False)

    # Path file di storage (relatif terhadap OUTPUT_DIR/UPLOAD_DIR)
    input_path  = Column(String(500), nullable=True)
    output_path = Column(String(500), nullable=True)

    # Status pemrosesan
    status      = Column(String(50), default="pending")  # pending|processing|done|failed
    error_msg   = Column(Text, nullable=True)            # Pesan error jika status=failed

    # Mode: "standard" atau "adaptive"
    mode        = Column(String(20), default="standard")

    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi
    user     = relationship("User", back_populates="formatting_tasks")
    template = relationship("TemplateConfig", back_populates="tasks")

    def __repr__(self) -> str:
        return f"<FormattingTask id={self.id} status={self.status!r} file={self.original_filename!r}>"


# -------------------------------------------------------------------------
# Dependency & Init
# -------------------------------------------------------------------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency untuk mendapatkan database session.

    Penggunaan:
        @router.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """
    Inisialisasi database: buat semua tabel jika belum ada.
    Dipanggil saat aplikasi FastAPI startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
