from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(default="sqlite:///./pocketquant.db", alias="DATABASE_URL")
    coingecko_base_url: str = Field(
        default="https://api.coingecko.com/api/v3", alias="COINGECKO_BASE_URL"
    )
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    backend_base_url: str = Field(default="http://127.0.0.1:8000", alias="BACKEND_BASE_URL")
    bot_timezone: str = Field(default="UTC", alias="BOT_TIMEZONE")
    daily_digest_hour: int = Field(default=9, alias="DAILY_DIGEST_HOUR")
    weekly_digest_weekday: str = Field(default="MON", alias="WEEKLY_DIGEST_WEEKDAY")
    price_sync_enabled: bool = Field(default=True, alias="PRICE_SYNC_ENABLED")
    price_sync_interval_hours: int = Field(default=1, alias="PRICE_SYNC_INTERVAL_HOURS")
    coingecko_timeout_sec: float = Field(default=10.0, alias="COINGECKO_TIMEOUT_SEC")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
