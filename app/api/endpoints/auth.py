"""
认证API端点
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.core.database import get_session
from app.core.audit import audit_log
from app.core.rate_limit import limit_requests
from app.core.settings import settings
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.core.exceptions import AuthenticationException
from app.models.tables import User
from app.core.logger import logger
from app.services.user_service import UserService

router = APIRouter()


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
    _: None = Depends(
        limit_requests(
            bucket="auth-login",
            max_calls=settings.auth_rate_limit_count,
            window_seconds=settings.auth_rate_limit_window_seconds,
        )
    ),
):
    """用户登录"""
    # 查询用户
    statement = select(User).where(User.username == form_data.username)
    user = session.exec(statement).first()

    if user and user.locked_until and user.locked_until > datetime.now():
        audit_log("auth.login", user.username, "auth", outcome="failed", reason="locked")
        raise AuthenticationException("账户已被锁定，请稍后再试")
    
    # 验证密码
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"登录失败: username={form_data.username}")
        UserService.register_login_failure(session, form_data.username)
        audit_log("auth.login", form_data.username, "auth", outcome="failed")
        raise AuthenticationException("用户名或密码错误")

    if not user.is_active:
        audit_log("auth.login", user.username, "auth", outcome="failed", reason="inactive")
        raise AuthenticationException("用户已停用")

    user = UserService.register_login_success(session, user)
    # 生成Token
    token_payload = {"sub": user.username, "ver": user.token_version, "role": user.role}
    access_token = create_access_token(data=token_payload)
    refresh_token = create_refresh_token(data=token_payload)
    audit_log("auth.login", user.username, "auth", role=user.role, must_change_password=user.must_change_password)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.role,
        "must_change_password": user.must_change_password,
    }


@router.post("/refresh")
def refresh_access_token(
    request: RefreshTokenRequest,
    session: Session = Depends(get_session),
):
    """使用 refresh token 获取新的 access token。"""
    try:
        payload = jwt.decode(
            request.refresh_token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except JWTError:
        audit_log("auth.refresh", "anonymous", "auth", outcome="failed", reason="invalid_token")
        raise AuthenticationException("刷新令牌无效")

    if payload.get("typ") != "refresh":
        audit_log("auth.refresh", str(payload.get("sub") or "anonymous"), "auth", outcome="failed", reason="invalid_type")
        raise AuthenticationException("刷新令牌类型无效")

    username = payload.get("sub")
    if not username:
        raise AuthenticationException("刷新令牌无效")

    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not user.is_active:
        audit_log("auth.refresh", username, "auth", outcome="failed", reason="inactive_or_missing")
        raise AuthenticationException("用户不存在或已停用")
    if user.locked_until and user.locked_until > datetime.now():
        audit_log("auth.refresh", user.username, "auth", outcome="failed", reason="locked")
        raise AuthenticationException("账户已被锁定，请稍后再试")
    if payload.get("ver") != user.token_version:
        audit_log("auth.refresh", user.username, "auth", outcome="failed", reason="token_revoked")
        raise AuthenticationException("刷新令牌已失效，请重新登录")

    user = UserService.rotate_refresh_session(session, user.id)
    token_payload = {"sub": user.username, "ver": user.token_version, "role": user.role}
    access_token = create_access_token(data=token_payload)
    refresh_token = create_refresh_token(data=token_payload)
    audit_log("auth.refresh", user.username, "auth", role=user.role, rotated=True)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.role,
        "must_change_password": user.must_change_password,
    }


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """当前用户登出，并使现有令牌失效。"""
    user = UserService.revoke_user_tokens(session, current_user.id)
    audit_log("auth.logout", current_user.username, "auth", role=current_user.role)
    return {
        "success": True,
        "message": "已退出登录",
        "token_version": user.token_version,
    }
