"""
API 路由注册

集中管理公开路由与受保护路由，避免入口文件堆积注册细节。
"""

from fastapi import Depends, FastAPI

from app.api.deps import get_current_user
from app.api.endpoints import (
    alarms,
    analysis,
    auth,
    data_cleanup,
    data_generator,
    device_groups,
    devices,
    energy,
    fdd,
    forecast,
    health,
    inspection,
    locations,
    maintenance,
    reports,
)


PUBLIC_ROUTERS = (
    (health.router, "", ("系统健康",)),
    (auth.router, "/auth", ("认证",)),
)

PROTECTED_ROUTERS = (
    (devices.router, "/devices", ("设备管理",)),
    (alarms.router, "/alarms", ("报警管理",)),
    (analysis.router, "/analysis", ("数据分析",)),
    (fdd.router, "/fdd", ("故障诊断",)),
    (reports.router, "/reports", ("报表导出",)),
    (forecast.router, "/forecast", ("预测功能",)),
    (data_generator.router, "/data-generator", ("数据生成",)),
    (energy.router, "/energy", ("多能源管理",)),
    (maintenance.router, "/maintenance", ("设备维护",)),
    (locations.router, "/locations", ("位置管理",)),
    (device_groups.router, "/device-groups", ("设备分组",)),
    (data_cleanup.router, "/data-cleanup", ("数据清理",)),
    (inspection.router, "/inspection", ("巡检运维",)),
)


def register_routers(app: FastAPI) -> None:
    """将所有 API 路由注册到 FastAPI 应用。"""
    for router, prefix, tags in PUBLIC_ROUTERS:
        app.include_router(router, prefix=prefix, tags=list(tags))

    protected_dependencies = [Depends(get_current_user)]
    for router, prefix, tags in PROTECTED_ROUTERS:
        app.include_router(
            router,
            prefix=prefix,
            tags=list(tags),
            dependencies=protected_dependencies,
        )
