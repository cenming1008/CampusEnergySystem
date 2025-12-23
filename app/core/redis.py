import os
import redis.asyncio as redis
from typing import Optional

# 从环境变量获取 Redis URL，默认为本地开发地址
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class RedisClient:
    _client: Optional[redis.Redis] = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        """获取 Redis 客户端实例（单例模式）"""
        if cls._client is None:
            # 创建连接池
            cls._client = redis.from_url(
                REDIS_URL, 
                encoding="utf-8", 
                decode_responses=True # 自动解码为字符串
            )
        return cls._client

    @classmethod
    async def close(cls):
        """关闭连接"""
        if cls._client:
            await cls._client.close()
            cls._client = None

# 导出获取客户端的函数，方便调用
async def get_redis() -> redis.Redis:
    return RedisClient.get_client()