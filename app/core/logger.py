"""
日志配置（Loguru）

说明：
- 控制台输出 + 文件输出（按天轮转）
- 日志目录与级别从 settings 读取
"""

from __future__ import annotations

import os
import sys

from loguru import logger

from app.core.settings import settings


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


LOG_DIR = settings.log_dir or "logs"
_ensure_dir(LOG_DIR)

logger.remove()

logger.add(
    sys.stderr,
    level=settings.log_level,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
)

logger.add(
    os.path.join(LOG_DIR, "ems_app_{time:YYYY-MM-DD}.log"),
    rotation="00:00",
    retention=f"{settings.log_retention_days} days",
    level=settings.log_level,
    encoding="utf-8",
    enqueue=True,
)

logger.add(
    os.path.join(LOG_DIR, "ems_error_{time:YYYY-MM-DD}.log"),
    rotation="00:00",
    retention="30 days",
    level="ERROR",
    encoding="utf-8",
    enqueue=True,
    backtrace=True,
    diagnose=bool(settings.debug),
)

__all__ = ["logger"]