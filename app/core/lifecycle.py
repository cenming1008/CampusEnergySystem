"""
应用生命周期管理

负责启动与关闭时的基础设施初始化和清理。
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI

from app.core.database import init_db
from app.core.logger import logger
from app.core.redis import RedisClient
from app.core.runtime_state import runtime_state
from app.core.settings import settings
from app.core.socket_manager import manager
from app.core.startup_checks import validate_runtime_configuration
from app.services.mqtt_realtime_bridge import bridge_loop
from app.services.mqtt_publisher import stop_publisher as stop_mqtt_publisher
from app.services.scheduler_service import start_scheduler, stop_scheduler


_event_loop: Optional[asyncio.AbstractEventLoop] = None
_bridge_stop_event: Optional[asyncio.Event] = None
_bridge_task: Optional[asyncio.Task] = None


async def startup() -> None:
    """应用启动：数据库、Redis、MQTT、定时任务。"""
    global _event_loop, _bridge_stop_event, _bridge_task
    _event_loop = asyncio.get_running_loop()

    logger.info("🚀 应用启动中...")
    validate_runtime_configuration(settings)
    init_db()
    runtime_state.mark_service("database", "healthy", "initialized")
    logger.info("✅ 数据库初始化完成")

    try:
        redis = RedisClient.get_client()
        await redis.ping()
        logger.info("✅ Redis连接成功")
    except Exception as exc:
        runtime_state.mark_service("redis", "unhealthy", str(exc))
        logger.warning(f"⚠️ Redis连接失败: {exc}")
    else:
        runtime_state.mark_service("redis", "healthy", "connected")

    runtime_state.mark_service("mqtt", "stopped", "detached to mqtt ingest worker")
    _bridge_stop_event = asyncio.Event()
    _bridge_task = asyncio.create_task(bridge_loop(_bridge_stop_event, manager.broadcast))

    try:
        scheduler_result = await start_scheduler()
        logger.info(f"✅ 定时任务调度器启动完成: {scheduler_result.get('status')}")
    except Exception as exc:
        logger.warning(f"⚠️ 定时任务调度器启动失败: {exc}")

    logger.info(f"✨ 系统就绪 - {settings.app_name} v{settings.app_version}")


async def shutdown() -> None:
    """应用关闭：停止调度器、MQTT、Redis，清理引用。"""
    global _event_loop, _bridge_stop_event, _bridge_task
    logger.info("🛑 应用关闭中...")

    try:
        scheduler_result = await stop_scheduler()
        logger.info(f"✅ 定时任务调度器已停止: {scheduler_result.get('status')}")
    except Exception as exc:
        runtime_state.mark_service("scheduler", "unhealthy", str(exc))
        logger.warning(f"⚠️ 定时任务调度器停止失败: {exc}")

    if _bridge_stop_event is not None:
        _bridge_stop_event.set()
    if _bridge_task is not None:
        try:
            await _bridge_task
            logger.info("✅ Redis 实时桥接已停止")
        except Exception as exc:
            logger.warning(f"⚠️ Redis 实时桥接停止失败: {exc}")
    _bridge_stop_event = None
    _bridge_task = None

    try:
        stop_mqtt_publisher()
        logger.info("✅ MQTT 发布客户端已停止")
    except Exception as exc:
        logger.warning(f"⚠️ MQTT 发布客户端停止失败: {exc}")

    try:
        await RedisClient.close()
        runtime_state.mark_service("redis", "stopped", "closed")
        logger.info("✅ Redis连接已关闭")
    except Exception as exc:
        runtime_state.mark_service("redis", "unhealthy", str(exc))
        logger.warning(f"⚠️ Redis关闭失败: {exc}")

    runtime_state.mark_service("database", "stopped", "process shutdown")
    _event_loop = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """FastAPI 生命周期上下文。"""
    await startup()
    yield
    await shutdown()
