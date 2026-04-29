from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(ValueError):
    """Raised when required CDK configuration is missing or invalid."""


@dataclass(frozen=True)
class AppConfig:
    aws_account: str | None
    aws_region: str
    stack_name: str
    app_name: str
    api_image_repository: str
    api_image_tag: str
    worker_image_repository: str
    worker_image_tag: str
    s3_bucket_name: str
    api_port: int
    worker_port: int
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    redis_port: int
    rabbitmq_port: int
    rabbitmq_default_user: str
    rabbitmq_default_pass: str
    rabbitmq_vhost: str
    rabbitmq_queue: str
    rabbitmq_prefetch_count: int
    worker_max_concurrency: int
    db_pool_size: int
    db_max_overflow: int
    email_provider_mode: str
    resend_api_key: str
    resend_from_email: str
    resend_from_name: str
    worker_work_root: str
    output_storage_path: str
    openrouter_api_key: str
    openrouter_model: str

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.rabbitmq_default_user}:{self.rabbitmq_default_pass}"
            f"@rabbitmq:{self.rabbitmq_port}/{self.rabbitmq_vhost}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://redis:{self.redis_port}/0"


def load_app_config(env_file: str | Path | None = None) -> AppConfig:
    env_path = Path(env_file) if env_file is not None else Path(__file__).resolve().parent / ".env.cdk"
    file_values = _parse_env_file(env_path)
    values = {**file_values, **os.environ}

    return AppConfig(
        aws_account=_optional_str(values, "AWS_ACCOUNT"),
        aws_region=_required_str(values, "AWS_REGION"),
        stack_name=_required_str(values, "STACK_NAME"),
        app_name=_required_str(values, "APP_NAME"),
        api_image_repository=_required_str(values, "API_IMAGE_REPOSITORY"),
        api_image_tag=_required_str(values, "API_IMAGE_TAG"),
        worker_image_repository=_required_str(values, "WORKER_IMAGE_REPOSITORY"),
        worker_image_tag=_required_str(values, "WORKER_IMAGE_TAG"),
        s3_bucket_name=_required_str(values, "S3_BUCKET_NAME"),
        api_port=_required_int(values, "API_PORT"),
        worker_port=_required_int(values, "WORKER_PORT"),
        postgres_port=_required_int(values, "POSTGRES_PORT"),
        postgres_db=_required_str(values, "POSTGRES_DB"),
        postgres_user=_required_str(values, "POSTGRES_USER"),
        postgres_password=_required_str(values, "POSTGRES_PASSWORD"),
        redis_port=_required_int(values, "REDIS_PORT"),
        rabbitmq_port=_required_int(values, "RABBITMQ_PORT"),
        rabbitmq_default_user=_required_str(values, "RABBITMQ_DEFAULT_USER"),
        rabbitmq_default_pass=_required_str(values, "RABBITMQ_DEFAULT_PASS"),
        rabbitmq_vhost=_required_str(values, "RABBITMQ_VHOST"),
        rabbitmq_queue=_required_str(values, "RABBITMQ_QUEUE"),
        rabbitmq_prefetch_count=_required_int(values, "RABBITMQ_PREFETCH_COUNT"),
        worker_max_concurrency=_required_int(values, "WORKER_MAX_CONCURRENCY"),
        db_pool_size=_required_int(values, "DB_POOL_SIZE"),
        db_max_overflow=_required_int(values, "DB_MAX_OVERFLOW"),
        email_provider_mode=_required_str(values, "EMAIL_PROVIDER_MODE"),
        resend_api_key=_required_str(values, "RESEND_API_KEY"),
        resend_from_email=_required_str(values, "RESEND_FROM_EMAIL"),
        resend_from_name=_required_str(values, "RESEND_FROM_NAME"),
        worker_work_root=_required_str(values, "WORKER_WORK_ROOT"),
        output_storage_path=_required_str(values, "OUTPUT_STORAGE_PATH"),
        openrouter_api_key=_required_str(values, "OPENROUTER_API_KEY"),
        openrouter_model=_required_str(values, "OPENROUTER_MODEL"),
    )


def _parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        raise ConfigError(
            f"Missing CDK config file at {path}. Create it from {path.parent / '.env.cdk.example'}."
        )

    parsed: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ConfigError(f"Invalid line in {path}: {raw_line!r}")
        key, value = line.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def _required_str(values: dict[str, str], key: str) -> str:
    value = values.get(key, "").strip()
    if not value:
        raise ConfigError(f"Missing required CDK config value: {key}")
    return value


def _optional_str(values: dict[str, str], key: str) -> str | None:
    value = values.get(key, "").strip()
    return value or None


def _required_int(values: dict[str, str], key: str) -> int:
    raw_value = _required_str(values, key)
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ConfigError(f"CDK config value {key} must be an integer, got {raw_value!r}") from exc
