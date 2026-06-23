"""Application configuration via environment variables.

Uses pydantic-settings to load and validate config from .env files
or environment variables. Secrets (API keys) are NEVER hardcoded.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All values can be overridden via .env file or OS environment variables.
    Secrets like GROQ_API_KEY must be set externally — they have no default.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- LLM Provider ---
    groq_api_key: str  # Required — no default, forces explicit configuration
    groq_model: str = "llama-3.3-70b-versatile"

    # --- Model Paths ---
    model_path: str = "model/isl_model_2hand.tflite"
    labels_path: str = "model/labels_2hand.json"

    # --- Recognition Tuning ---
    stability_frames: int = 5
    buffer_timeout_seconds: float = 5.0
    min_buffer_size: int = 3
    confidence_threshold: float = 80.0

    # --- Networking ---
    cors_origins: str = "http://localhost:5173"
    host: str = "0.0.0.0"
    port: int = 8000

    # --- Logging ---
    log_level: str = "info"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def model_dir(self) -> Path:
        """Return the directory containing the model file."""
        return Path(self.model_path).parent


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — loaded once per process."""
    return Settings()
