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

from app.core.settings import settings

# 兼容旧代码：保留这些常量导出（推荐直接使用 settings）
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

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
    except Exception:
        return False


def get_password_hash(password: Union[str, bytes]) -> str:
    """生成密码哈希（包含 bcrypt 72 bytes 截断逻辑）。"""
    if not password:
        raise ValueError("Password cannot be empty")
    secret = _truncate_bcrypt_secret(password)
    return pwd_context.hash(secret)


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """生成 JWT access token。"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)