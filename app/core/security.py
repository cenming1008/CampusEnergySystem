"""
认证与密码学工具

- bcrypt 密码哈希/校验（含 72 bytes 截断处理）
- JWT access token 生成
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional, Union

from jose import jwt
from passlib.context import CryptContext

from app.core.exceptions import ValidationException
from app.core.settings import settings

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=False,
)


def _truncate_bcrypt_secret(secret: Union[str, bytes]) -> Union[str, bytes]:
    """
    bcrypt 只使用前 72 bytes。这里尽量按 bytes 截断以保持一致性。
    """
    if isinstance(secret, bytes):
        return secret[:72]

    # str -> bytes 截断（注意：可能截断多字节字符）
    raw = secret.encode("utf-8", errors="ignore")
    if len(raw) <= 72:
        return raw
    return raw[:72]


def verify_password(plain_password: Union[str, bytes], hashed_password: str) -> bool:
    """验证密码（包含 bcrypt 72 bytes 截断逻辑）。"""
    if not plain_password or not hashed_password:
        return False
    try:
        secret = _truncate_bcrypt_secret(plain_password)
        return bool(pwd_context.verify(secret, hashed_password))
    except Exception as exc:
        from app.core.logger import logger
        logger.warning(f"verify_password unexpected error: {type(exc).__name__}: {exc}")
        return False


def get_password_hash(password: Union[str, bytes]) -> str:
    """生成密码哈希（包含 bcrypt 72 bytes 截断逻辑）。"""
    if not password:
        raise ValueError("Password cannot be empty")
    secret = _truncate_bcrypt_secret(password)
    return pwd_context.hash(secret)


def validate_password_strength(password: Union[str, bytes]) -> str:
    """校验密码强度。当前仅要求至少 6 位。"""
    if isinstance(password, bytes):
        password_text = password.decode("utf-8", errors="ignore")
    else:
        password_text = password

    if len(password_text) < 6:
        raise ValidationException("密码长度至少 6 位")
    return password_text


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """生成 JWT access token。"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "typ": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """生成 JWT refresh token。"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.refresh_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "typ": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
