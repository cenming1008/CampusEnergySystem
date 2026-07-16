import pytest

from scripts.python.migration_schema import (
    CONSTRAINTS_SQL,
    HYPERTABLE_SQL,
    INDEXES_SQL,
    PUBLIC_COLUMNS_SQL,
    MigrationVerificationError,
    collect_schema_fingerprint,
    compare_fingerprints,
    normalize_fingerprint,
    validate_temporary_database_name,
)


@pytest.mark.parametrize(
    "name",
    [
        "ces_migration_fresh",
        "ces_migration_offline",
        "ces_migration_roundtrip",
    ],
)
def test_accepts_only_fixed_temporary_database_names(name):
    assert validate_temporary_database_name(name) == name


@pytest.mark.parametrize(
    "name",
    ["campus_energy", "postgres", "ces_migration_", "ces_migration_bad-name"],
)
def test_rejects_unsafe_database_names(name):
    with pytest.raises(MigrationVerificationError):
        validate_temporary_database_name(name)


def test_fingerprint_normalization_is_order_independent():
    left = {
        "tables": [
            {"name": "device", "columns": [{"name": "id", "type": "integer"}]}
        ]
    }
    right = {
        "tables": [
            {"columns": [{"type": "INTEGER", "name": "id"}], "name": "device"}
        ]
    }

    assert normalize_fingerprint(left) == normalize_fingerprint(right)


def test_fingerprint_normalization_sorts_nested_lists_and_dictionary_keys():
    fingerprint = {
        "objects": {
            "second": {"columns": ["z", "a"], "type": "CHARACTER VARYING"},
            "first": {"enabled": True},
        }
    }

    normalized = normalize_fingerprint(fingerprint)

    assert list(normalized["objects"]) == ["first", "second"]
    assert normalized["objects"]["second"] == {
        "columns": ["a", "z"],
        "type": "character varying",
    }


def test_fingerprint_normalization_excludes_only_migration_and_internal_objects():
    fingerprint = {
        "tables": [
            {"kind": "table", "schema": "public", "name": "alembic_version"},
            {
                "kind": "table",
                "schema": "_timescaledb_internal",
                "name": "_hyper_1_1_chunk",
            },
            {"kind": "table", "schema": "public", "name": "device"},
            {"kind": "table", "schema": "audit", "name": "event"},
        ],
        "objects": {
            "table.alembic_version.column.version_num": {"kind": "column"},
            "table.device.column.alembic_version": {
                "kind": "column",
                "schema": "public",
                "table": "device",
            },
            "table._timescaledb_customer.column.id": {
                "kind": "column",
                "schema": "public",
                "table": "_timescaledb_customer",
            },
        },
    }

    assert normalize_fingerprint(fingerprint) == {
        "objects": {
            "table._timescaledb_customer.column.id": {
                "kind": "column",
                "schema": "public",
                "table": "_timescaledb_customer",
            },
            "table.device.column.alembic_version": {
                "kind": "column",
                "schema": "public",
                "table": "device",
            },
        },
        "tables": [
            {"kind": "table", "name": "device", "schema": "public"},
            {"kind": "table", "name": "event", "schema": "audit"},
        ]
    }


def test_comparison_reports_first_differing_object():
    with pytest.raises(MigrationVerificationError, match="device.archive_status"):
        compare_fingerprints(
            {"objects": {"device.archive_status": {"type": "varchar"}}},
            {"objects": {"device.archive_status": {"type": "text"}}},
        )


class FakeCursor:
    def __init__(self, rows_by_query):
        self.rows_by_query = rows_by_query
        self.rows = []
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query):
        self.executed.append(query)
        self.rows = self.rows_by_query[query]

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, rows_by_query):
        self.fake_cursor = FakeCursor(rows_by_query)

    def cursor(self):
        return self.fake_cursor


def test_collect_schema_fingerprint_maps_catalog_rows_to_stable_object_keys():
    connection = FakeConnection(
        {
            PUBLIC_COLUMNS_SQL: [
                ("device", "archive_status", "character varying", "varchar", "NO", None),
                ("alembic_version", "version_num", "character varying", "varchar", "NO", None),
            ],
            CONSTRAINTS_SQL: [
                (
                    1001,
                    "device",
                    "device_pkey",
                    "PRIMARY KEY",
                    "id",
                    None,
                    None,
                    None,
                    None,
                    1,
                    None,
                ),
                (
                    1002,
                    "device",
                    "device_location_id_fkey",
                    "FOREIGN KEY",
                    "location_id",
                    "location",
                    "id",
                    "NO ACTION",
                    "CASCADE",
                    1,
                    1,
                ),
            ],
            INDEXES_SQL: [
                (
                    "device",
                    "ix_device_archive_status",
                    "CREATE INDEX ix_device_archive_status ON public.device USING btree (archive_status)",
                )
            ],
            HYPERTABLE_SQL: [("energydata", 1)],
        }
    )

    fingerprint = collect_schema_fingerprint(connection)

    assert connection.fake_cursor.executed == [
        PUBLIC_COLUMNS_SQL,
        CONSTRAINTS_SQL,
        INDEXES_SQL,
        HYPERTABLE_SQL,
    ]
    assert set(fingerprint["objects"]) == {
        "table.device.column.archive_status",
        "table.device.constraint.device_location_id_fkey",
        "table.device.constraint.device_pkey",
        "table.device.index.ix_device_archive_status",
        "hypertable.energydata",
    }
    assert fingerprint["objects"]["table.device.column.archive_status"] == {
        "column_default": None,
        "data_type": "character varying",
        "is_nullable": "NO",
        "kind": "column",
        "table": "device",
        "udt_name": "varchar",
    }
    assert fingerprint["objects"]["table.device.constraint.device_location_id_fkey"] == {
        "column_mappings": [
            {
                "column": "location_id",
                "foreign_column": "id",
                "foreign_position": 1,
                "foreign_table": "location",
                "position": 1,
            }
        ],
        "columns": [{"name": "location_id", "position": 1}],
        "constraint_type": "FOREIGN KEY",
        "delete_rule": "CASCADE",
        "kind": "constraint",
        "table": "device",
        "update_rule": "NO ACTION",
    }
    assert fingerprint["objects"]["hypertable.energydata"] == {
        "kind": "hypertable",
        "num_dimensions": 1,
        "table": "energydata",
    }


def test_collect_schema_fingerprint_is_json_serializable():
    connection = FakeConnection(
        {
            PUBLIC_COLUMNS_SQL: [],
            CONSTRAINTS_SQL: [],
            INDEXES_SQL: [],
            HYPERTABLE_SQL: [],
        }
    )

    import json

    json.dumps(collect_schema_fingerprint(connection), sort_keys=True)


def test_collect_schema_fingerprint_preserves_composite_foreign_key_pairing():
    def fingerprint_for(references):
        rows = [
            (
                2001,
                "child",
                "child_parent_fkey",
                "FOREIGN KEY",
                local_column,
                "parent",
                foreign_column,
                "NO ACTION",
                "NO ACTION",
                position,
                foreign_position,
            )
            for position, (local_column, foreign_column, foreign_position) in enumerate(
                references, start=1
            )
        ]
        return collect_schema_fingerprint(
            FakeConnection(
                {
                    PUBLIC_COLUMNS_SQL: [],
                    CONSTRAINTS_SQL: rows,
                    INDEXES_SQL: [],
                    HYPERTABLE_SQL: [],
                }
            )
        )

    direct = fingerprint_for([("a", "x", 1), ("b", "y", 2)])
    crossed = fingerprint_for([("a", "y", 2), ("b", "x", 1)])

    assert direct != crossed
    assert direct["objects"]["table.child.constraint.child_parent_fkey"][
        "column_mappings"
    ] == [
        {
            "column": "a",
            "foreign_column": "x",
            "foreign_position": 1,
            "foreign_table": "parent",
            "position": 1,
        },
        {
            "column": "b",
            "foreign_column": "y",
            "foreign_position": 2,
            "foreign_table": "parent",
            "position": 2,
        },
    ]


def test_collect_schema_fingerprint_deduplicates_constraint_catalog_rows():
    duplicate_row = (
        3001,
        "child",
        "child_parent_fkey",
        "FOREIGN KEY",
        "parent_id",
        "parent",
        "id",
        "NO ACTION",
        "CASCADE",
        1,
        1,
    )
    fingerprint = collect_schema_fingerprint(
        FakeConnection(
            {
                PUBLIC_COLUMNS_SQL: [],
                CONSTRAINTS_SQL: [duplicate_row, duplicate_row],
                INDEXES_SQL: [],
                HYPERTABLE_SQL: [],
            }
        )
    )

    constraint = fingerprint["objects"]["table.child.constraint.child_parent_fkey"]
    assert len(constraint["columns"]) == 1
    assert len(constraint["column_mappings"]) == 1


@pytest.mark.parametrize("constraint_type", ["PRIMARY KEY", "UNIQUE"])
def test_non_foreign_constraints_do_not_contain_foreign_columns(constraint_type):
    fingerprint = collect_schema_fingerprint(
        FakeConnection(
            {
                PUBLIC_COLUMNS_SQL: [],
                CONSTRAINTS_SQL: [
                    (
                        3101,
                        "device",
                        "device_identity_key",
                        constraint_type,
                        "id",
                        None,
                        None,
                        None,
                        None,
                        1,
                        None,
                    )
                ],
                INDEXES_SQL: [],
                HYPERTABLE_SQL: [],
            }
        )
    )

    constraint = fingerprint["objects"]["table.device.constraint.device_identity_key"]
    assert constraint["columns"] == [{"name": "id", "position": 1}]
    assert "foreign_columns" not in constraint
    assert "column_mappings" not in constraint


def test_constraints_query_pairs_columns_by_constraint_array_ordinality():
    assert "unnest(con.conkey) WITH ORDINALITY" in CONSTRAINTS_SQL
    assert "con.confkey[local_key.ordinality::integer]" in CONSTRAINTS_SQL


def test_same_named_constraints_on_different_tables_remain_isolated_by_oid():
    fingerprint = collect_schema_fingerprint(
        FakeConnection(
            {
                PUBLIC_COLUMNS_SQL: [],
                CONSTRAINTS_SQL: [
                    (
                        4101,
                        "first_child",
                        "shared_parent_fkey",
                        "FOREIGN KEY",
                        "first_parent_id",
                        "first_parent",
                        "id",
                        "NO ACTION",
                        "CASCADE",
                        1,
                        1,
                    ),
                    (
                        4201,
                        "second_child",
                        "shared_parent_fkey",
                        "FOREIGN KEY",
                        "second_parent_code",
                        "second_parent",
                        "code",
                        "NO ACTION",
                        "RESTRICT",
                        1,
                        1,
                    ),
                ],
                INDEXES_SQL: [],
                HYPERTABLE_SQL: [],
            }
        )
    )

    first = fingerprint["objects"][
        "table.first_child.constraint.shared_parent_fkey"
    ]
    second = fingerprint["objects"][
        "table.second_child.constraint.shared_parent_fkey"
    ]
    assert first["column_mappings"][0]["foreign_table"] == "first_parent"
    assert first["column_mappings"][0]["foreign_column"] == "id"
    assert second["column_mappings"][0]["foreign_table"] == "second_parent"
    assert second["column_mappings"][0]["foreign_column"] == "code"


def test_constraints_query_uses_pg_constraint_oid_relationships():
    assert "pg_catalog.pg_constraint" in CONSTRAINTS_SQL
    assert "con.oid AS constraint_oid" in CONSTRAINTS_SQL
    assert "con.conrelid" in CONSTRAINTS_SQL
    assert "con.confrelid" in CONSTRAINTS_SQL
    assert "unnest(con.conkey) WITH ORDINALITY" in CONSTRAINTS_SQL
    assert "con.confkey[" in CONSTRAINTS_SQL
    assert "information_schema" not in CONSTRAINTS_SQL
