"""
全局异常处理器
统一捕获和处理各类异常
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import AppException
from app.core.response import error_response
from app.core.logger import logger


async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    """处理自定义应用异常"""
    logger.warning(f"业务异常: {exc.code} - {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            message=exc.message,
            code=exc.code,
            details=exc.details
        )
    )


async def validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """处理请求参数验证异常"""
    logger.warning(f"参数验证失败: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(
            message="请求参数验证失败",
            code="VALIDATION_ERROR",
            details=exc.errors()
        )
    )


async def sqlalchemy_exception_handler(
    _request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """处理数据库异常"""
    logger.error(f"数据库异常: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            message="数据库操作失败",
            code="DATABASE_ERROR"
        )
    )


async def general_exception_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    """处理未捕获的通用异常"""
    logger.exception(f"未处理异常: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            message="服务器内部错误",
            code="INTERNAL_ERROR"
        )
    )


def register_exception_handlers(app):
    """注册所有异常处理器"""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

