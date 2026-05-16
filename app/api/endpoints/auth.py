"""
认证API端点
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.api.deps import get_current_user
from app.application.auth import (
    login_use_case,
    logout_use_case,
    refresh_access_token_use_case,
)
from app.core.database import get_session
from app.core.rate_limit import limit_requests
from app.core.settings import settings
from app.models.tables import User

router = APIRouter()


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


def _enforce_auth_login_rate_limit(request: Request) -> None:
    limit_requests(
        bucket="auth-login",
        max_calls=settings.auth_rate_limit_count,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )(request)


@router.post("/login")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    """用户登录"""
    return login_use_case(
        session=session,
        username=form_data.username,
        password=form_data.password,
        enforce_rate_limit=lambda: _enforce_auth_login_rate_limit(request),
    )


@router.post("/refresh")
def refresh_access_token(
    request: RefreshTokenRequest,
    session: Session = Depends(get_session),
):
    """使用 refresh token 获取新的 access token。"""
    return refresh_access_token_use_case(session=session, refresh_token=request.refresh_token)


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """当前用户登出，并使现有令牌失效。"""
    return logout_use_case(session=session, current_user=current_user)
