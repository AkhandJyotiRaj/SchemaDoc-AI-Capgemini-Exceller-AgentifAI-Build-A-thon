"""
Production-grade configuration using Pydantic Settings.
Replaces the old flat AppConfig class.
"""
import os
import logging
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── API Keys ──
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # ── Pipeline ──
    MAX_RETRIES: int = 3

    # ── Paths (computed from project root) ──
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = Path("")
    OUTPUT_DIR: Path = Path("")
    LOGS_DIR: Path = Path("")

    # ── Server ──
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    LOG_LEVEL: str = "INFO"

    # ── Database ──
    DATABASE_URL: Optional[str] = None
    NEON_DATABASE_URL: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    def model_post_init(self, __context):
        """Compute derived paths after loading env."""
        if not self.DATA_DIR or str(self.DATA_DIR) == ".":
            self.DATA_DIR = self.BASE_DIR / "data"
        if not self.OUTPUT_DIR or str(self.OUTPUT_DIR) == ".":
            self.OUTPUT_DIR = self.DATA_DIR / "output"
        if not self.LOGS_DIR or str(self.LOGS_DIR) == ".":
            self.LOGS_DIR = self.DATA_DIR / "logs"
        # Ensure directories exist
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    @field_validator("GOOGLE_API_KEY", mode="before")
    @classmethod
    def clean_api_key(cls, v):
        if v:
            return v.strip().strip('"').strip("'")
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    def validate_keys(self):
        """Validate that required API keys are present."""
        if not self.GOOGLE_API_KEY:
            raise ValueError("CRITICAL: GOOGLE_API_KEY is missing from environment variables.")
        try:
            preview = f"{self.GOOGLE_API_KEY[:6]}...{self.GOOGLE_API_KEY[-4:]}"
            logger.info(f"GOOGLE_API_KEY present. Preview={preview} (len={len(self.GOOGLE_API_KEY)})")
        except Exception:
            logger.info("GOOGLE_API_KEY present. (unable to preview)")

    @property
    def DEFAULT_DB_CONNECTION(self) -> str:
        return f"sqlite:///{self.DATA_DIR}/demo.db"


# ── Singleton ──
settings = Settings()


# ── Backwards-compatible AppConfig shim (so pipeline code doesn't break) ──
class AppConfig:
    """Backwards-compatible shim for existing pipeline nodes."""
    BASE_DIR = settings.BASE_DIR
    DATA_DIR = settings.DATA_DIR
    OUTPUT_DIR = settings.OUTPUT_DIR
    LOGS_DIR = settings.LOGS_DIR
    DEFAULT_DB_CONNECTION = settings.DEFAULT_DB_CONNECTION
    GEMINI_API_KEY = settings.GOOGLE_API_KEY
    GEMINI_MODEL = settings.GEMINI_MODEL
    MAX_RETRIES = settings.MAX_RETRIES

    @classmethod
    def validate(cls):
        settings.validate_keys()
