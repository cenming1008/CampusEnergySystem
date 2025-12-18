# app/api/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from app.core.database import get_session
from app.core.security import verify_password, create_access_token
from app.models.tables import User

router = APIRouter()

@router.post("/login", response_model=dict)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    # 1. 查用户
    statement = select(User).where(User.username == form_data.username)
    user = session.exec(statement).first()
    
    # 2. 验密码
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    
    # 3. 发 Token
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}