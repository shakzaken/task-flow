from app.core.config import Settings


def test_s3_settings_have_reasonable_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.s3_bucket == "task-flow"
    assert settings.s3_region == "us-east-1"
    assert settings.s3_auto_create_bucket is False
