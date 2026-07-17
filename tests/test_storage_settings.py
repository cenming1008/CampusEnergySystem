import os
from pathlib import Path
from unittest.mock import patch

from app.core.settings import Settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_storage_automation_and_simulation_are_default_off():
    with patch.dict(
        os.environ,
        {"DATABASE_URL": "postgresql://tester:secret@localhost/test_db"},
        clear=True,
    ):
        settings = Settings(_env_file=None)

    assert settings.storage_ems_enabled is False
    assert settings.storage_simulation_enabled is False
    assert settings.storage_simulation_topic_prefix == "campus/simulation/"
    assert settings.storage_daily_dispatch_time == "00:05"


def test_storage_settings_can_be_explicitly_enabled_and_overridden():
    with patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql://tester:secret@localhost/test_db",
            "STORAGE_EMS_ENABLED": "true",
            "STORAGE_SIMULATION_ENABLED": "true",
            "STORAGE_SIMULATION_TOPIC_PREFIX": "test/simulation/",
            "STORAGE_DAILY_DISPATCH_TIME": "01:30",
        },
        clear=True,
    ):
        settings = Settings(_env_file=None)

    assert settings.storage_ems_enabled is True
    assert settings.storage_simulation_enabled is True
    assert settings.storage_simulation_topic_prefix == "test/simulation/"
    assert settings.storage_daily_dispatch_time == "01:30"


def test_all_environment_examples_keep_storage_features_default_off():
    for filename in ("env.example", "env.local.example", "env.prod.example"):
        content = (PROJECT_ROOT / filename).read_text(encoding="utf-8")
        assert "STORAGE_EMS_ENABLED=False" in content
        assert "STORAGE_SIMULATION_ENABLED=False" in content
        assert "STORAGE_SIMULATION_TOPIC_PREFIX=campus/simulation/" in content
        assert "STORAGE_DAILY_DISPATCH_TIME=00:05" in content
