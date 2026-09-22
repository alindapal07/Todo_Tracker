import os

from pydantic_settings import BaseSettings, SettingsConfigDict


environment = os.getenv("APP_ENV", "dev")


class Settings(BaseSettings):
    APP_NAME: str = "Todo_App"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=f".env.{environment}",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()