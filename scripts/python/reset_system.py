import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlmodel import Session, text
from app.core.database import engine

def factory_reset():
    print("🧨 正在执行工厂重置...")
    with Session(engine) as session:
        # TRUNCATE 是强力删除，RESTART IDENTITY 会把 ID 变回 1，CASCADE 会连带删除关联的数据和报警
        statement = text("TRUNCATE TABLE Device, DeviceData, alarm RESTART IDENTITY CASCADE;")
        session.exec(statement)
        session.commit()
    print("✅ 系统已重置！数据库现在是一张白纸 (ID 从 1 开始)。")

if __name__ == "__main__":
    factory_reset()