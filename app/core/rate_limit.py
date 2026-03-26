"""
限流能力封装。

- 开发环境默认使用进程内固定窗口限流
- 生产环境可切换为 Redis 共享限流状态，支持多实例部署
- 当 Redis 不可用时可按配置选择回退到进程内限流，避免阻塞核心业务
"""

from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import time
from typing import Callable, Optional, Protocol

from fastapi import HTTPException, Request
from redis import Redis
from redis.exceptions import RedisError

from app.core.logger import logger
from app.core.settings import settings


class RateLimiter(Protocol):
    def check(self, bucket: str, key: str, max_calls: int, window_seconds: int) -> None:
        ...


class InMemoryRateLimiter:
    """固定窗口限流器。"""

    def __init__(self) -> None:
        self._lock = Lock()
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    def check(self, bucket: str, key: str, max_calls: int, window_seconds: int) -> None:
        now = time()
        bucket_key = f"{bucket}:{key}"
        cutoff = now - window_seconds

        with self._lock:
            entries = self._buckets[bucket_key]
            while entries and entries[0] <= cutoff:
                entries.popleft()

            if len(entries) >= max_calls:
                raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

            entries.append(now)


class RedisRateLimiter:
    """基于 Redis ZSET 的滑动窗口限流器。"""

    def __init__(self, redis_client: Redis, key_prefix: str = "rate-limit") -> None:
        self._redis = redis_client
        self._key_prefix = key_prefix

    def check(self, bucket: str, key: str, max_calls: int, window_seconds: int) -> None:
        now = time()
        bucket_key = self._redis_key(bucket, key)
        member = f"{now:.6f}:{key}"
        cutoff = now - window_seconds

        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(bucket_key, 0, cutoff)
        pipe.zcard(bucket_key)
        pipe.zadd(bucket_key, {member: now})
        pipe.expire(bucket_key, max(window_seconds, 1))
        _, current_count, _, _ = pipe.execute()

        if int(current_count) >= max_calls:
            # 超限时撤回本次写入，保持计数准确。
            self._redis.zrem(bucket_key, member)
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

    def _redis_key(self, bucket: str, key: str) -> str:
        return f"{self._key_prefix}:{bucket}:{key}"


class SafeRateLimiter:
    """优先使用主限流器，异常时根据配置回退到备用限流器。"""

    def __init__(
        self,
        primary: RateLimiter,
        *,
        fallback: Optional[RateLimiter] = None,
        fail_open: bool = True,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._fail_open = fail_open

    def check(self, bucket: str, key: str, max_calls: int, window_seconds: int) -> None:
        try:
            self._primary.check(bucket=bucket, key=key, max_calls=max_calls, window_seconds=window_seconds)
        except HTTPException:
            raise
        except RedisError as exc:
            self._handle_backend_error(exc, bucket, key, max_calls, window_seconds)
        except Exception as exc:
            self._handle_backend_error(exc, bucket, key, max_calls, window_seconds)

    def _handle_backend_error(
        self,
        exc: Exception,
        bucket: str,
        key: str,
        max_calls: int,
        window_seconds: int,
    ) -> None:
        logger.warning(f"Rate limiter backend failed, falling back if possible: {exc}")
        if self._fallback is not None:
            self._fallback.check(bucket=bucket, key=key, max_calls=max_calls, window_seconds=window_seconds)
            return
        if self._fail_open:
            return
        raise HTTPException(status_code=503, detail="限流服务暂时不可用")


class RateLimiterFactory:
    _lock = Lock()
    _instance: Optional[RateLimiter] = None

    @classmethod
    def get(cls) -> RateLimiter:
        if cls._instance is not None:
            return cls._instance
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls._build()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._instance = None

    @classmethod
    def _build(cls) -> RateLimiter:
        backend = settings.rate_limit_backend
        if backend == "auto":
            backend = "redis" if settings.is_production else "memory"

        memory_limiter = InMemoryRateLimiter()
        if backend == "memory":
            return memory_limiter

        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        redis_limiter = RedisRateLimiter(
            redis_client=redis_client,
            key_prefix=settings.rate_limit_key_prefix,
        )
        return SafeRateLimiter(
            redis_limiter,
            fallback=memory_limiter if settings.rate_limit_fallback_to_memory else None,
            fail_open=settings.rate_limit_fail_open,
        )


def client_key_from_request(request: Request) -> str:
    client_host = request.client.host if request.client else "unknown"
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip() or client_host
    return client_host


def limit_requests(bucket: str, max_calls: int, window_seconds: int) -> Callable[[Request], None]:
    """生成 FastAPI 依赖，用于端点限流。"""

    def dependency(request: Request) -> None:
        if max_calls <= 0 or window_seconds <= 0:
            return
        RateLimiterFactory.get().check(
            bucket=bucket,
            key=client_key_from_request(request),
            max_calls=max_calls,
            window_seconds=window_seconds,
        )

    return dependency
