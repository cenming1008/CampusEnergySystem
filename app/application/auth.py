"""
认证主流程 use case。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from jose import JWTError, jwt
from sqlmodel import Session, select

from app.core.audit import audit_log
from app.core.auth_lock import build_account_lock_message
from app.core.exceptions import AuthenticationException
from app.core.logger import logger
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.core.settings import settings
from app.models.tables import User
from app.services.user_service import UserService


def _build_token_response(user: User) -> dict[str, Any]:
    token_payload = {"sub": user.username, "ver": user.token_version, "role": user.role}
    return {
        "access_token": create_access_token(data=token_payload),
        "refresh_token": create_refresh_token(data=token_payload),
        "token_type": "bearer",
        "role": user.role,
        "must_change_password": user.must_change_password,
    }


def login_use_case(
    session: Session,
    username: str,
    password: str,
    enforce_rate_limit: Callable[[], None],
) -> dict[str, Any]:
    """用户登录主流程：查用户、锁定判定、限流、密码校验、登记成功、签发令牌。"""
    user = session.exec(select(User).where(User.username == username)).first()

    if user and user.locked_until and user.locked_until > datetime.now():
        audit_log("auth.login", user.username, "auth", outcome="failed", reason="locked")
        raise AuthenticationException(build_account_lock_message(user.locked_until))

    enforce_rate_limit()

    if not user or not verify_password(password, user.hashed_password):
        logger.warning(f"登录失败: username={username}")
        failed_user = UserService.register_login_failure(session, username)
        if failed_user and failed_user.locked_until and failed_user.locked_until > datetime.now():
            audit_log("auth.login", username, "auth", outcome="failed", reason="locked")
            raise AuthenticationException(build_account_lock_message(failed_user.locked_until))
        audit_log("auth.login", username, "auth", outcome="failed")
        raise AuthenticationException("用户名或密码错误")

    if not user.is_active:
        audit_log("auth.login", user.username, "auth", outcome="failed", reason="inactive")
        raise AuthenticationException("用户已停用")

    user = UserService.register_login_success(session, user)
    response = _build_token_response(user)
    audit_log(
        "auth.login",
        user.username,
        "auth",
        role=user.role,
        must_change_password=user.must_change_password,
    )
    return response


def refresh_access_token_use_case(session: Session, refresh_token: str) -> dict[str, Any]:
    """使用 refresh token 轮换会话并签发新令牌。"""
    try:
        payload = jwt.decode(
            refresh_token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except JWTError:
        audit_log("auth.refresh", "anonymous", "auth", outcome="failed", reason="invalid_token")
        raise AuthenticationException("刷新令牌无效")

    if payload.get("typ") != "refresh":
        audit_log(
            "auth.refresh",
            str(payload.get("sub") or "anonymous"),
            "auth",
            outcome="failed",
            reason="invalid_type",
        )
        raise AuthenticationException("刷新令牌类型无效")

    username = payload.get("sub")
    if not username:
        raise AuthenticationException("刷新令牌无效")

    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not user.is_active:
        audit_log(
            "auth.refresh",
            username,
            "auth",
            outcome="failed",
            reason="inactive_or_missing",
        )
        raise AuthenticationException("用户不存在或已停用")
    if user.locked_until and user.locked_until > datetime.now():
        audit_log("auth.refresh", user.username, "auth", outcome="failed", reason="locked")
        raise AuthenticationException(build_account_lock_message(user.locked_until))
    if payload.get("ver") != user.token_version:
        audit_log("auth.refresh", user.username, "auth", outcome="failed", reason="token_revoked")
        raise AuthenticationException("刷新令牌已失效，请重新登录")

    user = UserService.rotate_refresh_session(session, user.id)
    response = _build_token_response(user)
    audit_log("auth.refresh", user.username, "auth", role=user.role, rotated=True)
    return response


def logout_use_case(session: Session, current_user: User) -> dict[str, Any]:
    """当前用户登出，吊销现有令牌。"""
    user = UserService.revoke_user_tokens(session, current_user.id)
    audit_log("auth.logout", current_user.username, "auth", role=current_user.role)
    return {
        "success": True,
        "message": "已退出登录",
        "token_version": user.token_version,
    }
