"""
健康检查端点
用于系统监控、Docker健康检查、负载均衡器等
"""
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import APIRouter, Depends, Response
from sqlmodel import Session, select

from app.api.deps import require_monitoring_access
from app.core.database import get_session
from app.core.redis import RedisClient
from app.core.logger import logger
from app.core.metrics import render_metrics
from app.core.runtime_state import runtime_state
from app.core.settings import settings
from app.services.mqtt_realtime_bridge import load_worker_health

router = APIRouter()


def _is_worker_heartbeat_fresh(worker_health: dict[str, Any]) -> bool:
    updated_at = worker_health.get("updated_at")
    if not updated_at:
        return False

    try:
        heartbeat_time = datetime.fromisoformat(updated_at)
    except (TypeError, ValueError):
        return False

    freshness_window = max(
        5,
        int(settings.mqtt_worker_health_ttl_seconds),
        int(settings.mqtt_worker_health_heartbeat_seconds) * 2,
    )
    return heartbeat_time >= datetime.now() - timedelta(seconds=freshness_window)


@router.get(
    "/health",
    summary="系统健康检查",
    description="检查系统各组件（数据库、Redis、MQTT）的健康状态",
    response_description="返回系统健康状态"
)
async def health_check(
    _: None = Depends(require_monitoring_access),
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
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
        "version": settings.app_version,
        "semantics": {
            "liveness": "/health/live 只表达进程存活",
            "readiness": "/health/ready 只表达技术 readiness，不等于完整业务就绪",
            "diagnostics": "/health 提供组件状态、诊断摘要与业务信号可见性",
        },
        "services": {
            "database": "unknown",
            "redis": "unknown",
            "mqtt_bridge": "unknown",
            "mqtt_worker": "unknown",
            "api_realtime": "unknown",
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
    for service_name in ("mqtt_bridge", "api_realtime", "scheduler"):
        service_payload = runtime_snapshot["services"].get(service_name, {})
        service_status = service_payload.get("status", "unknown")
        health_status["services"][service_name] = service_status
        if service_status in {"unhealthy"}:
            health_status["status"] = "unhealthy"
        elif service_status not in {"healthy", "unknown"} and health_status["status"] == "healthy":
            health_status["status"] = "degraded"

    try:
        worker_health = await load_worker_health()
    except Exception as exc:
        worker_health = {"status": "unhealthy", "detail": str(exc), "updated_at": None}
    worker_status = worker_health.get("status", "unknown")
    health_status["services"]["mqtt_worker"] = worker_status
    if worker_status in {"unhealthy"}:
        health_status["status"] = "unhealthy"
    elif worker_status not in {"healthy", "unknown"} and health_status["status"] == "healthy":
        health_status["status"] = "degraded"

    diagnostics = {
        "bridge": runtime_snapshot["services"].get("mqtt_bridge", {}),
        "worker": worker_health,
        "api_realtime": runtime_snapshot["services"].get("api_realtime", {}),
    }
    business_signals = {
        "replay": {
            "success_total": runtime_snapshot["counters"].get("mqtt_replay_success_total", 0),
            "failure_total": runtime_snapshot["counters"].get("mqtt_replay_failure_total", 0),
            "skipped_total": runtime_snapshot["counters"].get("mqtt_replay_skipped_total", 0),
        },
        "ingestion": {
            "mqtt_messages_total": runtime_snapshot["counters"].get("mqtt_messages_total", 0),
            "ingestion_success_total": runtime_snapshot["counters"].get("mqtt_ingestion_success_total", 0),
            "ingestion_failure_total": runtime_snapshot["counters"].get("mqtt_ingestion_failure_total", 0),
            "duplicates_total": runtime_snapshot["counters"].get("mqtt_duplicates_total", 0),
        },
    }

    health_status["runtime"] = runtime_snapshot
    health_status["mqtt_bridge"] = runtime_snapshot["services"].get("mqtt_bridge", {})
    health_status["mqtt_worker"] = worker_health
    health_status["api_realtime"] = runtime_snapshot["services"].get("api_realtime", {})
    health_status["diagnostics"] = diagnostics
    health_status["business_signals"] = business_signals
    
    return health_status


@router.get(
    "/metrics",
    summary="Prometheus 指标",
    description="暴露 Prometheus 可抓取的运行指标"
)
async def metrics(_: None = Depends(require_monitoring_access)) -> Response:
    payload, content_type = render_metrics()
    return Response(content=payload, media_type=content_type)


@router.get(
    "/health/live",
    summary="存活检查",
    description="简单的存活检查，用于 Kubernetes liveness probe"
)
async def liveness_check(_: None = Depends(require_monitoring_access)) -> Dict[str, str]:
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
async def readiness_check(
    _: None = Depends(require_monitoring_access),
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    就绪检查（Readiness Probe）
    
    检查应用是否已准备好接收流量。
    主要检查关键依赖（数据库）是否可用。
    用于负载均衡器判断是否将流量路由到此实例。
    """
    ready_status = {
        "status": "ready",
        "timestamp": datetime.now().isoformat(),
        "semantics": "technical_readiness_only",
        "checks": {
            "database": "unknown",
            "redis": "unknown",
            "mqtt_worker_heartbeat": "unknown",
            "mqtt_bridge": "unknown",
        },
    }
    
    # 检查数据库（核心依赖）
    try:
        session.exec(select(1)).first()
        ready_status["checks"]["database"] = "ready"
    except Exception as e:
        ready_status["checks"]["database"] = "not_ready"
        ready_status["status"] = "not_ready"
        logger.error(f"❌ 就绪检查: 数据库未就绪 - {e}")
    try:
        redis = RedisClient.get_client()
        await redis.ping()
        ready_status["checks"]["redis"] = "ready"
    except Exception as exc:
        ready_status["checks"]["redis"] = "not_ready"
        ready_status["status"] = "not_ready"
        logger.warning(f"⚠️ 就绪检查: Redis 未就绪 - {exc}")

    try:
        worker_health = await load_worker_health()
    except Exception as exc:
        worker_health = {"status": "unhealthy", "detail": str(exc), "updated_at": None}
    worker_ready = worker_health.get("status") == "healthy" and _is_worker_heartbeat_fresh(worker_health)
    ready_status["checks"]["mqtt_worker_heartbeat"] = "ready" if worker_ready else "not_ready"
    if not worker_ready:
        ready_status["status"] = "not_ready"

    runtime_snapshot = runtime_state.snapshot()
    bridge_ready = runtime_snapshot["services"].get("mqtt_bridge", {}).get("status") == "healthy"
    ready_status["checks"]["mqtt_bridge"] = "ready" if bridge_ready else "not_ready"
    if not bridge_ready:
        ready_status["status"] = "not_ready"

    ready_status["diagnostics"] = {
        "notes": "readiness 仅由数据库、Redis、worker 心跳新鲜度和 bridge 在线状态驱动",
        "excluded_signals": [
            "recent_valid_processing",
            "replay_summary",
            "device_success_rate",
            "consecutive_failures",
            "last_failure_reason",
        ],
    }

    return ready_status
