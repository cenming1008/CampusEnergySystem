"""FastAPI 应用主入口。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router_registry import register_routers
from app.api.websocket import router as websocket_router
from app.core.error_handlers import register_exception_handlers
from app.core.lifecycle import lifespan
from app.core.settings import settings


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

app.include_router(websocket_router)
register_routers(app)
