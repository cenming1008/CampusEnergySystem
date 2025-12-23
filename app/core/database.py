import os
from sqlmodel import SQLModel, create_engine, Session, text # 
from dotenv import load_dotenv

load_dotenv()

# 数据库连接串
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password123@localhost:5433/mine_energy")

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    # 1. 创建普通表结构
    SQLModel.metadata.create_all(engine)
    
    # 2. ⚡️ 启用 TimescaleDB Hypertable 特性
    print("⚡️ [TimescaleDB] 正在优化数据表存储结构...")
    with Session(engine) as session:
        try:
            # 执行转换命令
            # 'devicedata': 表名
            # 'timestamp': 按这个时间字段进行切片（分区）
            # if_not_exists=TRUE: 如果已经是超表了，就跳过不报错
            # migrate_data=TRUE: 如果表里已经有数据，也强制转换
            statement = text("SELECT create_hypertable('devicedata', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);")
            session.exec(statement)
            session.commit()
            print("✅ [TimescaleDB] 'devicedata' 表已成功转换为 Hypertable！性能优化完成。")
        except Exception as e:
            # 如果报错，可能是因为数据库不是 TimescaleDB 版本，或者权限不足
            print(f"⚠️ [TimescaleDB] 转换失败 (如果是普通 PostgreSQL 请忽略): {e}")

def get_session():
    with Session(engine) as session:
        yield session