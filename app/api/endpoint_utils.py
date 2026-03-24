"""
API endpoint 复用工具
统一常见的错误转换和日志行为。
"""
from fastapi import HTTPException

from app.core.logger import logger


def bad_request_from_value_error(exc: ValueError) -> HTTPException:
    """将业务层 ValueError 转为 400 响应。"""
    return HTTPException(status_code=400, detail=str(exc))


def log_endpoint_exception(message: str, exc: Exception) -> None:
    """记录 endpoint 未预期异常。"""
    logger.exception(f"{message}: {exc}")
