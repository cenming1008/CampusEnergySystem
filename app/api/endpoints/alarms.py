from typing import List #py标准库中的类型标注工具
from fastapi import APIRouter, Depends #接口模块化， 依赖注入，
from sqlmodel import Session, select # 数据库连接会话， 构建数据库sql查询
from app.core.database import get_session #负责创建和管理数据库会话 yield逻辑 确保结束请求时关闭连接
from app.models.tables import Alarm #导入已经定义好的数据库模型类

# 初始化 FastAPI 路由对象，用于定义该模块下的所有接口路径
router = APIRouter() # 定义一个装饰器 实例化路由对象

@router.get("/", response_model=List[Alarm]) #定义一个根目录下的 处理http get请求
def read_alarms(limit: int = 20, session: Session = Depends(get_session)):
    """
    获取最新的【未处理】报警记录。
    
    参数:
    - limit: 返回记录的数量限制，默认为 20 条。
    - session: 通过 FastAPI 依赖注入获取数据库会话对象。
    
    返回:
    - 符合条件的 Alarm 模型列表。
    """
    # 构建查询语句：
    # 1. select(Alarm): 指定查询的对象是 Alarm 表。
    # 2. .where(Alarm.is_resolved == False): 👈 关键逻辑：过滤出尚未被处理（未解决）的报警。
    # 3. .order_by(Alarm.timestamp.desc()): 按发生时间倒序排列，优先展示最新的报警。
    # 4. .limit(limit): 限制返回的数据行数。
    statement = (
        select(Alarm)
        .where(Alarm.is_resolved == False)
        .order_by(Alarm.timestamp.desc())
        .limit(limit)
    )
    
    # 执行查询并返回结果列表
    return session.exec(statement).all()

@router.post("/resolve-all")
def resolve_all_alarms(session: Session = Depends(get_session)):
    """
    一键清除所有报警（将所有未处理报警标记为已解决）。
    
    该操作常用于管理员批量确认当前系统中的所有异常情况。
    """
    # 1. 查找出数据库中所有处于“未解决”状态（is_resolved 为 False）的报警记录
    statement = select(Alarm).where(Alarm.is_resolved == False)
    alarms = session.exec(statement).all()
    
    # 2. 遍历结果集，将每一条报警记录的状态变更为“已解决” (True)
    for alarm in alarms:
        alarm.is_resolved = True
        # 将修改后的对象标记为待更新状态
        session.add(alarm)
    
    # 3. 提交数据库事务，使上述修改正式生效
    session.commit()
    
    # 4. 返回处理结果，包含成功标识以及本次清理的报警总数
    return {"ok": True, "count": len(alarms)}