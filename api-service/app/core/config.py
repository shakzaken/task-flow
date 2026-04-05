from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url_override: str | None = Field(default=None, alias="DATABASE_URL")
    api_port: int = Field(default=8000, alias="API_PORT")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="tasks", alias="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    rabbitmq_url: str = Field(
        default="amqp://guest:guest@localhost:5672/%2F",
        alias="RABBITMQ_URL",
    )
    storage_mode: str = Field(default="local", alias="STORAGE_MODE")
    local_storage_path: Path = Field(default=Path("/shared-data"), alias="LOCAL_STORAGE_PATH")
    minio_endpoint: str | None = Field(default=None, alias="MINIO_ENDPOINT")
    minio_access_key: str | None = Field(default=None, alias="MINIO_ACCESS_KEY")
    minio_secret_key: str | None = Field(default=None, alias="MINIO_SECRET_KEY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
    )

    @property
    def sync_database_url(self) -> str:
        if self.database_url_override:
            if self.database_url_override.startswith("sqlite+aiosqlite:///"):
                return self.database_url_override.replace("sqlite+aiosqlite:///", "sqlite:///", 1)
            if self.database_url_override.startswith("postgresql+asyncpg://"):
                return self.database_url_override.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
            return self.database_url_override
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            if self.database_url_override.startswith("sqlite:///"):
                return self.database_url_override.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
            if self.database_url_override.startswith("postgresql+psycopg://"):
                return self.database_url_override.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)
            return self.database_url_override
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
