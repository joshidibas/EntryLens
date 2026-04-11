from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(Path(__file__).resolve().parents[2] / ".env", Path(__file__).resolve().parents[1] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "EntryLens API"
    api_key: str = Field(alias="SENTINEL_API_KEY")
    recognition_provider: str = Field(default="local", alias="SENTINEL_RECOGNITION_PROVIDER")
    high_confidence_threshold: float = Field(default=0.85, alias="SENTINEL_HIGH_CONFIDENCE_THRESHOLD")
    low_confidence_threshold: float = Field(default=0.60, alias="SENTINEL_LOW_CONFIDENCE_THRESHOLD")
    debounce_window_seconds: int = Field(default=300, alias="SENTINEL_DEBOUNCE_WINDOW_SECONDS")
    allowed_origins: str = Field(default="http://localhost:5173", alias="SENTINEL_ALLOWED_ORIGINS")
    database_url: str = Field(default="sqlite+aiosqlite:///./entrylens.db", alias="SENTINEL_DATABASE_URL")
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_service_key: str = Field(default="", alias="SUPABASE_SERVICE_KEY")
    supabase_db_url: str = Field(default="", alias="SUPABASE_DB_URL")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def has_supabase_config(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_key and self.supabase_db_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
