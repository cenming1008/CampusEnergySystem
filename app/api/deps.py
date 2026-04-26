"""
依赖注入模块
提供通用的依赖项（如用户认证）
"""
from datetime import datetime
import ipaddress
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select

from app.core.auth_lock import build_account_lock_message
from app.core.database import get_session
from app.core.exceptions import AuthenticationException, PermissionDeniedException
from app.core.settings import settings
from app.models.tables import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
optional_bearer = HTTPBearer(auto_error=False)
PASSWORD_CHANGE_ALLOWED_PATHS = {
    "/users/me",
    "/users/me/password",
    "/auth/logout",
}


def decode_access_token(token: str) -> dict:
    """校验并解析 access token。"""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise AuthenticationException("Token无效")
        if payload.get("typ") == "refresh":
            raise AuthenticationException("访问令牌类型无效")
    except JWTError:
        raise AuthenticationException("Token验证失败")
    return payload


def get_user_from_token_payload(session: Session, payload: dict, request: Optional[Request] = None) -> User:
    username: str = payload.get("sub")
    # 查询用户
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()

    if user is None:
        raise AuthenticationException("用户不存在")
    if not user.is_active:
        raise AuthenticationException("用户已停用")
    if user.locked_until and user.locked_until > datetime.now():
        raise AuthenticationException(build_account_lock_message(user.locked_until))

    token_version = payload.get("ver")
    if token_version is not None and token_version != user.token_version:
        raise AuthenticationException("令牌已失效，请重新登录")

    if request is not None:
        request.state.current_user = user
    return user


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    """验证Token并返回当前用户"""
    payload = decode_access_token(token)
    return get_user_from_token_payload(session=session, payload=payload, request=request)


def get_optional_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
    session: Session = Depends(get_session),
) -> Optional[User]:
    """在带 Bearer Token 时解析用户，否则返回 None。"""
    if credentials is None:
        return None
    payload = decode_access_token(credentials.credentials)
    return get_user_from_token_payload(session=session, payload=payload, request=request)


def get_client_ip(request: Request) -> str:
    """提取客户端 IP。仅在请求来自内网/反代时信任第一个 X-Forwarded-For 值。"""
    client_host = request.client.host if request.client else ""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for and is_private_network_ip(client_host):
        forwarded_host = forwarded_for.split(",")[0].strip()
        if forwarded_host:
            return forwarded_host
    return client_host


def is_private_network_ip(host: str) -> bool:
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return address.is_private or address.is_loopback


def require_monitoring_access(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> None:
    """限制 /health /metrics 等运维端点访问来源。"""
    mode = settings.monitoring_access_mode
    if mode == "public":
        return

    is_internal = is_private_network_ip(get_client_ip(request))
    if mode == "internal" and is_internal:
        return
    if mode == "internal_or_jwt" and is_internal:
        return

    if current_user is not None:
        allowed_roles = {str(role).lower() for role in settings.monitoring_access_roles}
        if str(current_user.role).lower() in allowed_roles:
            return
        raise PermissionDeniedException("当前用户无权访问监控端点")

    if mode == "jwt":
        raise AuthenticationException("监控端点需要 Bearer Token")
    if mode == "internal_or_jwt":
        raise HTTPException(status_code=403, detail="监控端点仅允许内网访问或携带有效凭证")
    raise HTTPException(status_code=403, detail="监控端点仅允许内网访问")


def require_roles(*allowed_roles: str):
    """生成角色校验依赖。"""

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise PermissionDeniedException(
                f"当前操作需要角色: {', '.join(allowed_roles)}"
            )
        return current_user

    return dependency


def ensure_password_change_completed(request: Request) -> None:
    """要求标记为必须改密的用户先完成自助改密。"""
    current_user = getattr(request.state, "current_user", None)
    if not current_user or not getattr(current_user, "must_change_password", False):
        return

    if request.url.path in PASSWORD_CHANGE_ALLOWED_PATHS:
        return

    raise PermissionDeniedException("首次登录后必须先修改密码")


ADMIN_ONLY = require_roles(UserRole.ADMIN)
OPERATOR_OR_ADMIN = require_roles(UserRole.ADMIN, UserRole.OPERATOR)
MAINTAINER_OR_ADMIN = require_roles(UserRole.ADMIN, UserRole.MAINTAINER)
MAINTAINER_OPERATOR_OR_ADMIN = require_roles(
    UserRole.ADMIN,
    UserRole.OPERATOR,
    UserRole.MAINTAINER,
)
