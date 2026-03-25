"""
认证API端点
"""
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.rate_limit import limit_requests
from app.core.settings import settings
from app.core.security import verify_password, create_access_token
from app.core.exceptions import AuthenticationException
from app.models.tables import User

router = APIRouter()


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
    
    # 验证密码
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise AuthenticationException("用户名或密码错误")
    
    # 生成Token
    access_token = create_access_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
