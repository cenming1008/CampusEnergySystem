import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


# 1. 导入核心模块
from app.core.database import init_db
from app.core.socket_manager import manager  # 👈 新增：WebSocket 连接管理器
from app.services.mqtt_worker import start_mqtt_background  # 👈 新增：MQTT 启动函数
from app.core.redis import RedisClient
from app.core.logger import logger
# 2. 导入各个业务模块的路由
from app.api.endpoints import (
    auth,       # 认证
    devices,    # 设备管理
    telemetry,  # 遥测数据 (HTTP上传)
    alarms,     # 报警管理
    analysis,   # 数据分析
    reports,    # 报表导出
    fdd         # 故障诊断
)
from app.api.deps import get_current_user  # 权限验证依赖

# =================================================================
# 🔄 生命周期管理器 (Lifespan)
# 作用：在服务器启动时初始化数据库和 MQTT，在关闭时清理资源
# =================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 🟢 启动阶段 ---
    init_db()  # 1. 创建表结构
    
        # 初始化 Redis 连接测试
    try:
        redis = RedisClient.get_client()
        await redis.ping()
        logger.info("✅ [Redis] 连接成功")
    except Exception as e:
        logger.info(f"❌ [Redis] 连接失败: {e}")

    print("📡 [MQTT] 正在启动后台监听线程...")
    
    # 定义一个“桥梁”函数：当 MQTT 收到数据时，执行这个函数
    # 它的作用是把 MQTT 消息“转发”给 WebSocket
    def mqtt_to_ws_callback(msg_dict):
        # manager.broadcast 是一个异步函数 (async def)
        # 但这里的回调是同步的，所以需要用 create_task 把它扔进事件循环里执行
        asyncio.create_task(manager.broadcast(msg_dict))

    # 2. 启动 MQTT Worker (传入回调函数)
    start_mqtt_background(on_message_callback=mqtt_to_ws_callback)
    
    print("✅ 系统就绪，等待连接...\n")
    
    yield  # ⏸️ 这里是分界线，应用开始运行
    
    # --- 🔴 关闭阶段 ---
    print("\n🛑 [系统关闭]正在清理资源...")

# =================================================================
# 🏗️ 初始化 FastAPI 应用
# =================================================================
app = FastAPI(
    title="煤矿综合能源管理系统 (Mine EMS)",
    description="基于 FastAPI + TimescaleDB + MQTT 的工业级能源管理后端",
    version="2.0.0",
    lifespan=lifespan  # 挂载生命周期钩子
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议改为具体的 ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📂 注意：前端已迁移到 frontend 目录，使用 Vite 开发服务器
# 前端开发服务器运行在 http://localhost:5173
# 生产环境可以将 frontend/dist 构建产物挂载到此处


# =================================================================
# 🔌 WebSocket 路由 (实时数据推送)
# =================================================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    前端通过 ws://localhost:8088/ws 连接此接口
    连接建立后，服务器会把 MQTT 收到的数据实时推给该客户端
    """
    # 1. 接受连接
    await manager.connect(websocket)
    try:
        while True:
            # 2. 保持连接活跃
            # 虽然我们目前不需要前端发消息过来，但必须有一个 await 挂起
            # 否则连接会立即断开。这里等待接收文本（心跳检测可以在这里做）
            await websocket.receive_text()
    except WebSocketDisconnect:
        # 3. 断开连接时清理
        manager.disconnect(websocket)
        # print("🔌 客户端已断开 WebSocket 连接")


# =================================================================
# 🛣️ 注册 HTTP 路由 (RESTful API)
# =================================================================

# 1. 认证模块 (登录获取 Token) - 不需要权限锁
app.include_router(auth.router, prefix="/auth", tags=["0. 认证中心"])

# 2. 设备管理 (增删改查) - 🔐 需要登录
app.include_router(
    devices.router, 
    prefix="/devices", 
    tags=["1. 设备管理"], 
    dependencies=[Depends(get_current_user)]
)

# 3. 遥测数据 (接收 HTTP 上传) - 通常由设备调用，视情况是否加锁
app.include_router(
    telemetry.router, 
    prefix="/telemetry", 
    tags=["2. 遥测数据"]
)

# 4. 报警中心 (查询/处理报警) - 🔐 需要登录
app.include_router(
    alarms.router, 
    prefix="/alarms", 
    tags=["3. 报警中心"], 
    dependencies=[Depends(get_current_user)]
)

# 5. 数据分析 (图表数据源) - 🔐 需要登录
app.include_router(
    analysis.router, 
    prefix="/analysis", 
    tags=["4. 数据分析"], 
    dependencies=[Depends(get_current_user)]
)

# 6. 故障诊断 (FDD算法结果) - 🔐 需要登录
app.include_router(
    fdd.router, 
    prefix="/fdd", 
    tags=["5. 故障诊断"], 
    dependencies=[Depends(get_current_user)]
)

# 7. 报表中心 (导出 CSV) - 🔐 需要登录
app.include_router(
    reports.router, 
    prefix="/reports", 
    tags=["6. 报表中心"], 
    dependencies=[Depends(get_current_user)]
)


# =================================================================
# ▶️ 程序入口
# =================================================================
if __name__ == "__main__":
    # 生产环境通常使用命令行: uvicorn app.main:app --host 0.0.0.0 ...
    # 开发环境直接运行此文件即可
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8088, 
        reload=True,  # 开启热重载：改代码后自动重启
        workers=1     # 开发环境 1 个 worker 即可
    )