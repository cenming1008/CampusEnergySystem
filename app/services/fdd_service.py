"""
故障诊断服务（编排层）

职责：
- 调 domain 层的纯业务规则（健康分数、扣分、建议生成、统计计算）
- 调 repository 层的数据访问
- 处理副作用（日志）

业务规则在 app/domain/fdd_rules.py，数据查询在 app/repositories/fdd_repository.py。
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlmodel import Session

from app.core.settings import settings
from app.domain import fdd_rules
from app.domain.fdd_rules import (
    AlarmStats,
    FDDConfig,
    TelemetrySample,
)
from app.repositories.fdd_repository import FDDRepository


def _build_fdd_config() -> FDDConfig:
    """从全局 settings 构造 FDDConfig。"""
    return FDDConfig(
        voltage_fluctuation_limit=settings.fdd_voltage_fluctuation_limit,
        overload_ratio=settings.fdd_overload_ratio,
        rated_power=settings.fdd_rated_power,
        alarm_threshold=settings.fdd_alarm_threshold,
    )


class FDDService:
    """故障诊断服务（编排层）。"""

    @staticmethod
    def diagnose_device(session: Session, device_id: int) -> Dict[str, Any]:
        """诊断指定设备的健康状况。"""
        device = FDDRepository.get_device_by_id(session, device_id)
        if not device:
            return {"error": "Device not found"}

        # 时间范围：最近 24 小时
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)

        config = _build_fdd_config()

        # 1. 报警分析
        alarm_records = FDDRepository.list_device_alarms_since(session, device_id, start_time)
        alarm_stats = AlarmStats(
            total_count=len(alarm_records),
            unresolved_count=sum(1 for a in alarm_records if not a.is_resolved),
        )

        # 2. 运行数据分析
        running_rows = FDDRepository.list_device_running_data_since(session, device_id, start_time)
        samples = [
            TelemetrySample(voltage=row[0], current=row[1], flow_rate=row[2])
            for row in running_rows
        ]
        running_stats = fdd_rules.compute_running_stats(samples, config)

        # 3. 健康分数 + 建议
        health = fdd_rules.calculate_health_score(alarm_stats, running_stats, config)
        suggestions = fdd_rules.generate_suggestions(health.deductions)

        return {
            "device_id": device_id,
            "device_name": device.name,
            "health_score": health.score,
            "suggestions": suggestions,
        }

    @staticmethod
    def get_fault_diagnosis_stats(
        session: Session,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> List[Dict[str, Any]]:
        """获取所有可访问设备的故障诊断统计。"""
        # 一次聚合查询，避免 N+1
        alarm_by_device = FDDRepository.count_unresolved_alarms_by_device(
            session,
            allowed_device_ids=allowed_device_ids,
        )
        devices = FDDRepository.list_devices(
            session,
            allowed_device_ids=allowed_device_ids,
        )

        results: List[Dict[str, Any]] = []
        for device in devices:
            alarm_count = alarm_by_device.get(device.id, 0)
            score, status = fdd_rules.classify_simple_health_status(alarm_count)
            results.append({
                "device_id": device.id,
                "device_name": device.name,
                "alarm_count": alarm_count,
                "health_score": score,
                "status": status,
            })
        return results
