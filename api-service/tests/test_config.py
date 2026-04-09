from pathlib import Path

from app.core.config import Settings


def test_local_storage_path_defaults_to_repo_shared_data() -> None:
    settings = Settings(_env_file=None)

    expected_path = Path(__file__).resolve().parents[2] / "shared-data"
    assert settings.local_storage_path == expected_path
