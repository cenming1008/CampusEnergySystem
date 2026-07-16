import ast
import os
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.core import database
from app.models.compensation import CapacitorBankControlProfile, CapacitorBankTelemetry

BASELINE = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "20260716_0001_campus_baseline.py"
)


def _baseline_table_columns(table_names):
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
        if table_name not in table_names:
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
    def __init__(self, tables=None, columns=None):
        self._tables = tables or []
        self._columns = columns or {}

    def get_table_names(self):
        return list(self._tables)

    def get_columns(self, table_name):
        return [{"name": column} for column in self._columns.get(table_name, [])]


class DatabaseCoreTest(unittest.TestCase):
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

    def test_init_db_runs_runtime_sync_when_enabled(self):
        with patch.object(database.settings, "db_auto_create_tables", True):
            with patch.object(database.settings, "db_runtime_schema_sync", True):
                with patch.object(database.SQLModel.metadata, "create_all") as mock_create_all:
                    with patch.object(database, "_sync_runtime_schema") as mock_sync:
                        with patch.object(database, "_ensure_runtime_indexes") as mock_indexes:
                            with patch.object(database, "_try_enable_timescaledb_hypertable") as mock_hypertable:
                                database.init_db()

        mock_create_all.assert_called_once_with(database.engine)
        mock_sync.assert_called_once()
        mock_indexes.assert_called_once()
        mock_hypertable.assert_called_once()

    def test_init_db_asserts_schema_when_runtime_sync_disabled(self):
        with patch.object(database.settings, "db_auto_create_tables", False):
            with patch.object(database.settings, "db_runtime_schema_sync", False):
                with patch.object(database, "_assert_required_tables_exist") as mock_tables:
                    with patch.object(database, "_assert_required_columns_present") as mock_columns:
                        with patch.object(database, "_try_enable_timescaledb_hypertable") as mock_hypertable:
                            database.init_db()

        mock_tables.assert_called_once()
        mock_columns.assert_called_once()
        mock_hypertable.assert_called_once()

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

    def test_get_session_yields_session_from_context_manager(self):
        fake_session = object()

        @contextmanager
        def fake_session_factory(_engine):
            yield fake_session

        with patch.object(database, "Session", side_effect=fake_session_factory):
            session_gen = database.get_session()
            yielded = next(session_gen)

        self.assertIs(yielded, fake_session)

    def test_try_enable_timescaledb_hypertable_swallows_errors(self):
        fake_session = MagicMock()
        fake_session.exec.side_effect = RuntimeError("timescaledb missing")

        @contextmanager
        def fake_session_factory(_engine):
            yield fake_session

        with patch.object(database, "Session", side_effect=fake_session_factory):
            database._try_enable_timescaledb_hypertable()

        fake_session.exec.assert_called_once()


if __name__ == "__main__":
    unittest.main()
