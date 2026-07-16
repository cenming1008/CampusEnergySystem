import unittest
import warnings
from types import SimpleNamespace

from app.core.startup_checks import validate_runtime_configuration


class StartupChecksTest(unittest.TestCase):
    def test_strict_startup_checks_reject_schema_mutation_flags_in_all_environments(self):
        for is_production in (False, True):
            for auto_create, runtime_sync in ((True, False), (False, True), (True, True)):
                settings = SimpleNamespace(
                    strict_startup_checks=True,
                    is_production=is_production,
                    debug=False,
                    reload=False,
                    secret_key="strong-random-secret-key-value-1234567890",
                    db_auto_create_tables=auto_create,
                    db_runtime_schema_sync=runtime_sync,
                    force_https=True,
                    websocket_auth_mode="required",
                    monitoring_access_mode="authenticated",
                    trusted_hosts=["campus.example.com"],
                    cors_origins=["https://campus.example.com"],
                    mqtt_username="ingest-worker",
                    mqtt_password="secret",
                )

                with self.subTest(
                    is_production=is_production,
                    db_auto_create_tables=auto_create,
                    db_runtime_schema_sync=runtime_sync,
                ):
                    with self.assertRaisesRegex(RuntimeError, "alembic upgrade head"):
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
