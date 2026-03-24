"""
WebSocket 路由
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logger import logger
from app.core.socket_manager import manager


router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket 实时数据推送。"""
    logger.info("🔌 收到 WebSocket 连接请求")
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.error(f"WebSocket 错误: {exc}")
    finally:
        manager.disconnect(websocket)
