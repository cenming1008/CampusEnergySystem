from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import jwt #JSON Web TOken
from passlib.context import CryptContext #pyD的哈希库
 
# ⚠️ 生产环境请务必修改这个密钥，并放入环境变量！
SECRET_KEY = "mine-energy-system-secret-key-change-me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300 # Token 有效期 5 小时


pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__truncate_error=False  # 允许自动截断超过72字节的密码
)

def verify_password(plain_password: Union[str, bytes], hashed_password: str) -> bool:
    """
    验证密码，包含针对 bcrypt 限制的手动截断逻辑
    """
    if plain_password is None:
        return False
        
    try:
        # 1. 确保转换为 bytes
        if isinstance(plain_password, str):
            try:
                password_bytes = plain_password.encode('utf-8')
            except UnicodeError:
                return False
        elif isinstance(plain_password, bytes):
            password_bytes = plain_password
        else:
            return False

        # 2. 手动截断到 72 字节 (Bcrypt 限制)
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
                
        # 3. 传入截断后的 bytes 进行验证
        return pwd_context.verify(password_bytes, hashed_password)
    except ValueError as e:
        # 如果仍然出现长度错误，再次确保截断
        if "72 bytes" in str(e) or "longer than" in str(e).lower():
            if isinstance(plain_password, str):
                password_str = plain_password[:72] if len(plain_password.encode('utf-8')) > 72 else plain_password
                return pwd_context.verify(password_str, hashed_password)
        return False
    except Exception:
        return False

def get_password_hash(password: Union[str, bytes]) -> str:
    """
    生成密码哈希，包含针对 bcrypt 限制的手动截断逻辑
    """
    if not password:
         raise ValueError("Password cannot be empty")

    try:
        # 1. 确保转换为 bytes
        if isinstance(password, str):
            password_bytes = password.encode('utf-8')
        else:
            password_bytes = password

        # 2. 手动截断到 72 字节
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
                
        # 3. 传入截断后的 bytes 生成哈希
        return pwd_context.hash(password_bytes)
    except ValueError as e:
        # 如果仍然出现长度错误，再次确保截断
        if "72 bytes" in str(e) or "longer than" in str(e).lower():
            if isinstance(password, str):
                # 按字符截断（更安全，避免截断多字节字符）
                password_str = password
                while len(password_str.encode('utf-8')) > 72:
                    password_str = password_str[:-1]
                return pwd_context.hash(password_str)
            else:
                return pwd_context.hash(password_bytes[:72])
        raise

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt