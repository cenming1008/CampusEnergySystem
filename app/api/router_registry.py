"""
API 路由注册

集中管理公开路由与受保护路由，避免入口文件堆积注册细节。
"""

from fastapi import Depends, FastAPI

from app.api.deps import ensure_password_change_completed, get_current_user
from app.api.endpoints import (
    alarms,
    analysis,
    audit,
    auth,
    campus,
    data_cleanup,
    data_generator,
    device_groups,
    devices,
    energy,
    fdd,
    forecast,
    frontend_errors,
    health,
    inspection,
    locations,
    maintenance,
    reports,
    users,
)
from app.api.endpoints.svg import router as svg_router


PUBLIC_ROUTERS = (
    (health.router, "", ("系统健康",)),
    (auth.router, "/auth", ("认证",)),
    (frontend_errors.router, "", ("前端可观测性",)),
)

PROTECTED_ROUTERS = (
    (campus.router, "/campus", ("园区 EMS",)),
    (devices.router, "/devices", ("设备管理",)),
    (alarms.router, "/alarms", ("报警管理",)),
    (analysis.router, "/analysis", ("数据分析",)),
    (fdd.router, "/fdd", ("故障诊断",)),
    (reports.router, "/reports", ("报表导出",)),
    (forecast.router, "/forecast", ("预测功能",)),
    (data_generator.router, "/data-generator", ("数据生成",)),
    (energy.router, "/energy", ("多能源管理",)),
    (maintenance.router, "/maintenance", ("设备维护",)),
    (users.router, "/users", ("用户管理",)),
    (audit.router, "/audit", ("审计日志",)),
    (locations.router, "/locations", ("位置管理",)),
    (device_groups.router, "/device-groups", ("设备分组",)),
    (data_cleanup.router, "/data-cleanup", ("数据清理",)),
    (inspection.router, "/inspection", ("巡检运维",)),
    (svg_router, "/svg", ("SVG 静止无功发生器",)),
)


def register_routers(app: FastAPI) -> None:
    """将所有 API 路由注册到 FastAPI 应用。"""
    for router, prefix, tags in PUBLIC_ROUTERS:
        app.include_router(router, prefix=prefix, tags=list(tags))

    protected_dependencies = [Depends(get_current_user), Depends(ensure_password_change_completed)]
    for router, prefix, tags in PROTECTED_ROUTERS:
        app.include_router(
            router,
            prefix=prefix,
            tags=list(tags),
            dependencies=protected_dependencies,
        )
