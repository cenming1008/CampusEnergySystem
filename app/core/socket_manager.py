from typing import List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # 存放所有活跃的 WebSocket 连接
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """向所有连接的客户端发送消息"""
        # 遍历所有连接，发送 JSON 数据
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # 如果发送失败（比如连接断开），移除该连接
                self.disconnect(connection)

# 实例化一个全局对象供其他模块使用
manager = ConnectionManager()