"""数据库连接与启动时 schema 校验。

数据库结构只由 Alembic migration 管理。应用启动只读取并校验既有结构，
不会创建表、补字段、补索引或转换 TimescaleDB hypertable。
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import inspect
from sqlmodel import Session, create_engine, text

from app.core.settings import settings

CAPACITOR_BANK_CONTROL_PROFILE_REQUIRED_COLUMNS = {
    "source",
    "snapshot_timestamp",
    "phase_a_circuit_total_count",
    "phase_b_circuit_total_count",
    "phase_c_circuit_total_count",
    "common_1_circuit_total_count",
    "common_2_circuit_total_count",
    "common_3_circuit_total_count",
    "phase_a_capacity_steps_kvar_json",
    "phase_b_capacity_steps_kvar_json",
    "phase_c_capacity_steps_kvar_json",
    "common_1_capacity_steps_kvar_json",
    "common_2_capacity_steps_kvar_json",
    "common_3_capacity_steps_kvar_json",
    "phase_a_circuit_running_count",
    "phase_b_circuit_running_count",
    "phase_c_circuit_running_count",
    "common_group_1_running_count",
    "common_group_2_running_count",
    "common_group_3_running_count",
    "split_circuit_running_count",
    "common_circuit_running_count",
    "running_circuit_count",
    "control_mode",
    "auto_on_elapsed_seconds",
    "auto_off_elapsed_seconds",
    "last_auto_action",
}

CAPACITOR_BANK_TELEMETRY_REQUIRED_COLUMNS = {
    "phase_a_circuit_running_count",
    "phase_b_circuit_running_count",
    "phase_c_circuit_running_count",
    "common_group_1_running_count",
    "common_group_2_running_count",
    "common_group_3_running_count",
    "split_circuit_running_count",
    "common_circuit_running_count",
    "running_circuit_count",
    "control_mode",
    "auto_on_elapsed_seconds",
    "auto_off_elapsed_seconds",
    "last_auto_action",
}

REQUIRED_TABLES = {
    "alarm",
    "audit_event",
    "capacitor_bank_control_profile",
    "capacitor_bank_telemetry",
    "carbon_emission",
    "device",
    "device_control_log",
    "device_group",
    "device_group_membership",
    "device_ingestion_health",
    "device_maintenance",
    "energy_statistics",
    "energydata",
    "inspection_plan",
    "inspection_point",
    "inspection_record",
    "inspection_route",
    "inspection_task",
    "location",
    "mqtt_ingestion_record",
    "storage_telemetry",
    "svg_asset_profile",
    "svg_config",
    "svg_telemetry",
    "user",
}

REQUIRED_COLUMNS = {
    "energydata": {"reactive_power"},
    "device": {"device_subtype", "archive_status"},
    "svg_asset_profile": {
        "model_number",
        "rated_voltage",
        "rated_frequency",
        "comm_address",
        "software_version",
        "hardware_version",
        "protocol_version",
        "module_count",
        "single_module_capacity",
    },
    "capacitor_bank_control_profile": CAPACITOR_BANK_CONTROL_PROFILE_REQUIRED_COLUMNS,
    "capacitor_bank_telemetry": CAPACITOR_BANK_TELEMETRY_REQUIRED_COLUMNS,
    "alarm": {
        "severity",
        "category",
        "source",
        "instance_key",
        "last_seen_at",
        "recovered_at",
        "resolved_at",
        "resolved_by",
        "handling_note",
    },
    "mqtt_ingestion_record": {
        "raw_payload",
        "retry_count",
        "next_retry_at",
        "replay_count",
        "last_replayed_at",
    },
    "user": {
        "role",
        "location_scope",
        "must_change_password",
        "failed_login_attempts",
        "locked_until",
        "token_version",
        "last_login_at",
        "last_password_changed_at",
    },
}

REQUIRED_INDEXES = {
    "alarm": {"ix_alarm_device_id", "idx_alarm_device_resolved_timestamp"},
    "device": {
        "ix_device_sn",
        "ix_device_device_category",
        "ix_device_archive_status",
    },
    "energydata": {
        "idx_energydata_device_timestamp",
        "idx_energydata_energy_type_timestamp",
    },
    "mqtt_ingestion_record": {
        "ix_mqtt_ingestion_record_fingerprint",
        "idx_mqtt_ingestion_record_next_retry_at",
    },
}


engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
)


def init_db() -> None:
    """校验 migration 已完整建立应用启动所需的数据库结构。"""
    if settings.db_auto_create_tables or settings.db_runtime_schema_sync:
        raise RuntimeError(
            "启动时 schema mutation 已禁用；请设置 "
            "DB_AUTO_CREATE_TABLES=False、DB_RUNTIME_SCHEMA_SYNC=False，"
            "然后执行 alembic upgrade head"
        )

    _assert_required_tables_exist()
    _assert_required_columns_present()
    _assert_required_indexes_present()
    _assert_energydata_hypertable()


def _assert_required_tables_exist() -> None:
    """验证静态根 migration 定义的 25 张业务表全部存在。"""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    missing_tables = sorted(REQUIRED_TABLES - existing_tables)
    if missing_tables:
        raise RuntimeError(
            "数据库缺少关键表，请先执行 alembic upgrade head 后再启动应用: "
            + ", ".join(missing_tables)
        )


def _assert_required_columns_present() -> None:
    """验证应用依赖的关键字段已由 migration 创建。"""
    inspector = inspect(engine)
    missing_fields: list[str] = []
    for table_name, columns in REQUIRED_COLUMNS.items():
        existing_columns = {
            column["name"] for column in inspector.get_columns(table_name)
        }
        missing = sorted(columns - existing_columns)
        missing_fields.extend(f"{table_name}.{column}" for column in missing)
    if missing_fields:
        raise RuntimeError(
            "数据库 schema 与当前应用不兼容，请先执行 alembic upgrade head: "
            + ", ".join(missing_fields)
        )


def _assert_required_indexes_present() -> None:
    """验证关键查询索引已由 migration 创建。"""
    inspector = inspect(engine)
    missing_indexes: list[str] = []
    for table_name, indexes in REQUIRED_INDEXES.items():
        existing_indexes = {
            index["name"] for index in inspector.get_indexes(table_name)
        }
        missing = sorted(indexes - existing_indexes)
        missing_indexes.extend(f"{table_name}.{index}" for index in missing)
    if missing_indexes:
        raise RuntimeError(
            "数据库缺少关键索引，请先执行 alembic upgrade head: "
            + ", ".join(missing_indexes)
        )


def _assert_energydata_hypertable() -> None:
    """只读验证 energydata 已由 migration 转换为 hypertable。"""
    query = text(
        "SELECT 1 FROM timescaledb_information.hypertables "
        "WHERE hypertable_schema = 'public' "
        "AND hypertable_name = 'energydata' LIMIT 1"
    )
    with engine.connect() as connection:
        found = connection.execute(query).scalar_one_or_none()
    if found is None:
        raise RuntimeError(
            "energydata 尚未通过 migration 转换为 TimescaleDB hypertable"
        )


def get_session() -> Generator[Session, None, None]:
    """FastAPI 依赖注入：获取数据库 Session。"""
    with Session(engine) as session:
        yield session
