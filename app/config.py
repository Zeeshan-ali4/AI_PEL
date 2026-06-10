from functools import lru_cache

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    app_host: str = Field(default="0.0.0.0", validation_alias="APP_HOST")
    app_port: int = Field(default=8080, validation_alias="APP_PORT")
    opa_url: str = Field(default="http://opa:8181", validation_alias="OPA_URL")
    postgres_host: str = Field(default="postgres", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, validation_alias="POSTGRES_PORT")
    postgres_db: str = Field(default="ai_pel", validation_alias="POSTGRES_DB")
    postgres_user: str = Field(default="ai_pel", validation_alias="POSTGRES_USER")
    postgres_password: str = Field(default="ai_pel", validation_alias="POSTGRES_PASSWORD")
    database_url: PostgresDsn = Field(
        default="postgresql://ai_pel:ai_pel@postgres:5432/ai_pel",
        validation_alias="DATABASE_URL",
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()
