"""
Redis 客户端封装（异步）

- 统一从 `settings` 读取配置
- 懒加载单例，便于多处复用
- 提供 `close()` 用于应用关闭阶段释放连接
"""

from __future__ import annotations

from typing import Optional

import redis.asyncio as redis

from app.core.settings import settings


class RedisClient:
    _client: Optional[redis.Redis] = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        """获取 Redis 客户端实例（单例）。"""
        if cls._client is None:
            connection_kwargs = {
                "encoding": "utf-8",
                "decode_responses": True,
            }
            if settings.redis_password:
                connection_kwargs["password"] = settings.redis_password

            cls._client = redis.from_url(settings.redis_url, **connection_kwargs)
        return cls._client

    @classmethod
    async def close(cls) -> None:
        """关闭 Redis 连接（在应用关闭阶段调用）。"""
        if cls._client is None:
            return

        client = cls._client
        cls._client = None
        try:
            await client.close()
            # 保险起见断开连接池（不同版本 redis-py 可能实现细节不同）
            pool = getattr(client, "connection_pool", None)
            if pool and hasattr(pool, "disconnect"):
                result = pool.disconnect(inuse_connections=True)  # type: ignore[call-arg]
                if result is not None:
                    await result
        except Exception:
            # 关闭阶段不再向外抛异常
            pass


async def get_redis() -> redis.Redis:
    """FastAPI 依赖注入：获取 Redis 客户端。"""
    return RedisClient.get_client()