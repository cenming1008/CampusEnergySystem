"""
统一响应格式模块
规范API返回数据结构。当前 API 主要使用 success_response/error_response 返回 dict；
以下 Pydantic 模型保留供 OpenAPI 文档或后续统一响应体使用。
"""
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

try:
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover - Pydantic v1 fallback
    ConfigDict = None  # type: ignore[assignment]

DataT = TypeVar("DataT")


class ApiResponse(BaseModel, Generic[DataT]):
    """标准API响应格式（OpenAPI/文档用）"""
    if ConfigDict is not None:
        model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool = True
    message: str = "操作成功"
    data: Optional[DataT] = None
    code: str = "SUCCESS"


class ErrorResponse(BaseModel):
    """错误响应格式（OpenAPI/文档用）"""
    success: bool = False
    message: str
    code: str
    details: Optional[Any] = None


class PaginatedResponse(BaseModel, Generic[DataT]):
    """分页响应格式（OpenAPI/文档用）"""
    if ConfigDict is not None:
        model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool = True
    data: list[DataT]
    total: int
    page: int
    page_size: int


def success_response(data: Any = None, message: str = "操作成功") -> dict:
    """成功响应快捷方法"""
    return {
        "success": True,
        "message": message,
        "data": data,
        "code": "SUCCESS"
    }


def error_response(
    message: str,
    code: str = "ERROR",
    details: Any = None
) -> dict:
    """错误响应快捷方法"""
    return {
        "success": False,
        "message": message,
        "code": code,
        "details": details
    }
