"""
FastAPI 应用主入口
"""
import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db
from app.core.socket_manager import manager
from app.core.redis import RedisClient
from app.core.logger import logger
from app.core.settings import settings
from app.core.error_handlers import register_exception_handlers
from app.api.deps import get_current_user
from app.services.mqtt_worker import start_mqtt_background
from app.services.scheduler_service import start_scheduler, stop_scheduler

from app.api.endpoints import (
    auth,
    devices,
    alarms,
    analysis,
    reports,
    fdd,
    health,
    forecast,
    data_generator,
    energy,
    maintenance,
    locations,
    device_groups,
    data_cleanup,
    inspection,
)


# 事件循环引用，供 MQTT 回调线程调度异步 WebSocket 广播
_event_loop: Optional[asyncio.AbstractEventLoop] = None


def _mqtt_to_ws_callback(msg_dict: dict) -> None:
    """MQTT 消息回调：将消息通过 WebSocket 广播给前端。"""
    global _event_loop
    if not _event_loop or not _event_loop.is_running():
        logger.warning("⚠️ 事件循环不可用，无法广播 WebSocket 消息")
        return
    try:
        asyncio.run_coroutine_threadsafe(
            manager.broadcast(msg_dict),
            _event_loop,
        )
        logger.debug(f"✅ MQTT消息已调度到WebSocket: {msg_dict.get('type', 'unknown')}")
    except Exception as e:
        logger.error(f"❌ 调度WebSocket广播失败: {e}")


async def _lifespan_startup() -> None:
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
    except Exception as e:
        logger.warning(f"⚠️ Redis连接失败: {e}")

    start_mqtt_background(on_message_callback=_mqtt_to_ws_callback)
    logger.info("✅ MQTT服务启动完成")

    try:
        start_scheduler()
        logger.info("✅ 定时任务调度器启动完成")
    except Exception as e:
        logger.warning(f"⚠️ 定时任务调度器启动失败: {e}")

    logger.info(f"✨ 系统就绪 - {settings.app_name} v{settings.app_version}")


async def _lifespan_shutdown() -> None:
    """应用关闭：停止调度器、关闭 Redis、清理引用。"""
    global _event_loop
    logger.info("🛑 应用关闭中...")

    try:
        stop_scheduler()
        logger.info("✅ 定时任务调度器已停止")
    except Exception as e:
        logger.warning(f"⚠️ 定时任务调度器停止失败: {e}")

    try:
        await RedisClient.close()
        logger.info("✅ Redis连接已关闭")
    except Exception as e:
        logger.warning(f"⚠️ Redis关闭失败: {e}")

    _event_loop = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。"""
    await _lifespan_startup()
    yield
    await _lifespan_shutdown()


# ---------------------------------------------------------------------------
# 应用与中间件
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    description="基于 FastAPI + TimescaleDB + MQTT 的工业级能源管理系统",
    version=settings.app_version,
    lifespan=lifespan,
)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket 实时数据推送。"""
    logger.info("🔌 收到 WebSocket 连接请求")
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
    finally:
        manager.disconnect(websocket)


# ---------------------------------------------------------------------------
# 路由注册（无需认证）
# ---------------------------------------------------------------------------

app.include_router(health.router, tags=["系统健康"])

app.include_router(auth.router, prefix="/auth", tags=["认证"])


# ---------------------------------------------------------------------------
# 路由注册（需认证：dependencies=[Depends(get_current_user)]）
# ---------------------------------------------------------------------------

_ROUTERS = [
    (devices, "/devices", "设备管理"),
    (alarms, "/alarms", "报警管理"),
    (analysis, "/analysis", "数据分析"),
    (fdd, "/fdd", "故障诊断"),
    (reports, "/reports", "报表导出"),
    (forecast, "/forecast", "预测功能"),
    (data_generator, "/data-generator", "数据生成"),
    (energy, "/energy", "多能源管理"),
    (maintenance, "/maintenance", "设备维护"),
    (locations, "/locations", "位置管理"),
    (device_groups, "/device-groups", "设备分组"),
    (data_cleanup, "/data-cleanup", "数据清理"),
    (inspection, "/inspection", "巡检运维"),
]

for router_module, prefix, tag in _ROUTERS:
    app.include_router(
        router_module.router,
        prefix=prefix,
        tags=[tag],
        dependencies=[Depends(get_current_user)],
    )
