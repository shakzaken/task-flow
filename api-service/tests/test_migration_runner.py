from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import Settings
from app.services.migration_runner import MigrationRunner


@pytest.mark.anyio
async def test_migration_runner_upgrades_head(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(
        APP_ENVIRONMENT="test",
        POSTGRES_HOST="db.internal",
        POSTGRES_PORT=5432,
        POSTGRES_DB="task_flow",
        POSTGRES_USER="task_flow",
        POSTGRES_PASSWORD="secret",
    )
    runner = MigrationRunner(settings)

    captured: dict[str, str] = {}

    def fake_upgrade(config, revision: str) -> None:
        captured["revision"] = revision
        captured["script_location"] = config.get_main_option("script_location")
        captured["sqlalchemy_url"] = config.get_main_option("sqlalchemy.url")

    monkeypatch.setattr("app.services.migration_runner.command.upgrade", fake_upgrade)

    await runner.run_pending_migrations()

    assert captured["revision"] == "head"
    assert captured["script_location"] == str(Path(__file__).resolve().parents[1] / "migrations")
    assert captured["sqlalchemy_url"] == settings.sync_database_url
