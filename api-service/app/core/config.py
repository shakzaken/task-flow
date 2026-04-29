from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_environment: str = Field(default="development", alias="APP_ENVIRONMENT")
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
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    rate_limit_prefix: str = Field(default="rate-limit", alias="RATE_LIMIT_PREFIX")
    s3_endpoint: str | None = Field(default=None, alias="S3_ENDPOINT")
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")
    s3_bucket: str = Field(default="task-flow", alias="S3_BUCKET")
    s3_access_key_id: str | None = Field(default=None, alias="S3_ACCESS_KEY_ID")
    s3_secret_access_key: str | None = Field(default=None, alias="S3_SECRET_ACCESS_KEY")
    s3_use_ssl: bool = Field(default=True, alias="S3_USE_SSL")
    s3_force_path_style: bool = Field(default=False, alias="S3_FORCE_PATH_STYLE")
    s3_auto_create_bucket: bool = Field(default=False, alias="S3_AUTO_CREATE_BUCKET")

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )

    @property
    def cors_allow_all_origins(self) -> bool:
        return (
            self.app_environment.lower() == "development"
            and self.postgres_host in {"localhost", "127.0.0.1"}
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
