"""
config.py
=========
Konfigurasi aplikasi menggunakan Pydantic Settings.
Nilai diambil dari file .env atau environment variables.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Semua konfigurasi aplikasi terpusat di sini.
    Otomatis membaca dari file .env di direktori yang sama.
    """

    # --- App ---
    APP_NAME: str = "AI Document Formatting Agent"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"

    # --- File Storage ---
    UPLOAD_DIR: Path = Path("./storage/uploads")
    OUTPUT_DIR: Path = Path("./storage/outputs")

    # --- IndoBERT Model ---
    INDOBERT_MODEL_PATH: Path = Path("./models/indobert_finetuned")
    INDOBERT_BASE_MODEL: str = "indobenchmark/indobert-base-p1"

    # --- CORS ---
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # --- Security ---
    SECRET_KEY: str = "dev-secret-key-ganti-di-production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    def ensure_directories(self) -> None:
        """Buat direktori storage jika belum ada."""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        Path("./data").mkdir(parents=True, exist_ok=True)
        Path("./models").mkdir(parents=True, exist_ok=True)


# Singleton instance — impor ini di seluruh aplikasi
settings = Settings()
