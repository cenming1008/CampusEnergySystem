"""Deterministic schema fingerprints for isolated migration verification."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

TEMP_DATABASE_NAMES = frozenset(
    {
        "ces_migration_fresh",
        "ces_migration_offline",
        "ces_migration_roundtrip",
    }
)


class MigrationVerificationError(RuntimeError):
    """Raised when migration verification cannot proceed safely."""


def validate_temporary_database_name(name: str) -> str:
    """Accept only the three disposable databases reserved by the migration plan."""
    if name not in TEMP_DATABASE_NAMES:
        raise MigrationVerificationError(
            f"refusing database outside fixed migration set: {name!r}"
        )
    return name


PUBLIC_COLUMNS_SQL = """
SELECT table_name, column_name, data_type, udt_name, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name <> 'alembic_version'
ORDER BY table_name, ordinal_position
"""

CONSTRAINTS_SQL = """
SELECT tc.table_name, tc.constraint_name, tc.constraint_type,
       kcu.column_name, ccu.table_name AS foreign_table,
       ccu.column_name AS foreign_column,
       rc.update_rule, rc.delete_rule
FROM information_schema.table_constraints tc
LEFT JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
LEFT JOIN information_schema.constraint_column_usage ccu
  ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
LEFT JOIN information_schema.referential_constraints rc
  ON tc.constraint_name = rc.constraint_name AND tc.constraint_schema = rc.constraint_schema
WHERE tc.table_schema = 'public'
ORDER BY tc.table_name, tc.constraint_name, kcu.ordinal_position
"""

INDEXES_SQL = """
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname
"""

HYPERTABLE_SQL = """
SELECT hypertable_name, num_dimensions
FROM timescaledb_information.hypertables
WHERE hypertable_schema = 'public'
ORDER BY hypertable_name
"""

_POSTGRES_TYPE_KEYS = frozenset({"type", "data_type", "udt_name"})


def _is_excluded_record(value: Mapping[str, Any]) -> bool:
    schema = value.get("schema", value.get("table_schema", value.get("schema_name")))
    if isinstance(schema, str) and schema.startswith("_timescaledb_"):
        return True

    table = value.get("table", value.get("table_name", value.get("name")))
    return table == "alembic_version"


def _is_excluded_object_key(key: str) -> bool:
    segments = key.split(".")
    return "alembic_version" in segments or any(
        segment.startswith("_timescaledb_") for segment in segments
    )


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _normalize(value: Any, *, parent_key: str | None = None) -> Any:
    if isinstance(value, Mapping):
        normalized_items = []
        for key, child in value.items():
            key_string = str(key)
            if _is_excluded_object_key(key_string):
                continue
            if isinstance(child, Mapping) and _is_excluded_record(child):
                continue
            normalized_items.append(
                (key_string, _normalize(child, parent_key=key_string))
            )
        return dict(sorted(normalized_items))

    if isinstance(value, (list, tuple)):
        normalized_values = [
            _normalize(item, parent_key=parent_key)
            for item in value
            if not (isinstance(item, Mapping) and _is_excluded_record(item))
        ]
        return sorted(normalized_values, key=_canonical_json)

    if isinstance(value, str) and parent_key in _POSTGRES_TYPE_KEYS:
        return value.lower()

    return value


def normalize_fingerprint(fingerprint: Mapping[str, Any]) -> dict[str, Any]:
    """Return a recursively ordered, JSON-serializable schema fingerprint."""
    normalized = _normalize(fingerprint)
    if not isinstance(normalized, dict):  # Defensive guard for the public contract.
        raise MigrationVerificationError("schema fingerprint must be a mapping")
    return normalized


def _first_differing_path(left: Any, right: Any, path: str = "fingerprint") -> str:
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        for key in sorted(set(left) | set(right)):
            child_path = key if path == "fingerprint" else f"{path}.{key}"
            if key not in left or key not in right:
                return child_path
            if left[key] != right[key]:
                return _first_differing_path(left[key], right[key], child_path)
    elif isinstance(left, list) and isinstance(right, list):
        for index, (left_item, right_item) in enumerate(zip(left, right)):
            if left_item != right_item:
                return _first_differing_path(
                    left_item, right_item, f"{path}[{index}]"
                )
        if len(left) != len(right):
            return f"{path}[{min(len(left), len(right))}]"
    return path


def compare_fingerprints(
    left: Mapping[str, Any], right: Mapping[str, Any]
) -> None:
    """Raise with the first stable object name when two schemas differ."""
    normalized_left = normalize_fingerprint(left)
    normalized_right = normalize_fingerprint(right)
    if normalized_left == normalized_right:
        return

    left_objects = normalized_left.get("objects")
    right_objects = normalized_right.get("objects")
    if isinstance(left_objects, Mapping) and isinstance(right_objects, Mapping):
        for object_name in sorted(set(left_objects) | set(right_objects)):
            if left_objects.get(object_name) != right_objects.get(object_name):
                raise MigrationVerificationError(
                    f"schema fingerprints differ at object {object_name}"
                )

    difference = _first_differing_path(normalized_left, normalized_right)
    raise MigrationVerificationError(f"schema fingerprints differ at {difference}")


def _add_unique(values: list[str], value: str | None) -> None:
    if value is not None and value not in values:
        values.append(value)


def collect_schema_fingerprint(connection: Any) -> dict[str, Any]:
    """Read public PostgreSQL and Timescale catalog objects into stable keys."""
    objects: dict[str, dict[str, Any]] = {}

    with connection.cursor() as cursor:
        cursor.execute(PUBLIC_COLUMNS_SQL)
        for table, column, data_type, udt_name, nullable, default in cursor.fetchall():
            if table == "alembic_version":
                continue
            objects[f"table.{table}.column.{column}"] = {
                "kind": "column",
                "table": table,
                "data_type": data_type,
                "udt_name": udt_name,
                "is_nullable": nullable,
                "column_default": default,
            }

        cursor.execute(CONSTRAINTS_SQL)
        for row in cursor.fetchall():
            (
                table,
                constraint_name,
                constraint_type,
                column,
                foreign_table,
                foreign_column,
                update_rule,
                delete_rule,
            ) = row
            if table == "alembic_version":
                continue
            key = f"table.{table}.constraint.{constraint_name}"
            constraint = objects.setdefault(
                key,
                {
                    "kind": "constraint",
                    "table": table,
                    "constraint_type": constraint_type,
                    "columns": [],
                    "foreign_columns": [],
                    "update_rule": update_rule,
                    "delete_rule": delete_rule,
                },
            )
            _add_unique(constraint["columns"], column)
            foreign_reference = (
                f"{foreign_table}.{foreign_column}"
                if foreign_table is not None and foreign_column is not None
                else None
            )
            _add_unique(constraint["foreign_columns"], foreign_reference)

        cursor.execute(INDEXES_SQL)
        for table, index_name, index_definition in cursor.fetchall():
            if table == "alembic_version":
                continue
            objects[f"table.{table}.index.{index_name}"] = {
                "kind": "index",
                "table": table,
                "definition": index_definition,
            }

        cursor.execute(HYPERTABLE_SQL)
        for table, dimensions in cursor.fetchall():
            if table == "alembic_version":
                continue
            objects[f"hypertable.{table}"] = {
                "kind": "hypertable",
                "table": table,
                "num_dimensions": dimensions,
            }

    return normalize_fingerprint({"objects": objects})
