from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_host: str = Field(default="0.0.0.0", validation_alias="APP_HOST")
    app_port: int = Field(default=8080, validation_alias="APP_PORT")
    opa_url: str = Field(default="http://opa:8181", validation_alias="OPA_URL")
    postgres_host: str = Field(default="postgres", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, validation_alias="POSTGRES_PORT")
    postgres_db: str = Field(default="ai_pel", validation_alias="POSTGRES_DB")
    postgres_user: str = Field(default="ai_pel", validation_alias="POSTGRES_USER")
    postgres_password: str = Field(validation_alias="POSTGRES_PASSWORD")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def postgres_connection_kwargs(self) -> dict[str, str | int]:
        return {
            "host": self.postgres_host,
            "port": self.postgres_port,
            "dbname": self.postgres_db,
            "user": self.postgres_user,
            "password": self.postgres_password,  # NOSONAR - runtime env value, not a committed secret
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
