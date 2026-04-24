"""
数据库连接与初始化

- 使用 SQLModel 管理 ORM
- 开发环境可自动 create_all / 运行时补齐字段
- 生产环境默认要求通过版本化 migration 管理表结构
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import inspect
from sqlmodel import Session, SQLModel, create_engine, text

from app.core.logger import logger
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

REQUIRED_COLUMNS = {
    "energydata": {"reactive_power"},
    "device": {"device_subtype"},
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
    "mqtt_ingestion_record": {"raw_payload", "retry_count", "next_retry_at", "replay_count", "last_replayed_at"},
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
    """初始化数据库表结构，并尝试开启 TimescaleDB hypertable 优化。"""
    if settings.db_auto_create_tables:
        SQLModel.metadata.create_all(engine)
    else:
        _assert_required_tables_exist()

    if settings.db_runtime_schema_sync:
        _sync_runtime_schema()
        _ensure_runtime_indexes()
    else:
        _assert_required_columns_present()

    _try_enable_timescaledb_hypertable()


def _sync_runtime_schema() -> None:
    """为已有数据库补齐新增列，避免 create_all 不更新旧表结构。"""
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    with Session(engine) as session:
        if "alarm" in table_names:
            existing_columns = {column["name"] for column in inspector.get_columns("alarm")}
            alarm_column_sql = {
                "severity": "ALTER TABLE alarm ADD COLUMN severity VARCHAR(32) DEFAULT 'warning'",
                "category": "ALTER TABLE alarm ADD COLUMN category VARCHAR(64) DEFAULT 'threshold'",
                "source": "ALTER TABLE alarm ADD COLUMN source VARCHAR(64) DEFAULT 'telemetry'",
                "instance_key": "ALTER TABLE alarm ADD COLUMN instance_key VARCHAR(255) NULL",
                "last_seen_at": "ALTER TABLE alarm ADD COLUMN last_seen_at TIMESTAMP NULL",
                "recovered_at": "ALTER TABLE alarm ADD COLUMN recovered_at TIMESTAMP NULL",
                "resolved_at": "ALTER TABLE alarm ADD COLUMN resolved_at TIMESTAMP NULL",
                "resolved_by": "ALTER TABLE alarm ADD COLUMN resolved_by VARCHAR(255) NULL",
                "handling_note": "ALTER TABLE alarm ADD COLUMN handling_note TEXT NULL",
            }
            for column_name, sql in alarm_column_sql.items():
                if column_name not in existing_columns:
                    logger.info(f"Schema sync: adding alarm.{column_name}")
                    session.exec(text(sql))

        if "device_control_log" not in table_names:
            # 新表由 create_all 创建；这里不需要额外处理。
            pass

        if "mqtt_ingestion_record" in table_names:
            existing_columns = {column["name"] for column in inspector.get_columns("mqtt_ingestion_record")}
            if "raw_payload" not in existing_columns:
                logger.info("Schema sync: adding mqtt_ingestion_record.raw_payload")
                session.exec(text("ALTER TABLE mqtt_ingestion_record ADD COLUMN raw_payload TEXT NULL"))
            if "retry_count" not in existing_columns:
                logger.info("Schema sync: adding mqtt_ingestion_record.retry_count")
                session.exec(text("ALTER TABLE mqtt_ingestion_record ADD COLUMN retry_count INTEGER DEFAULT 0"))
            if "next_retry_at" not in existing_columns:
                logger.info("Schema sync: adding mqtt_ingestion_record.next_retry_at")
                session.exec(text("ALTER TABLE mqtt_ingestion_record ADD COLUMN next_retry_at TIMESTAMP NULL"))
            if "replay_count" not in existing_columns:
                logger.info("Schema sync: adding mqtt_ingestion_record.replay_count")
                session.exec(text("ALTER TABLE mqtt_ingestion_record ADD COLUMN replay_count INTEGER DEFAULT 0"))
            if "last_replayed_at" not in existing_columns:
                logger.info("Schema sync: adding mqtt_ingestion_record.last_replayed_at")
                session.exec(text("ALTER TABLE mqtt_ingestion_record ADD COLUMN last_replayed_at TIMESTAMP NULL"))

        if "energydata" in table_names:
            existing_columns = {column["name"] for column in inspector.get_columns("energydata")}
            if "reactive_power" not in existing_columns:
                logger.info("Schema sync: adding energydata.reactive_power")
                session.exec(text("ALTER TABLE energydata ADD COLUMN reactive_power DOUBLE PRECISION NULL"))

        if "device" in table_names:
            existing_columns = {column["name"] for column in inspector.get_columns("device")}
            if "device_subtype" not in existing_columns:
                logger.info("Schema sync: adding device.device_subtype")
                session.exec(text("ALTER TABLE device ADD COLUMN device_subtype VARCHAR(64) NULL"))
                session.exec(
                    text(
                        """
                        UPDATE device
                        SET device_subtype = CASE
                            WHEN device_type = 'reactive_power_compensator' THEN 'capacitor_bank_controller'
                            WHEN device_type = 'compensation' THEN 'capacitor_bank_controller'
                            WHEN device_type = 'capacitor_bank_controller' THEN 'capacitor_bank_controller'
                            WHEN device_type = 'svg' THEN 'svg'
                            ELSE NULL
                        END
                        WHERE device_subtype IS NULL
                        """
                    )
                )

        if "svg_asset_profile" in table_names:
            existing_columns = {column["name"] for column in inspector.get_columns("svg_asset_profile")}
            svg_profile_column_sql = {
                "model_number": "ALTER TABLE svg_asset_profile ADD COLUMN model_number VARCHAR NULL",
                "rated_voltage": "ALTER TABLE svg_asset_profile ADD COLUMN rated_voltage DOUBLE PRECISION NULL",
                "rated_frequency": "ALTER TABLE svg_asset_profile ADD COLUMN rated_frequency DOUBLE PRECISION NULL",
                "comm_address": "ALTER TABLE svg_asset_profile ADD COLUMN comm_address VARCHAR NULL",
                "software_version": "ALTER TABLE svg_asset_profile ADD COLUMN software_version VARCHAR NULL",
                "hardware_version": "ALTER TABLE svg_asset_profile ADD COLUMN hardware_version VARCHAR NULL",
                "protocol_version": "ALTER TABLE svg_asset_profile ADD COLUMN protocol_version VARCHAR NULL",
                "module_count": "ALTER TABLE svg_asset_profile ADD COLUMN module_count INTEGER NULL",
                "single_module_capacity": "ALTER TABLE svg_asset_profile ADD COLUMN single_module_capacity DOUBLE PRECISION NULL",
            }
            for column_name, sql in svg_profile_column_sql.items():
                if column_name not in existing_columns:
                    logger.info(f"Schema sync: adding svg_asset_profile.{column_name}")
                    session.exec(text(sql))

        if "capacitor_bank_control_profile" in table_names:
            existing_columns = {column["name"] for column in inspector.get_columns("capacitor_bank_control_profile")}
            cap_profile_column_sql = {
                "source": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN source VARCHAR NULL",
                "snapshot_timestamp": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN snapshot_timestamp TIMESTAMP NULL",
                "phase_a_circuit_total_count": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN phase_a_circuit_total_count INTEGER NULL",
                "phase_b_circuit_total_count": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN phase_b_circuit_total_count INTEGER NULL",
                "phase_c_circuit_total_count": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN phase_c_circuit_total_count INTEGER NULL",
                "common_1_circuit_total_count": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN common_1_circuit_total_count INTEGER NULL",
                "common_2_circuit_total_count": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN common_2_circuit_total_count INTEGER NULL",
                "common_3_circuit_total_count": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN common_3_circuit_total_count INTEGER NULL",
                "phase_a_capacity_steps_kvar_json": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN phase_a_capacity_steps_kvar_json TEXT NULL",
                "phase_b_capacity_steps_kvar_json": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN phase_b_capacity_steps_kvar_json TEXT NULL",
                "phase_c_capacity_steps_kvar_json": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN phase_c_capacity_steps_kvar_json TEXT NULL",
                "common_1_capacity_steps_kvar_json": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN common_1_capacity_steps_kvar_json TEXT NULL",
                "common_2_capacity_steps_kvar_json": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN common_2_capacity_steps_kvar_json TEXT NULL",
                "common_3_capacity_steps_kvar_json": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN common_3_capacity_steps_kvar_json TEXT NULL",
                "phase_a_circuit_running_count": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN phase_a_circuit_running_count INTEGER NULL",
                "phase_b_circuit_running_count": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN phase_b_circuit_running_count INTEGER NULL",
                "phase_c_circuit_running_count": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN phase_c_circuit_running_count INTEGER NULL",
                "common_group_1_running_count": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN common_group_1_running_count INTEGER NULL",
                "common_group_2_running_count": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN common_group_2_running_count INTEGER NULL",
                "common_group_3_running_count": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN common_group_3_running_count INTEGER NULL",
                "split_circuit_running_count": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN split_circuit_running_count INTEGER NULL",
                "common_circuit_running_count": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN common_circuit_running_count INTEGER NULL",
                "running_circuit_count": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN running_circuit_count INTEGER NULL",
                "control_mode": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN control_mode VARCHAR(32) NULL",
                "auto_on_elapsed_seconds": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN auto_on_elapsed_seconds INTEGER NULL",
                "auto_off_elapsed_seconds": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN auto_off_elapsed_seconds INTEGER NULL",
                "last_auto_action": "ALTER TABLE capacitor_bank_control_profile ADD COLUMN last_auto_action VARCHAR(64) NULL",
            }
            for column_name, sql in cap_profile_column_sql.items():
                if column_name not in existing_columns:
                    logger.info(f"Schema sync: adding capacitor_bank_control_profile.{column_name}")
                    session.exec(text(sql))

        if "capacitor_bank_telemetry" in table_names:
            existing_columns = {column["name"] for column in inspector.get_columns("capacitor_bank_telemetry")}
            cap_telemetry_column_sql = {
                "phase_a_circuit_running_count": "ALTER TABLE capacitor_bank_telemetry ADD COLUMN phase_a_circuit_running_count INTEGER NULL",
                "phase_b_circuit_running_count": "ALTER TABLE capacitor_bank_telemetry ADD COLUMN phase_b_circuit_running_count INTEGER NULL",
                "phase_c_circuit_running_count": "ALTER TABLE capacitor_bank_telemetry ADD COLUMN phase_c_circuit_running_count INTEGER NULL",
                "common_group_1_running_count": "ALTER TABLE capacitor_bank_telemetry ADD COLUMN common_group_1_running_count INTEGER NULL",
                "common_group_2_running_count": "ALTER TABLE capacitor_bank_telemetry ADD COLUMN common_group_2_running_count INTEGER NULL",
                "common_group_3_running_count": "ALTER TABLE capacitor_bank_telemetry ADD COLUMN common_group_3_running_count INTEGER NULL",
                "split_circuit_running_count": "ALTER TABLE capacitor_bank_telemetry ADD COLUMN split_circuit_running_count INTEGER NULL",
                "common_circuit_running_count": "ALTER TABLE capacitor_bank_telemetry ADD COLUMN common_circuit_running_count INTEGER NULL",
                "running_circuit_count": "ALTER TABLE capacitor_bank_telemetry ADD COLUMN running_circuit_count INTEGER NULL",
                "control_mode": "ALTER TABLE capacitor_bank_telemetry ADD COLUMN control_mode VARCHAR(32) NULL",
                "auto_on_elapsed_seconds": "ALTER TABLE capacitor_bank_telemetry ADD COLUMN auto_on_elapsed_seconds INTEGER NULL",
                "auto_off_elapsed_seconds": "ALTER TABLE capacitor_bank_telemetry ADD COLUMN auto_off_elapsed_seconds INTEGER NULL",
                "last_auto_action": "ALTER TABLE capacitor_bank_telemetry ADD COLUMN last_auto_action VARCHAR(64) NULL",
            }
            for column_name, sql in cap_telemetry_column_sql.items():
                if column_name not in existing_columns:
                    logger.info(f"Schema sync: adding capacitor_bank_telemetry.{column_name}")
                    session.exec(text(sql))

        if "user" in table_names:
            existing_columns = {column["name"] for column in inspector.get_columns("user")}
            if "role" not in existing_columns:
                logger.info("Schema sync: adding user.role")
                session.exec(text("ALTER TABLE \"user\" ADD COLUMN role VARCHAR(32) DEFAULT 'admin'"))
                session.exec(text("UPDATE \"user\" SET role = 'admin' WHERE role IS NULL"))
                session.exec(text("CREATE INDEX IF NOT EXISTS idx_user_role ON \"user\" (role)"))
            if "location_scope" not in existing_columns:
                logger.info("Schema sync: adding user.location_scope")
                session.exec(text("ALTER TABLE \"user\" ADD COLUMN location_scope TEXT NULL"))
            if "must_change_password" not in existing_columns:
                logger.info("Schema sync: adding user.must_change_password")
                session.exec(text("ALTER TABLE \"user\" ADD COLUMN must_change_password BOOLEAN DEFAULT FALSE"))
            if "failed_login_attempts" not in existing_columns:
                logger.info("Schema sync: adding user.failed_login_attempts")
                session.exec(text("ALTER TABLE \"user\" ADD COLUMN failed_login_attempts INTEGER DEFAULT 0"))
            if "locked_until" not in existing_columns:
                logger.info("Schema sync: adding user.locked_until")
                session.exec(text("ALTER TABLE \"user\" ADD COLUMN locked_until TIMESTAMP NULL"))
                session.exec(text("CREATE INDEX IF NOT EXISTS idx_user_locked_until ON \"user\" (locked_until)"))
            if "token_version" not in existing_columns:
                logger.info("Schema sync: adding user.token_version")
                session.exec(text("ALTER TABLE \"user\" ADD COLUMN token_version INTEGER DEFAULT 0"))
            if "last_login_at" not in existing_columns:
                logger.info("Schema sync: adding user.last_login_at")
                session.exec(text("ALTER TABLE \"user\" ADD COLUMN last_login_at TIMESTAMP NULL"))
            if "last_password_changed_at" not in existing_columns:
                logger.info("Schema sync: adding user.last_password_changed_at")
                session.exec(text("ALTER TABLE \"user\" ADD COLUMN last_password_changed_at TIMESTAMP NULL"))

        session.commit()


def _ensure_runtime_indexes() -> None:
    """开发/兼容模式下补齐高频索引。"""
    index_sql = (
        "CREATE INDEX IF NOT EXISTS idx_energydata_device_timestamp "
        "ON energydata (device_id, timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_energydata_energy_type_timestamp "
        "ON energydata (energy_type, timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_alarm_device_resolved_timestamp "
        "ON alarm (device_id, is_resolved, timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_alarm_instance_recovered_last_seen "
        "ON alarm (instance_key, recovered_at, last_seen_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_device_ingestion_health_last_success "
        "ON device_ingestion_health (last_success_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_device_ingestion_health_last_failure "
        "ON device_ingestion_health (last_failure_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_audit_event_action_created_at "
        "ON audit_event (action, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_audit_event_actor_created_at "
        "ON audit_event (actor, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_audit_event_outcome_created_at "
        "ON audit_event (outcome, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_mqtt_ingestion_record_device_received "
        "ON mqtt_ingestion_record (device_id, received_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_mqtt_ingestion_record_status_received "
        "ON mqtt_ingestion_record (status, received_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_mqtt_ingestion_record_next_retry_at "
        "ON mqtt_ingestion_record (next_retry_at)",
    )
    with Session(engine) as session:
        for sql in index_sql:
            session.exec(text(sql))
        session.commit()


def _assert_required_tables_exist() -> None:
    """生产模式下，要求关键表已由 migration 正式创建。"""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    required_tables = {
        "alarm",
        "audit_event",
        "capacitor_bank_control_profile",
        "device",
        "device_control_log",
        "device_ingestion_health",
        "energydata",
        "mqtt_ingestion_record",
        "user",
    }
    missing_tables = sorted(required_tables - existing_tables)
    if missing_tables:
        raise RuntimeError(
            "数据库缺少关键表，请先执行 migration 后再启动应用: "
            + ", ".join(missing_tables)
        )


def _assert_required_columns_present() -> None:
    """生产模式下验证关键表字段已通过 migration 到位。"""
    inspector = inspect(engine)
    missing_fields: list[str] = []
    for table_name, columns in REQUIRED_COLUMNS.items():
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        missing = sorted(columns - existing_columns)
        missing_fields.extend(f"{table_name}.{column}" for column in missing)
    if missing_fields:
        raise RuntimeError(
            "数据库 schema 与当前应用不兼容，请先执行 migration: "
            + ", ".join(missing_fields)
        )


def _try_enable_timescaledb_hypertable() -> None:
    """将 energydata 转为 TimescaleDB hypertable（如果不是 TimescaleDB 则忽略）。"""
    logger.info("TimescaleDB hypertable: trying to enable for table energydata")
    with Session(engine) as session:
        try:
            session.exec(
                text(
                    "SELECT create_hypertable('energydata', 'timestamp', "
                    "if_not_exists => TRUE, migrate_data => TRUE);"
                )
            )
            session.commit()
            logger.info("TimescaleDB hypertable enabled for energydata")
        except Exception as e:
            logger.warning(f"TimescaleDB hypertable skipped: {e}")


def get_session() -> Generator[Session, None, None]:
    """FastAPI 依赖注入：获取数据库 Session。"""
    with Session(engine) as session:
        yield session
