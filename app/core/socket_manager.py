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
        logger.debug(f"WebSocket connected, total={len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.debug(f"WebSocket disconnected, total={len(self.active_connections)}")

    async def broadcast(self, message: dict[str, Any]) -> None:
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()