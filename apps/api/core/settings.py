"""
ORCA — Application Settings
Loads configuration from .env file with sensible defaults.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    secret_key: str = "change-me-in-production"
    version: str = "0.1.0"

    # Database
    database_url: str = "postgresql+asyncpg://orca:orca@localhost:5432/orca"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"

    # LLM / ORCA Configuration
    llm_provider: str = "gemini"
    llm_api_key: str = ""
    llm_model: str = "gemini-1.5-flash"
    orca_max_iterations: int = 10
    orca_temperature: float = 0.2

    # Feature Flags
    enable_demo_mode: bool = True
    enable_real_incois: bool = False
    enable_real_imd: bool = False
    enable_real_bhoonidhi: bool = False
    enable_real_transponder: bool = False

    # STT/TTS
    vosk_model_path: str = "./models/vosk-model-small-en-in-0.4"
    whisper_model: str = "tiny"
    tts_engine: str = "pyttsx3"

    # H3 Spatial Cache
    h3_cache_resolution: int = 8
    h3_cache_max_mb: int = 3

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def has_llm_key(self) -> bool:
        return bool(self.llm_api_key and self.llm_api_key != "your-llm-api-key-here")


# Singleton — import this wherever settings are needed
settings = Settings()
