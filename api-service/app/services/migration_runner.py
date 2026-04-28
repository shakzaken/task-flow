from __future__ import annotations

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.config import Settings


class MigrationRunner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.project_root = Path(__file__).resolve().parents[2]

    async def run_pending_migrations(self) -> None:
        await asyncio.to_thread(self._upgrade_head)

    def _upgrade_head(self) -> None:
        alembic_config = Config(str(self.project_root / "alembic.ini"))
        alembic_config.set_main_option("script_location", str(self.project_root / "migrations"))
        alembic_config.set_main_option("sqlalchemy.url", self.settings.sync_database_url)
        command.upgrade(alembic_config, "head")


def build_migration_runner(settings: Settings) -> MigrationRunner:
    return MigrationRunner(settings)
