"""
前端异常上报端点。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.core.logger import logger
from app.core.metrics import observe_frontend_error
from app.core.rate_limit import limit_requests
from app.core.response import success_response


router = APIRouter()


class FrontendErrorPayload(BaseModel):
    category: str = Field(default="runtime", max_length=50)
    message: str = Field(..., min_length=1, max_length=4000)
    url: Optional[str] = Field(default=None, max_length=2000)
    route: Optional[str] = Field(default=None, max_length=500)
    stack: Optional[str] = Field(default=None, max_length=12000)
    user_agent: Optional[str] = Field(default=None, max_length=1000)
    metadata: Optional[Dict[str, Any]] = None


@router.post("/frontend-errors")
def ingest_frontend_error(
    payload: FrontendErrorPayload,
    request: Request,
    _: None = Depends(limit_requests(bucket="frontend-errors", max_calls=30, window_seconds=60)),
):
    client_ip = request.client.host if request.client else "unknown"
    observe_frontend_error(payload.category)
    logger.bind(
        source="frontend",
        category=payload.category,
        route=payload.route,
        url=payload.url,
        client_ip=client_ip,
        user_agent=payload.user_agent,
    ).error(payload.message)
    if payload.stack:
        logger.bind(source="frontend", category=payload.category).debug(payload.stack)
    return success_response(data={"accepted": True}, message="前端异常已接收")
