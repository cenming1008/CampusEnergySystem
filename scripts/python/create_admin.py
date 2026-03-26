import sys
import os
import getpass

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.tables import User, UserRole
from app.core.security import get_password_hash, validate_password_strength


def _resolve_admin_password() -> str:
    password = os.getenv("ADMIN_PASSWORD")
    if password:
        return validate_password_strength(password)

    print("请为管理员 admin 设置初始密码。")
    print("要求：至少 12 位，包含大小写字母、数字和特殊字符。")
    while True:
        password = getpass.getpass("Admin password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("两次输入的密码不一致，请重试。")
            continue
        try:
            return validate_password_strength(password)
        except ValueError as exc:
            print(f"密码不符合要求: {exc}")

def init_admin():
    print("👤 正在创建管理员账号...")
    with Session(engine) as session:
        # 检查是否存在
        statement = select(User).where(User.username == "admin")
        result = session.exec(statement).first()
        if result:
            print("✅ 管理员已存在，跳过。")
            return

        password = _resolve_admin_password()
        admin_user = User(
            username="admin",
            hashed_password=get_password_hash(password),
            role=UserRole.ADMIN,
            is_active=True
        )
        session.add(admin_user)
        session.commit()
    print("✅ 管理员创建成功！账号: admin")

if __name__ == "__main__":
    init_admin()
