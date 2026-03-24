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
from app.core.settings import settings
from app.core.socket_manager import manager
from app.services.mqtt_worker import start_mqtt_background
from app.services.scheduler_service import start_scheduler, stop_scheduler


_event_loop: Optional[asyncio.AbstractEventLoop] = None


def mqtt_to_ws_callback(message: dict) -> None:
    """MQTT 消息回调：将消息调度到当前事件循环并广播到 WebSocket。"""
    global _event_loop

    if not _event_loop or not _event_loop.is_running():
        logger.warning("⚠️ 事件循环不可用，无法广播 WebSocket 消息")
        return

    try:
        asyncio.run_coroutine_threadsafe(manager.broadcast(message), _event_loop)
        logger.debug(f"✅ MQTT消息已调度到WebSocket: {message.get('type', 'unknown')}")
    except Exception as exc:
        logger.error(f"❌ 调度WebSocket广播失败: {exc}")


async def startup() -> None:
    """应用启动：数据库、Redis、MQTT、定时任务。"""
    global _event_loop
    _event_loop = asyncio.get_running_loop()

    logger.info("🚀 应用启动中...")
    init_db()
    logger.info("✅ 数据库初始化完成")

    try:
        redis = RedisClient.get_client()
        await redis.ping()
        logger.info("✅ Redis连接成功")
    except Exception as exc:
        logger.warning(f"⚠️ Redis连接失败: {exc}")

    start_mqtt_background(on_message_callback=mqtt_to_ws_callback)
    logger.info("✅ MQTT服务启动完成")

    try:
        start_scheduler()
        logger.info("✅ 定时任务调度器启动完成")
    except Exception as exc:
        logger.warning(f"⚠️ 定时任务调度器启动失败: {exc}")

    logger.info(f"✨ 系统就绪 - {settings.app_name} v{settings.app_version}")


async def shutdown() -> None:
    """应用关闭：停止调度器、关闭 Redis、清理引用。"""
    global _event_loop
    logger.info("🛑 应用关闭中...")

    try:
        stop_scheduler()
        logger.info("✅ 定时任务调度器已停止")
    except Exception as exc:
        logger.warning(f"⚠️ 定时任务调度器停止失败: {exc}")

    try:
        await RedisClient.close()
        logger.info("✅ Redis连接已关闭")
    except Exception as exc:
        logger.warning(f"⚠️ Redis关闭失败: {exc}")

    _event_loop = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """FastAPI 生命周期上下文。"""
    await startup()
    yield
    await shutdown()
