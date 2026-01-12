# scripts/create_admin.py
from sqlmodel import Session, select
from app.core.database import engine
from app.models.tables import User
from app.core.security import get_password_hash

def init_admin():
    print("👤 正在创建管理员账号...")
    with Session(engine) as session:
        # 检查是否存在
        statement = select(User).where(User.username == "admin")
        result = session.exec(statement).first()
        if result:
            print("✅ 管理员已存在，跳过。")
            return

        admin_user = User(
            username="admin",
            hashed_password=get_password_hash("123456"), # 初始密码
            is_active=True
        )
        session.add(admin_user)
        session.commit()
    print("✅ 管理员创建成功！账号: admin / 密码: 123456")

if __name__ == "__main__":
    init_admin()