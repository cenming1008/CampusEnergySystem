"""
故障诊断服务层
封装故障诊断相关的业务逻辑
"""
from typing import List, Dict, Any
from sqlmodel import Session, select, func

from app.models.tables import Alarm, Device


class FDDService:
    """故障诊断服务类"""
    
    @staticmethod
    def get_fault_diagnosis_stats(session: Session) -> List[Dict[str, Any]]:
        """获取设备故障诊断统计"""
        # 统计每个设备的报警次数
        statement = (
            select(Alarm.device_id, func.count(Alarm.id).label("count"))
            .group_by(Alarm.device_id)
            .order_by(func.count(Alarm.id).desc())
        )
        results = session.exec(statement).all()
        
        # 组装诊断报告
        diagnosis_report = []
        for device_id, alarm_count in results:
            device = session.get(Device, device_id)
            device_name = device.name if device else f"未知设备({device_id})"
            
            diagnosis_report.append({
                "device_id": device_id,
                "device_name": device_name,
                "alarm_count": alarm_count,
                "health_score": FDDService._calculate_health_score(alarm_count)
            })
        
        return diagnosis_report
    
    @staticmethod
    def _calculate_health_score(alarm_count: int) -> int:
        """计算设备健康分数"""
        return max(0, 100 - alarm_count * 5)

