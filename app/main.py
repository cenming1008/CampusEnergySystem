"""FastAPI 应用主入口。"""

from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.router_registry import register_routers
from app.api.websocket import router as websocket_router
from app.core.audit import reset_audit_request_context, set_audit_request_context
from app.core.error_handlers import register_exception_handlers
from app.core.lifecycle import lifespan
from app.core.metrics import observe_http_request
from app.core.rate_limit import RateLimiterFactory, client_key_from_request
from app.core.security_headers import build_security_headers
from app.core.settings import settings


GLOBAL_RATE_LIMIT_EXCLUDE_PREFIXES = (
    "/health",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
)


def should_apply_global_rate_limit(path: str) -> bool:
    return not any(path.startswith(prefix) for prefix in GLOBAL_RATE_LIMIT_EXCLUDE_PREFIXES)


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
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts or ["*"])

if settings.force_https:
    app.add_middleware(HTTPSRedirectMiddleware)


@app.middleware("http")
async def request_observability_middleware(request: Request, call_next):
    """记录请求耗时，并给响应增加耗时头。"""
    started_at = perf_counter()
    request_id = request.headers.get("X-Request-Id") or uuid4().hex
    client_ip = request.client.host if request.client else None
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip() or client_ip

    token = set_audit_request_context(
        request_id=request_id,
        client_ip=client_ip,
        user_agent=request.headers.get("User-Agent"),
        method=request.method,
        path=request.url.path,
    )
    request.state.request_id = request_id

    if should_apply_global_rate_limit(request.url.path):
        RateLimiterFactory.get().check(
            bucket="api-global",
            key=client_key_from_request(request),
            max_calls=settings.api_global_rate_limit_count,
            window_seconds=settings.api_global_rate_limit_window_seconds,
        )

    try:
        response = await call_next(request)
    except Exception:
        duration_seconds = perf_counter() - started_at
        observe_http_request(
            method=request.method,
            path=request.url.path,
            status_code=500,
            duration_seconds=duration_seconds,
        )
        raise
    finally:
        reset_audit_request_context(token)

    duration_seconds = perf_counter() - started_at
    duration_ms = round(duration_seconds * 1000, 2)
    observe_http_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_seconds=duration_seconds,
    )
    for header_name, header_value in build_security_headers(settings).items():
        response.headers.setdefault(header_name, header_value)
    response.headers["X-Process-Time-Ms"] = str(duration_ms)
    response.headers["X-Request-Id"] = request_id
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(websocket_router)
register_routers(app)
