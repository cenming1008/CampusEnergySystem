"""
轻量进程内限流。

不依赖额外中间件，适合当前单进程/单实例开发与基础保护场景。
"""

from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import time
from typing import Callable

from fastapi import HTTPException, Request


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


rate_limiter = InMemoryRateLimiter()


def _client_key(request: Request) -> str:
    client_host = request.client.host if request.client else "unknown"
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip() or client_host
    return client_host


def limit_requests(bucket: str, max_calls: int, window_seconds: int) -> Callable[[Request], None]:
    """生成 FastAPI 依赖，用于端点限流。"""

    def dependency(request: Request) -> None:
        rate_limiter.check(
            bucket=bucket,
            key=_client_key(request),
            max_calls=max_calls,
            window_seconds=window_seconds,
        )

    return dependency
