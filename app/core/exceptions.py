"""
统一异常处理模块
定义业务异常类型，便于API层统一处理
"""
from typing import Any, Optional


class AppException(Exception):
    """应用基础异常类"""
    
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 400,
        details: Optional[Any] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class ResourceNotFoundException(AppException):
    """资源不存在异常"""
    
    def __init__(self, resource: str, resource_id: Any):
        super().__init__(
            message=f"{resource} (ID: {resource_id}) 不存在",
            code="RESOURCE_NOT_FOUND",
            status_code=404
        )


class AuthenticationException(AppException):
    """认证失败异常"""
    
    def __init__(self, message: str = "认证失败"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_FAILED",
            status_code=401
        )


class ValidationException(AppException):
    """数据验证失败异常"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details
        )


class DatabaseException(AppException):
    """数据库操作异常"""
    
    def __init__(self, message: str = "数据库操作失败"):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=500
        )

