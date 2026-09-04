from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "KIROSHI Core Platform"
    VERSION: str = "0.2.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = "development-secret-key-do-not-use-in-production-change-me-0123456789abcdef"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = "sqlite:///./kiroshi.db"

    # Geospatial & Location Freshness
    LOCATION_FRESHNESS_LIVE_SECONDS: int = 30
    LOCATION_FRESHNESS_RECENT_SECONDS: int = 180
    MAX_GPS_CLOCK_SKEW_SECONDS: int = 300
    MAX_GPS_AGE_HOURS: int = 24

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
