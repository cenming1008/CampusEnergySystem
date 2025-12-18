from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from app.core.database import get_session
from app.models.tables import Alarm, Device

router = APIRouter()

@router.get("/stats")
def fault_diagnosis_stats(session: Session = Depends(get_session)):
    """
    FDD 分析：统计每个设备的报警次数，找出“故障王”
    """
    # SQL 逻辑: SELECT device_id, count(*) FROM alarm GROUP BY device_id
    # 注意：这里需要稍微复杂的 SQLAlchemy 语法
    
    # 1. 统计每个 ID 的报警数
    statement = (
        select(Alarm.device_id, func.count(Alarm.id).label("count"))
        .group_by(Alarm.device_id)
        .order_by(func.count(Alarm.id).desc())
    )
    results = session.exec(statement).all()
    
    # 2. 组装数据，加上设备名称
    diagnosis_report = []
    for dev_id, count in results:
        # 查询设备名称
        dev = session.get(Device, dev_id)
        dev_name = dev.name if dev else f"未知设备({dev_id})"
        
        diagnosis_report.append({
            "device_id": dev_id,
            "device_name": dev_name,
            "alarm_count": count,
            "health_score": max(0, 100 - count * 5) # 简单算法：一次报警扣5分
        })
        
    return diagnosis_report