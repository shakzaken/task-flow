from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url_override: str | None = Field(default=None, alias="DATABASE_URL")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="tasks", alias="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    rabbitmq_url: str = Field(
        default="amqp://guest:guest@localhost:5672/%2F",
        alias="RABBITMQ_URL",
    )
    worker_consumer_queue: str = Field(default="tasks.phase1", alias="WORKER_CONSUMER_QUEUE")
    worker_max_concurrency: int = Field(default=4, alias="WORKER_MAX_CONCURRENCY", ge=1)
    rabbitmq_prefetch_count: int = Field(default=4, alias="RABBITMQ_PREFETCH_COUNT", ge=1)
    db_pool_size: int = Field(default=4, alias="DB_POOL_SIZE", ge=1)
    db_max_overflow: int = Field(default=2, alias="DB_MAX_OVERFLOW", ge=0)
    email_provider_mode: str = Field(default="fake", alias="EMAIL_PROVIDER_MODE")
    resend_api_key: str | None = Field(default=None, alias="RESEND_API_KEY")
    resend_from_email: str = Field(default="onboarding@resend.dev", alias="RESEND_FROM_EMAIL")
    resend_from_name: str = Field(default="Task Flow", alias="RESEND_FROM_NAME")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="openrouter/free", alias="OPENROUTER_MODEL")
    s3_endpoint: str | None = Field(default=None, alias="S3_ENDPOINT")
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")
    s3_bucket: str = Field(default="task-flow", alias="S3_BUCKET")
    s3_access_key_id: str | None = Field(default=None, alias="S3_ACCESS_KEY_ID")
    s3_secret_access_key: str | None = Field(default=None, alias="S3_SECRET_ACCESS_KEY")
    s3_use_ssl: bool = Field(default=True, alias="S3_USE_SSL")
    s3_force_path_style: bool = Field(default=False, alias="S3_FORCE_PATH_STYLE")
    s3_auto_create_bucket: bool = Field(default=False, alias="S3_AUTO_CREATE_BUCKET")
    output_storage_path: str = Field(default="outputs", alias="OUTPUT_STORAGE_PATH")
    worker_work_root: Path | None = Field(default=None, alias="WORKER_WORK_ROOT")
    worker_port: int = Field(default=8001, alias="WORKER_PORT")

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            if self.database_url_override.startswith("postgresql+asyncpg://"):
                return self.database_url_override.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
            return self.database_url_override
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
