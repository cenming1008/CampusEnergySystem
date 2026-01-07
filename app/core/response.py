"""
统一响应格式模块
规范API返回数据结构
"""
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

DataT = TypeVar("DataT")


class ApiResponse(BaseModel, Generic[DataT]):
    """标准API响应格式"""
    
    success: bool = True
    message: str = "操作成功"
    data: Optional[DataT] = None
    code: str = "SUCCESS"
    
    class Config:
        arbitrary_types_allowed = True


class ErrorResponse(BaseModel):
    """错误响应格式"""
    
    success: bool = False
    message: str
    code: str
    details: Optional[Any] = None


class PaginatedResponse(BaseModel, Generic[DataT]):
    """分页响应格式"""
    
    success: bool = True
    data: list[DataT]
    total: int
    page: int
    page_size: int
    
    class Config:
        arbitrary_types_allowed = True


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

