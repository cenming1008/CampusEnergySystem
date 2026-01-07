"""
FastAPI应用主入口
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db
from app.core.socket_manager import manager
from app.core.redis import RedisClient
from app.core.logger import logger
from app.core.settings import settings
from app.core.error_handlers import register_exception_handlers
from app.services.mqtt_worker import start_mqtt_background
from app.api.endpoints import auth, devices, telemetry, alarms, analysis, reports, fdd
from app.api.deps import get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动阶段
    logger.info("🚀 应用启动中...")
    
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
        asyncio.create_task(manager.broadcast(msg_dict))
    
    start_mqtt_background(on_message_callback=mqtt_to_ws_callback)
    logger.info("✅ MQTT服务启动完成")
    
    logger.info("✨ 系统就绪")
    
    yield
    
    # 关闭阶段
    logger.info("🛑 应用关闭中...")
    try:
        await RedisClient.close()
        logger.info("✅ Redis连接已关闭")
    except Exception as e:
        logger.warning(f"⚠️ Redis关闭失败: {e}")


# 创建FastAPI应用
app = FastAPI(
    title="煤矿综合能源管理系统",
    description="基于FastAPI + TimescaleDB + MQTT的工业级能源管理系统",
    version="2.0.0",
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
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# 注册路由
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
    telemetry.router,
    prefix="/telemetry",
    tags=["遥测数据"]
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

