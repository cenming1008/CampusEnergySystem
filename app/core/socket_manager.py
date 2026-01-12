"""
WebSocket 连接管理器

- 维护当前活跃连接列表
- 提供 broadcast 能力用于推送实时数据
"""

from __future__ import annotations

from typing import Any

from fastapi import WebSocket

from app.core.logger import logger


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"✅ WebSocket 客户端已连接，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"❌ WebSocket 客户端已断开，当前连接数: {len(self.active_connections)}")

    async def broadcast(self, message: dict[str, Any]) -> None:
        """广播消息给所有活跃的WebSocket连接"""
        if not self.active_connections:
            logger.debug("📡 无活跃WebSocket连接，跳过广播")
            return
        
        logger.debug(f"📡 开始广播消息给 {len(self.active_connections)} 个连接: {message.get('type', 'unknown')}")
        disconnected = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"⚠️ WebSocket发送失败，断开连接: {e}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)
        
        if disconnected:
            logger.info(f"📡 广播完成，成功: {len(self.active_connections)}，失败: {len(disconnected)}")
        else:
            logger.debug(f"📡 广播完成，所有 {len(self.active_connections)} 个连接成功")


manager = ConnectionManager()