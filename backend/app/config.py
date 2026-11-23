"""Environment configuration and settings management using Pydantic Settings."""

from __future__ import annotations

import secrets
from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Centralized application settings loaded from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "CCTV Network Discovery & Recovery Assistant"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False

    HOST: str = "127.0.0.1"
    PORT: int = 8000
    ALLOW_LAN_ACCESS: bool = False

    API_ACCESS_TOKEN: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_hex(32))
    VAULT_KEY_PATH: str = str(ROOT_DIR / "data" / "database" / ".vault.key")

    CORS_ALLOWED_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000"
    )

    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 180
    SCAN_RATE_LIMIT_PER_MINUTE: int = 10

    DATABASE_URL: str = f"sqlite:///{(ROOT_DIR / 'data' / 'database' / 'cctv_assistant.db').as_posix()}"

    SCAN_DEFAULT_TIMEOUT_MS: int = 800
    SCAN_MAX_CONCURRENCY: int = 64
    SCAN_PORT_TIMEOUT_MS: int = 500
    SCAN_ENABLE_ARP: bool = True
    SCAN_ENABLE_ICMP: bool = True
    SCAN_ENABLE_TCP_PROBE: bool = True
    SCAN_ENABLE_ONVIF: bool = True
    SCAN_ENABLE_MDNS: bool = True
    SCAN_ENABLE_SSDP: bool = True
    ONVIF_DISCOVERY_TIMEOUT_SECONDS: float = 2.5
    MDNS_DISCOVERY_TIMEOUT_SECONDS: float = 2.0
    SSDP_DISCOVERY_TIMEOUT_SECONDS: float = 2.0

    MONITORING_ENABLED: bool = True
    MONITORING_INTERVAL_SECONDS: int = 60
    MONITORING_TIMEOUT_MS: int = 1000

    FFMPEG_BINARY: str = "ffmpeg"
    STREAM_MAX_FPS: int = 15
    STREAM_JPEG_QUALITY: int = 5
    STREAM_IDLE_TIMEOUT_SECONDS: int = 45

    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = str(ROOT_DIR / "data" / "logs" / "cctv_assistant.log")

    @property
    def cors_origins_list(self) -> list[str]:
        origins = [o.strip() for o in self.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]
        if self.ALLOW_LAN_ACCESS and "*" not in origins:
            # Allow local LAN origin patterns via CORS middleware configuration
            pass
        return origins

    @property
    def config_dir(self) -> Path:
        return ROOT_DIR / "config"

    @property
    def data_dir(self) -> Path:
        return ROOT_DIR / "data"


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()

