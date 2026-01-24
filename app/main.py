"""
FastAPI应用主入口
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
from app.services.mqtt_worker import start_mqtt_background
from app.services.scheduler_service import start_scheduler, stop_scheduler
from app.api.endpoints import (
    auth, devices, alarms, analysis, reports, fdd, health, 
    forecast, data_generator, energy, maintenance, locations, device_groups, data_cleanup
)
from app.api.deps import get_current_user


# 全局变量：保存事件循环引用，用于在MQTT回调线程中安全调用异步函数
_event_loop: Optional[asyncio.AbstractEventLoop] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global _event_loop
    
    # 启动阶段
    logger.info("🚀 应用启动中...")
    
    # 保存事件循环引用，供MQTT回调使用
    _event_loop = asyncio.get_running_loop()
    
    # 初始化数据库
    init_db()
    logger.info("✅ 数据库初始化完成")
    
    # 连接Redis
    try:
        redis = RedisClient.get_client()
        await redis.ping()
        logger.info("✅ Redis连接成功")
    except Exception as e:
        logger.warning(f"⚠️ Redis连接失败: {e}")
    
    # 启动MQTT监听
    def mqtt_to_ws_callback(msg_dict):
        """MQTT消息回调：将消息通过WebSocket广播给前端"""
        global _event_loop
        if _event_loop and _event_loop.is_running():
            # 在MQTT回调线程中安全地调度异步函数到事件循环
            try:
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast(msg_dict),
                    _event_loop
                )
                logger.debug(f"✅ MQTT消息已调度到WebSocket: {msg_dict.get('type', 'unknown')}")
            except Exception as e:
                logger.error(f"❌ 调度WebSocket广播失败: {e}")
        else:
            logger.warning("⚠️ 事件循环不可用，无法广播WebSocket消息")
    
    start_mqtt_background(on_message_callback=mqtt_to_ws_callback)
    logger.info("✅ MQTT服务启动完成")
    
    # 启动定时任务调度器
    try:
        start_scheduler()
        logger.info("✅ 定时任务调度器启动完成")
    except Exception as e:
        logger.warning(f"⚠️ 定时任务调度器启动失败: {e}")
    
    logger.info(f"✨ 系统就绪 - {settings.app_name} v{settings.app_version}")
    
    yield
    
    # 关闭阶段
    logger.info("🛑 应用关闭中...")
    
    # 停止定时任务调度器
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
    
    # 清理事件循环引用
    _event_loop = None


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    description="基于FastAPI + TimescaleDB + MQTT的工业级能源管理系统",
    version=settings.app_version,
    lifespan=lifespan
)

# 注册异常处理器
register_exception_handlers(app)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket实时数据推送端点"""
    logger.info("🔌 收到 WebSocket 连接请求")
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
        manager.disconnect(websocket)


# 注册路由

# 健康检查端点（无需认证，供监控系统使用）
app.include_router(
    health.router,
    tags=["系统健康"]
)

app.include_router(
    auth.router,
    prefix="/auth",
    tags=["认证"]
)

app.include_router(
    devices.router,
    prefix="/devices",
    tags=["设备管理"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    alarms.router,
    prefix="/alarms",
    tags=["报警管理"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    analysis.router,
    prefix="/analysis",
    tags=["数据分析"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    fdd.router,
    prefix="/fdd",
    tags=["故障诊断"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    reports.router,
    prefix="/reports",
    tags=["报表导出"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    forecast.router,
    prefix="/forecast",
    tags=["预测功能"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    data_generator.router,
    prefix="/data-generator",
    tags=["数据生成"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    energy.router,
    prefix="/energy",
    tags=["多能源管理"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    maintenance.router,
    prefix="/maintenance",
    tags=["设备维护"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    locations.router,
    prefix="/locations",
    tags=["位置管理"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    device_groups.router,
    prefix="/device-groups",
    tags=["设备分组"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    data_cleanup.router,
    prefix="/data-cleanup",
    tags=["数据清理"],
    dependencies=[Depends(get_current_user)]
)

