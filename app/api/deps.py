"""
依赖注入模块
提供通用的依赖项（如用户认证）
"""
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.settings import settings
from app.core.exceptions import AuthenticationException
from app.models.tables import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    """验证Token并返回当前用户"""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise AuthenticationException("Token无效")
    except JWTError:
        raise AuthenticationException("Token验证失败")
    
    # 查询用户
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()
    
    if user is None:
        raise AuthenticationException("用户不存在")
    
    return user