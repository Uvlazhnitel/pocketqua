from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="dev", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    database_url: str = Field(default="postgresql+psycopg://postgres:postgres@localhost:5432/pocketquant", alias="DATABASE_URL")

    bybit_base_url: str = Field(default="https://api.bybit.com", alias="BYBIT_BASE_URL")
    bybit_api_key: str = Field(default="", alias="BYBIT_API_KEY")
    bybit_api_secret: str = Field(default="", alias="BYBIT_API_SECRET")
    bybit_recv_window: int = Field(default=5000, alias="BYBIT_RECV_WINDOW")

    sync_interval_seconds: int = Field(default=300, alias="SYNC_INTERVAL_SECONDS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    max_sync_workers: int = Field(default=3, alias="MAX_SYNC_WORKERS")

    encryption_key: str = Field(default="", alias="ENCRYPTION_KEY")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
