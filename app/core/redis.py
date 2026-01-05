import redis.asyncio as redis
from typing import Optional
from app.core.settings import settings  # 使用统一配置管理

# 从统一配置中获取Redis URL
REDIS_URL = settings.redis_url

class RedisClient:
    _client: Optional[redis.Redis] = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        """获取 Redis 客户端实例（单例模式）"""
        if cls._client is None:
            # 创建连接池，支持密码配置
            connection_kwargs = {
                "encoding": "utf-8",
                "decode_responses": True  # 自动解码为字符串
            }
            # 如果配置了密码，添加到连接参数
            if settings.redis_password:
                connection_kwargs["password"] = settings.redis_password
            
            cls._client = redis.from_url(REDIS_URL, **connection_kwargs)
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