import os
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv  # 导入加载工具

# 1. 加载 .env 文件中的变量
load_dotenv()

# 2. 读取 DATABASE_URL，如果读不到，就用后面那个作为默认值
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password123@localhost:5433/mine_energy")

# print(f"当前连接数据库: {DATABASE_URL}") # 调试用，上线记得注释掉

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session