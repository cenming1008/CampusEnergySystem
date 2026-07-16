import ast
import os
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.core import database
from app.core.settings import Settings
from app.models.compensation import CapacitorBankControlProfile, CapacitorBankTelemetry

ROOT = Path(__file__).resolve().parents[1]
BASELINE = (
    ROOT
    / "migrations"
    / "versions"
    / "20260716_0001_campus_baseline.py"
)


def _baseline_table_columns(table_names=None):
    tree = ast.parse(BASELINE.read_text(encoding="utf-8"))
    result = {}
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "op"
            and node.func.attr == "create_table"
        ):
            continue
        table_name = ast.literal_eval(node.args[0])
        if table_names is not None and table_name not in table_names:
            continue
        result[table_name] = {
            ast.literal_eval(argument.args[0])
            for argument in node.args[1:]
            if isinstance(argument, ast.Call)
            and isinstance(argument.func, ast.Attribute)
            and argument.func.attr == "Column"
        }
    return result


class _FakeInspector:
    def __init__(self, tables=None, columns=None, indexes=None):
        self._tables = tables or []
        self._columns = columns or {}
        self._indexes = indexes or {}

    def get_table_names(self):
        return list(self._tables)

    def get_columns(self, table_name):
        return [{"name": column} for column in self._columns.get(table_name, [])]

    def get_indexes(self, table_name):
        return [{"name": index} for index in self._indexes.get(table_name, [])]


class DatabaseCoreTest(unittest.TestCase):
    def test_schema_mutation_settings_default_false_without_host_environment(self):
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "postgresql://tester:secret@localhost/test_db"},
            clear=True,
        ):
            runtime_settings = Settings(_env_file=None)

        self.assertFalse(runtime_settings.db_auto_create_tables)
        self.assertFalse(runtime_settings.db_runtime_schema_sync)

    def test_schema_mutation_settings_parse_boolean_environment_case_insensitively(self):
        for raw_value, expected in (
            ("True", True),
            ("true", True),
            ("FALSE", False),
            ("False", False),
        ):
            with self.subTest(raw_value=raw_value):
                with patch.dict(
                    os.environ,
                    {
                        "DATABASE_URL": "postgresql://tester:secret@localhost/test_db",
                        "DB_AUTO_CREATE_TABLES": raw_value,
                        "DB_RUNTIME_SCHEMA_SYNC": raw_value,
                    },
                    clear=True,
                ):
                    runtime_settings = Settings(_env_file=None)

                self.assertIs(runtime_settings.db_auto_create_tables, expected)
                self.assertIs(runtime_settings.db_runtime_schema_sync, expected)

    def test_schema_mutation_setting_descriptions_assign_schema_to_alembic(self):
        for field_name in ("db_auto_create_tables", "db_runtime_schema_sync"):
            description = Settings.__fields__[field_name].field_info.description or ""
            normalized = description.lower()

            with self.subTest(field_name=field_name):
                self.assertIn("true", normalized)
                self.assertIn("拒绝", description)
                self.assertIn("alembic", normalized)
                self.assertIn("schema", normalized)
                self.assertIn("管理", description)

    def test_environment_examples_disable_schema_mutation_flags(self):
        for filename in ("env.example", "env.local.example", "env.prod.example"):
            lines = (ROOT / filename).read_text(encoding="utf-8").splitlines()

            with self.subTest(filename=filename):
                self.assertIn("DB_AUTO_CREATE_TABLES=False", lines)
                self.assertIn("DB_RUNTIME_SCHEMA_SYNC=False", lines)
                self.assertNotIn("DB_AUTO_CREATE_TABLES=True", lines)
                self.assertNotIn("DB_RUNTIME_SCHEMA_SYNC=True", lines)

    def test_migration_readme_enforces_alembic_only_startup_guidance(self):
        readme = (ROOT / "migrations" / "README.md").read_text(encoding="utf-8")

        self.assertIn("DB_AUTO_CREATE_TABLES=False", readme)
        self.assertIn("DB_RUNTIME_SCHEMA_SYNC=False", readme)
        self.assertNotIn("DB_AUTO_CREATE_TABLES=True", readme)
        self.assertNotIn("DB_RUNTIME_SCHEMA_SYNC=True", readme)
        self.assertIn("20260716_0001", readme)
        self.assertIn("Alembic", readme)
        self.assertIn("alembic upgrade head", readme)
        self.assertIn("docs/archive/migrations/legacy-pre-20260716", readme)
        self.assertIn("Task 8", readme)
        self.assertNotRegex(readme, r"alembic\s+stamp\s+2026\d+")

    def test_lifecycle_reports_database_schema_validation_not_initialization(self):
        lifecycle = (ROOT / "app" / "core" / "lifecycle.py").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            'runtime_state.mark_service("database", "healthy", "validated")',
            lifecycle,
        )
        self.assertIn("数据库 schema 校验完成", lifecycle)
        self.assertNotIn('"database", "healthy", "initialized"', lifecycle)
        self.assertNotIn("数据库初始化完成", lifecycle)

    def test_capacitor_bank_models_and_baseline_include_required_runtime_columns(self):
        models = {
            "capacitor_bank_control_profile": CapacitorBankControlProfile,
            "capacitor_bank_telemetry": CapacitorBankTelemetry,
        }
        baseline_columns = _baseline_table_columns(models)

        self.assertEqual(set(baseline_columns), set(models))
        for table_name, model in models.items():
            required = database.REQUIRED_COLUMNS[table_name]
            self.assertLessEqual(required, set(model.__table__.columns.keys()))
            self.assertLessEqual(required, baseline_columns[table_name])

    def test_init_db_rejects_legacy_schema_mutation_flags(self):
        for auto_create, runtime_sync in ((True, False), (False, True), (True, True)):
            with self.subTest(
                db_auto_create_tables=auto_create,
                db_runtime_schema_sync=runtime_sync,
            ):
                with patch.object(database.settings, "db_auto_create_tables", auto_create):
                    with patch.object(database.settings, "db_runtime_schema_sync", runtime_sync):
                        with self.assertRaisesRegex(RuntimeError, "alembic upgrade head"):
                            database.init_db()

    def test_init_db_only_runs_schema_assertions_in_order(self):
        calls = []

        def record(name):
            return lambda: calls.append(name)

        with patch.object(database.settings, "db_auto_create_tables", False):
            with patch.object(database.settings, "db_runtime_schema_sync", False):
                with patch.object(
                    database,
                    "_assert_required_tables_exist",
                    side_effect=record("tables"),
                ) as mock_tables:
                    with patch.object(
                        database,
                        "_assert_required_columns_present",
                        side_effect=record("columns"),
                    ) as mock_columns:
                        with patch.object(
                            database,
                            "_assert_required_indexes_present",
                            side_effect=record("indexes"),
                        ) as mock_indexes:
                            with patch.object(
                                database,
                                "_assert_energydata_hypertable",
                                side_effect=record("hypertable"),
                            ) as mock_hypertable:
                                database.init_db()

        mock_tables.assert_called_once_with()
        mock_columns.assert_called_once_with()
        mock_indexes.assert_called_once_with()
        mock_hypertable.assert_called_once_with()
        self.assertEqual(calls, ["tables", "columns", "indexes", "hypertable"])

    def test_required_tables_match_static_baseline(self):
        baseline_tables = set(_baseline_table_columns())

        self.assertEqual(database.REQUIRED_TABLES, baseline_tables)

    def test_assert_required_tables_exist_raises_for_missing_table(self):
        inspector = _FakeInspector(tables=["alarm", "audit_event"])

        with patch.object(database, "inspect", return_value=inspector):
            with self.assertRaises(RuntimeError) as ctx:
                database._assert_required_tables_exist()

        self.assertIn("device", str(ctx.exception))

    def test_assert_required_columns_present_raises_for_missing_columns(self):
        inspector = _FakeInspector(
            tables=[
                "alarm",
                "device",
                "capacitor_bank_control_profile",
                "capacitor_bank_telemetry",
                "mqtt_ingestion_record",
                "user",
            ],
            columns={
                "alarm": ["severity"],
                "device": ["device_subtype"],
                "capacitor_bank_control_profile": ["source"],
                "capacitor_bank_telemetry": ["phase_a_circuit_running_count"],
                "mqtt_ingestion_record": ["raw_payload"],
                "user": ["role"],
            },
        )

        with patch.object(database, "inspect", return_value=inspector):
            with self.assertRaises(RuntimeError) as ctx:
                database._assert_required_columns_present()

        self.assertIn("alarm.category", str(ctx.exception))
        self.assertIn("capacitor_bank_control_profile.snapshot_timestamp", str(ctx.exception))
        self.assertIn("capacitor_bank_control_profile.running_circuit_count", str(ctx.exception))
        self.assertIn("capacitor_bank_telemetry.running_circuit_count", str(ctx.exception))
        self.assertIn("user.location_scope", str(ctx.exception))

    def test_assert_required_indexes_present_raises_for_missing_indexes(self):
        inspector = _FakeInspector(
            indexes={
                table_name: required_indexes
                for table_name, required_indexes in database.REQUIRED_INDEXES.items()
            }
        )
        inspector._indexes["energydata"] = {"idx_energydata_device_timestamp"}

        with patch.object(database, "inspect", return_value=inspector):
            with self.assertRaises(RuntimeError) as ctx:
                database._assert_required_indexes_present()

        self.assertIn("energydata.idx_energydata_energy_type_timestamp", str(ctx.exception))

    def test_assert_energydata_hypertable_raises_when_missing(self):
        connection = MagicMock()
        connection.execute.return_value.scalar_one_or_none.return_value = None

        @contextmanager
        def fake_connection():
            yield connection

        with patch.object(database.engine, "connect", side_effect=fake_connection):
            with self.assertRaisesRegex(
                RuntimeError,
                "energydata 尚未通过 migration 转换为 TimescaleDB hypertable",
            ):
                database._assert_energydata_hypertable()

        sql = str(connection.execute.call_args.args[0])
        self.assertIn("timescaledb_information.hypertables", sql)
        self.assertNotRegex(sql.upper(), r"\b(CREATE|ALTER|DROP|UPDATE|INSERT|DELETE)\b")

    def test_get_session_yields_session_from_context_manager(self):
        fake_session = object()

        @contextmanager
        def fake_session_factory(_engine):
            yield fake_session

        with patch.object(database, "Session", side_effect=fake_session_factory):
            session_gen = database.get_session()
            yielded = next(session_gen)

        self.assertIs(yielded, fake_session)

if __name__ == "__main__":
    unittest.main()
