"""
故障诊断服务层
封装故障诊断相关的业务逻辑
"""
from typing import List, Dict, Any, Tuple
from sqlmodel import Session, select, func
from datetime import datetime, timedelta
from app.models.tables import Alarm, Device, EnergyData
from app.core.logger import logger
from app.core.settings import settings

class FDDService:
    """故障诊断服务类
    
    提供设备故障诊断和健康评估功能，包括：
    - 设备健康分数计算
    - 报警数据分析
    - 运行数据分析
    - 故障诊断建议生成
    """
    
    @staticmethod
    def diagnose_device(session: Session, device_id: int) -> Dict[str, Any]:
        """
        诊断指定设备的健康状况
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            
        Returns:
            包含设备诊断结果的字典，包括：
            - device_id: 设备ID
            - device_name: 设备名称
            - health_score: 健康分数（0-100）
            - suggestions: 诊断建议列表
            如果设备不存在，返回 {"error": "Device not found"}
        """
        # 获取设备信息
        device = session.get(Device, device_id)
        if not device:
            return {"error": "Device not found"}
        
        # 设置时间范围：分析最近24小时的数据
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        # 分析报警数据
        alarm_stats = FDDService._analyze_alarms(session, device_id, start_time)
        # 分析运行数据（电压、电流、功率等）
        data_stats = FDDService._analyze_running_data(session, device_id, start_time)
        # 计算健康分数和扣分明细
        health_score, deductions = FDDService._calculate_health_score(alarm_stats, data_stats)
        # 生成诊断建议
        suggestions = FDDService._generate_suggestions(deductions)

        return {
            "device_id": device_id,
            "device_name": device.name,
            "health_score": health_score,
            "suggestions": suggestions
        }

    @staticmethod
    def get_fault_diagnosis_stats(session: Session) -> List[Dict[str, Any]]:
        """
        获取所有设备的故障诊断统计信息
        
        Args:
            session: 数据库会话
            
        Returns:
            设备诊断统计列表，每个元素包含：
            - device_id: 设备ID
            - device_name: 设备名称
            - alarm_count: 未解决的报警数量
            - health_score: 健康分数（0-100）
            - status: 健康状态（healthy/warning/critical）
        """
        # 一次查询：按设备聚合未解决报警数量，避免 N+1
        alarm_counts_stmt = (
            select(Alarm.device_id, func.count(Alarm.id).label("cnt"))
            .where(Alarm.is_resolved == False)
            .group_by(Alarm.device_id)
        )
        alarm_counts_rows = session.exec(alarm_counts_stmt).all()
        alarm_by_device = {row[0]: row[1] for row in alarm_counts_rows}

        devices = session.exec(select(Device)).all()
        results = []
        for device in devices:
            alarm_count = alarm_by_device.get(device.id, 0)
            simple_score = max(0, 100 - alarm_count * 10)
            if simple_score >= 80:
                status = "healthy"
            elif simple_score >= 60:
                status = "warning"
            else:
                status = "critical"
            results.append({
                "device_id": device.id,
                "device_name": device.name,
                "alarm_count": alarm_count,
                "health_score": simple_score,
                "status": status,
            })
        return results
        

    @staticmethod
    def _analyze_alarms(session: Session, device_id: int, start_time: datetime) -> Dict[str, Any]:
        """
        分析指定设备在时间范围内的报警数据
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            start_time: 开始时间
            
        Returns:
            报警统计字典，包含：
            - total_count: 总报警数量
            - unresolved_count: 未解决报警数量
        """
        # 获取指定时间范围内的所有报警记录（需要完整对象以访问is_resolved属性）
        statement = (
            select(Alarm)
            .where(Alarm.device_id == device_id)
            .where(Alarm.timestamp >= start_time)
        )
        alarms = session.exec(statement).all()
        
        # 统计总数量和未解决数量
        unresolved_count = sum(1 for alarm in alarms if not alarm.is_resolved)
        
        return {
            "total_count": len(alarms),
            "unresolved_count": unresolved_count
        }

    @staticmethod
    def _analyze_running_data(session: Session, device_id: int, start_time: datetime) -> Dict[str, Any]:
        """
        分析设备运行数据（电压、电流、功率等）
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            start_time: 开始时间
            
        Returns:
            运行数据统计字典，包含：
            - voltage_stability: 电压稳定性（Good/Poor/Unknown）
            - avg_load_factor: 平均负载率
            - is_overloaded: 是否过载
            - fluctuation: 电压波动百分比
            - max_current: 最大电流
            - avg_current: 平均电流
        """
        # 获取指定时间范围内的设备运行数据
        statement = (
            select(EnergyData.voltage, EnergyData.current, EnergyData.flow_rate)
            .where(EnergyData.device_id == device_id)
            .where(EnergyData.timestamp >= start_time)
            .order_by(EnergyData.timestamp.asc())
        )
        data = session.exec(statement).all()

        # 如果没有数据，返回默认值
        if not data:
            return {
                "voltage_stability": "Unknown",
                "avg_load_factor": 0.0,
                "is_overloaded": False,
                "fluctuation": 0.0,
                "max_current": 0.0,
                "avg_current": 0.0,
            }

        # 分析电压数据
        voltages = [d.voltage or 0 for d in data if d.voltage is not None]
        if not voltages:
            voltages = [0]
        max_v = max(voltages)
        min_v = min(voltages)

        # 计算电压波动：相对于额定电压380V的最大偏差百分比
        RATED_VOLTAGE = 380.0
        max_deviation = max(abs(max_v - RATED_VOLTAGE), abs(min_v - RATED_VOLTAGE))
        fluctuation = max_deviation / RATED_VOLTAGE
        
        # 判断电压稳定性
        voltage_stability = "Good"
        limit = settings.fdd_voltage_fluctuation_limit
        if fluctuation > limit:
            voltage_stability = "Poor"

        # 分析电流数据
        currents = [d.current or 0 for d in data if d.current is not None]
        if not currents:
            currents = [0]
        max_c = max(currents)
        avg_c = sum(currents) / len(currents)

        # 分析功率和负载率
        avg_power = sum((d.flow_rate or 0) for d in data) / len(data)
        # 使用配置的额定功率计算负载率
        load_factor = avg_power / settings.fdd_rated_power

        # 判断是否过载
        is_overloaded = load_factor > settings.fdd_overload_ratio

        return {
            "voltage_stability": voltage_stability,
            "avg_load_factor": round(load_factor, 2),
            "is_overloaded": is_overloaded,
            "fluctuation": round(fluctuation * 100, 1),  # 转换为百分比
            "max_current": round(max_c, 2),
            "avg_current": round(avg_c, 2),
        }
    
    @staticmethod
    def _calculate_health_score(alarm_stats: Dict[str, Any], data_stats: Dict[str, Any]) -> Tuple[int, List[str]]:
        """
        计算设备健康分数和扣分明细
        
        评分规则：
        - 基础分数：100分
        - 未解决报警：每个扣10分
        - 报警次数过多：超过阈值后，每多一个扣10分
        - 负载过高：扣20分
        - 电压不稳定：扣10分
        
        Args:
            alarm_stats: 报警统计数据
            data_stats: 运行统计数据
            
        Returns:
            元组 (健康分数, 扣分明细列表)
            健康分数范围：0-100
        """
        # 初始分数为100分
        score = 100
        deductions = []

        # 扣分规则1：未解决的报警
        if alarm_stats["unresolved_count"] > 0:
            deduct = alarm_stats["unresolved_count"] * 10
            deductions.append(f"未解决报警 {alarm_stats['unresolved_count']} 个，扣 {deduct} 分")
            score -= deduct

        # 扣分规则2：报警次数过多（超过阈值）
        if alarm_stats["total_count"] > settings.fdd_alarm_threshold:
            excess_count = alarm_stats["total_count"] - settings.fdd_alarm_threshold
            deduct = excess_count * 10
            deductions.append(f"报警次数过多（{alarm_stats['total_count']} 次，超过阈值 {settings.fdd_alarm_threshold} 次），扣 {deduct} 分")
            score -= deduct

        # 扣分规则3：负载过高
        if data_stats["is_overloaded"]:
            deduct = 20
            deductions.append(f"负载过高（负载率 {data_stats['avg_load_factor']}），扣 {deduct} 分")
            score -= deduct

        # 扣分规则4：电压不稳定
        if data_stats["voltage_stability"] == "Poor":
            deduct = 10
            deductions.append(f"电压不稳定（波动 {data_stats['fluctuation']}%），扣 {deduct} 分")
            score -= deduct

        # 确保分数不低于0
        final_score = max(0, score)
        return (final_score, deductions)

    @staticmethod
    def _generate_suggestions(deductions: List[str]) -> List[str]:
        """
        根据扣分明细生成诊断建议
        
        Args:
            deductions: 扣分明细列表
            
        Returns:
            诊断建议列表
        """
        suggestions = []
        
        # 如果没有扣分，说明设备运行正常
        if not deductions:
            suggestions.append("设备运行正常，无需处理")
            return suggestions

        # 添加建议标题
        suggestions.append("设备故障诊断建议：")
        
        # 根据扣分原因生成具体建议
        for deduction in deductions:
            if "报警" in deduction:
                if "未解决" in deduction:
                    suggestions.append("• 请及时处理未解决的报警，避免故障扩大")
                elif "过多" in deduction:
                    suggestions.append("• 报警频率过高，建议检查设备运行状态和报警阈值设置")
            elif "负载" in deduction:
                suggestions.append("• 设备负载过高，建议减少负载或检查设备容量配置")
            elif "电压" in deduction:
                suggestions.append("• 电压波动较大，建议检查供电系统稳定性")
            else:
                suggestions.append(f"• {deduction}")

        return suggestions
    
   