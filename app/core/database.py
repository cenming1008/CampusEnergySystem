"""
数据库连接与初始化

- 使用 SQLModel 管理 ORM
- 启动阶段自动 create_all
- 如数据库为 TimescaleDB，则尝试将 `devicedata` 转换为 hypertable（失败不阻塞）
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
    SQLModel.metadata.create_all(engine)
    _sync_runtime_schema()
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

        # 高频查询索引，兼容旧数据库实例。
        index_sql = (
            "CREATE INDEX IF NOT EXISTS idx_energydata_device_timestamp "
            "ON energydata (device_id, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_energydata_energy_type_timestamp "
            "ON energydata (energy_type, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_alarm_device_resolved_timestamp "
            "ON alarm (device_id, is_resolved, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_device_ingestion_health_last_success "
            "ON device_ingestion_health (last_success_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_device_ingestion_health_last_failure "
            "ON device_ingestion_health (last_failure_at DESC)",
        )
        for sql in index_sql:
            session.exec(text(sql))

        session.commit()


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
