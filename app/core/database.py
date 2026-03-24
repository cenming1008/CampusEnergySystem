"""
数据库连接与初始化

- 使用 SQLModel 管理 ORM
- 启动阶段自动 create_all
- 如数据库为 TimescaleDB，则尝试将 `devicedata` 转换为 hypertable（失败不阻塞）
"""

from __future__ import annotations

from collections.abc import Generator

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
    _try_enable_timescaledb_hypertable()


def _try_enable_timescaledb_hypertable() -> None:
    """将 devicedata 转为 TimescaleDB hypertable（如果不是 TimescaleDB 则忽略）。"""
    logger.info("TimescaleDB hypertable: trying to enable for table devicedata")
    with Session(engine) as session:
        try:
            session.exec(
                text(
                    "SELECT create_hypertable('devicedata', 'timestamp', "
                    "if_not_exists => TRUE, migrate_data => TRUE);"
                )
            )
            session.commit()
            logger.info("TimescaleDB hypertable enabled for devicedata")
        except Exception as e:
            logger.warning(f"TimescaleDB hypertable skipped: {e}")


def get_session() -> Generator[Session, None, None]:
    """FastAPI 依赖注入：获取数据库 Session。"""
    with Session(engine) as session:
        yield session
