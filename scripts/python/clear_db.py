import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlmodel import Session, text
from app.core.database import engine

def clear_alarms():
    print("🧹 正在清空历史报警记录...")
    with Session(engine) as session:
        # 执行 SQL 删除语句
        statement = text("DELETE FROM alarm")
        session.exec(statement)
        session.commit()
    print("✅ 历史报警已全部清除！数据库现在非常干净。")

if __name__ == "__main__":
    clear_alarms()