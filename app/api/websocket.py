"""
WebSocket 路由
"""

from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jose import JWTError
from sqlmodel import Session

from app.api.deps import decode_access_token, get_user_from_token_payload
from app.core.database import engine
from app.core.logger import logger
from app.core.socket_manager import manager
from app.core.settings import settings


router = APIRouter()


def authenticate_websocket_token(websocket: WebSocket) -> Optional[str]:
    return websocket.query_params.get("access_token") or websocket.query_params.get("token")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket 实时数据推送。"""
    logger.info("🔌 收到 WebSocket 连接请求")
    if settings.websocket_auth_mode != "disabled":
        token = authenticate_websocket_token(websocket)
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="missing_token")
            return
        try:
            payload = decode_access_token(token)
            with Session(engine) as session:
                user = get_user_from_token_payload(session=session, payload=payload)
            websocket.state.current_user = user
        except (JWTError, Exception) as exc:
            logger.warning(f"WebSocket 鉴权失败: {exc}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="invalid_token")
            return
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
