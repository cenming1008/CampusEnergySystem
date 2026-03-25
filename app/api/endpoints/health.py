"""
健康检查端点
用于系统监控、Docker健康检查、负载均衡器等
"""
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.redis import RedisClient
from app.core.logger import logger
from app.core.runtime_state import runtime_state

router = APIRouter()


@router.get(
    "/health",
    summary="系统健康检查",
    description="检查系统各组件（数据库、Redis、MQTT）的健康状态",
    response_description="返回系统健康状态"
)
async def health_check(session: Session = Depends(get_session)) -> Dict[str, Any]:
    """
    系统健康检查端点
    
    返回各个服务组件的健康状态：
    - database: 数据库连接状态
    - redis: Redis连接状态
    - status: 整体健康状态（healthy/degraded/unhealthy）
    
    状态码：
    - 200: 所有服务正常
    - 503: 至少一个服务异常
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "services": {
            "database": "unknown",
            "redis": "unknown",
            "mqtt": "unknown",
            "scheduler": "unknown",
        }
    }
    
    # 检查数据库连接
    try:
        # 执行简单查询测试连接
        result = session.exec(select(1)).first()
        if result == 1:
            health_status["services"]["database"] = "healthy"
            logger.debug("✅ 健康检查: 数据库正常")
        else:
            health_status["services"]["database"] = "unhealthy"
            health_status["status"] = "degraded"
            logger.warning("⚠️ 健康检查: 数据库查询结果异常")
    except Exception as e:
        health_status["services"]["database"] = "unhealthy"
        health_status["status"] = "unhealthy"
        logger.error(f"❌ 健康检查: 数据库连接失败 - {e}")
    
    # 检查 Redis 连接
    try:
        redis = RedisClient.get_client()
        await redis.ping()
        health_status["services"]["redis"] = "healthy"
        logger.debug("✅ 健康检查: Redis正常")
    except Exception as e:
        health_status["services"]["redis"] = "unhealthy"
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"
        logger.warning(f"⚠️ 健康检查: Redis连接失败 - {e}")

    runtime_snapshot = runtime_state.snapshot()
    for service_name in ("mqtt", "scheduler"):
        service_payload = runtime_snapshot["services"].get(service_name, {})
        service_status = service_payload.get("status", "unknown")
        health_status["services"][service_name] = service_status
        if service_status in {"unhealthy"}:
            health_status["status"] = "unhealthy"
        elif service_status not in {"healthy", "unknown"} and health_status["status"] == "healthy":
            health_status["status"] = "degraded"

    health_status["runtime"] = runtime_snapshot
    
    return health_status


@router.get(
    "/health/live",
    summary="存活检查",
    description="简单的存活检查，用于 Kubernetes liveness probe"
)
async def liveness_check() -> Dict[str, str]:
    """
    存活检查（Liveness Probe）
    
    只检查应用本身是否还在运行，不检查依赖服务。
    用于 Kubernetes/Docker 判断容器是否需要重启。
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    }


@router.get(
    "/health/ready",
    summary="就绪检查",
    description="就绪检查，用于 Kubernetes readiness probe",
    response_description="返回服务是否就绪"
)
async def readiness_check(session: Session = Depends(get_session)) -> Dict[str, Any]:
    """
    就绪检查（Readiness Probe）
    
    检查应用是否已准备好接收流量。
    主要检查关键依赖（数据库）是否可用。
    用于负载均衡器判断是否将流量路由到此实例。
    """
    ready_status = {
        "status": "ready",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "database": "unknown"
        }
    }
    
    # 检查数据库（核心依赖）
    try:
        session.exec(select(1)).first()
        ready_status["checks"]["database"] = "ready"
    except Exception as e:
        ready_status["checks"]["database"] = "not_ready"
        ready_status["status"] = "not_ready"
        logger.error(f"❌ 就绪检查: 数据库未就绪 - {e}")
        return ready_status
    
    return ready_status
