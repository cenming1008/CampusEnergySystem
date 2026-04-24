import unittest
import warnings
from types import SimpleNamespace

from app.core.startup_checks import validate_runtime_configuration


class StartupChecksTest(unittest.TestCase):
    def test_production_rejects_risky_startup_flags(self):
        settings = SimpleNamespace(
            strict_startup_checks=True,
            is_production=True,
            debug=True,
            reload=False,
            secret_key="mine-energy-system-secret-key-change-me",
            db_auto_create_tables=True,
            db_runtime_schema_sync=False,
            force_https=False,
            websocket_auth_mode="disabled",
            monitoring_access_mode="public",
            trusted_hosts=["*"],
            cors_origins=["*"],
        )

        with self.assertRaises(RuntimeError):
            validate_runtime_configuration(settings)

    def test_development_allows_relaxed_flags(self):
        settings = SimpleNamespace(
            strict_startup_checks=True,
            is_production=False,
            debug=True,
            reload=True,
            secret_key="mine-energy-system-secret-key-change-me",
            db_auto_create_tables=True,
            db_runtime_schema_sync=True,
            force_https=False,
            websocket_auth_mode="disabled",
            monitoring_access_mode="public",
            trusted_hosts=["*"],
            cors_origins=["*"],
        )

        validate_runtime_configuration(settings)

    def test_sqlite_warns_when_compensation_parameter_write_enabled(self):
        settings = SimpleNamespace(
            strict_startup_checks=True,
            is_production=False,
            database_url="sqlite:///tmp/campus.db",
            compensation_capacitor_bank_parameter_write_enabled=True,
        )

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            validate_runtime_configuration(settings)

        self.assertTrue(
            any("SQLite" in str(item.message) and "补偿器参数写入" in str(item.message) for item in captured)
        )
