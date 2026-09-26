import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


environment = os.getenv("APP_ENV", "dev")

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ".env"


class Settings(BaseSettings):
    APP_NAME: str = "Todo_App"
    ENVIRONMENT: str = environment

    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_ACCESS_TOKEN_EXPIRES_TIME: int = 30
    REFRESH_TOKEN_EXPIRY_TIME: int = 15
    REFRESH_COOKIE_NAME: str = "refresh_token"
    REFRESH_TOKEN_MAX_AGE: int = 14 * 24 * 60 * 60

    @property
    def token_expire_minutes(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES or self.JWT_ACCESS_TOKEN_EXPIRES_TIME or 30

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()