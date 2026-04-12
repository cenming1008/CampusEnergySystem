"""
数据库连接与初始化

- 使用 SQLModel 管理 ORM
- 开发环境可自动 create_all / 运行时补齐字段
- 生产环境默认要求通过版本化 migration 管理表结构
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import inspect
from sqlmodel import SQLModel, create_engine, Session, text

from app.core.logger import logger
from app.core.settings import settings


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
    required_columns = {
        "energydata": {"reactive_power"},
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
    missing_fields: list[str] = []
    for table_name, columns in required_columns.items():
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
