"""
Application configuration loaded from environment variables.
Uses Pydantic BaseSettings for automatic .env file loading and validation.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    """All application settings — loaded from .env file or environment variables."""

    # ── Application ──
    APP_NAME: str = "PlantDiseaseAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ── Database ──
    DATABASE_URL: str

    # ── Redis ──
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ──
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── MinIO ──
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET_NAME: str = "leaf-images"
    MINIO_SECURE: bool = False

    # ── ML Model ──
    MODEL_PATH: str = "../ml/models/plant_disease_model.keras"
    LABELS_PATH: str = "../ml/models/labels.json"

    # ── Rate Limiting ──
    RATE_LIMIT_PER_MINUTE: int = 10

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    Using lru_cache ensures the .env file is read only once.
    """
    return Settings()
