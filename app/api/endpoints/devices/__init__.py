"""
设备域 endpoint 包入口。

职责：
- 只聚合设备域子模块路由
- 对外暴露设备域子模块，便于测试按模块导入

不负责：
- 定义 schema
- 承载序列化逻辑
- 放置业务流程
"""

from fastapi import APIRouter

from . import compensation_capacitor_bank, compensation_svg, data, ingestion_health, management, monitoring

router = APIRouter()
router.include_router(management.router)
router.include_router(data.router)
router.include_router(ingestion_health.router)
router.include_router(monitoring.router)
router.include_router(compensation_svg.router)
router.include_router(compensation_capacitor_bank.router)

__all__ = [
    "router",
    "management",
    "data",
    "ingestion_health",
    "monitoring",
    "compensation_svg",
    "compensation_capacitor_bank",
]
