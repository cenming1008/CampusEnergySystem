"""
报警管理服务层
封装报警相关的业务逻辑
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlmodel import Session, select

from app.models.tables import Alarm, Device
from app.core.logger import logger


class AlarmService:
    """
    报警管理服务类
    
    提供报警相关的业务逻辑，包括：
    - 获取未解决的报警列表
    - 批量解决报警
    - 报警统计和查询
    """
    
    @staticmethod
    def get_unresolved_alarms(session: Session, limit: int = 20) -> List[Alarm]:
        """
        获取未处理的报警列表
        
        Args:
            session: 数据库会话
            limit: 返回的最大记录数，默认20条
            
        Returns:
            未处理的报警列表，按时间倒序排列（最新的在前）
        """
        statement = (
            select(Alarm)
            .where(Alarm.is_resolved == False)
            .order_by(Alarm.timestamp.desc())
            .limit(limit)
        )
        alarms = session.exec(statement).all()
        return list(alarms)

    @staticmethod
    def list_alarms(
        session: Session,
        device_id: Optional[int] = None,
        resolved: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> List[Alarm]:
        statement = select(Alarm)
        if allowed_device_ids is not None:
            statement = statement.where(Alarm.device_id.in_(allowed_device_ids))
        if device_id is not None:
            statement = statement.where(Alarm.device_id == device_id)
        if resolved is not None:
            statement = statement.where(Alarm.is_resolved == resolved)
        if start_time is not None:
            statement = statement.where(Alarm.timestamp >= start_time)
        if end_time is not None:
            statement = statement.where(Alarm.timestamp <= end_time)
        statement = statement.order_by(Alarm.timestamp.desc()).limit(limit)
        return list(session.exec(statement).all())
    
    @staticmethod
    def resolve_all_alarms(
        session: Session,
        resolved_by: Optional[str] = None,
        handling_note: Optional[str] = None,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> int:
        """
        批量处理所有未处理的报警
        
        Args:
            session: 数据库会话
            
        Returns:
            处理的报警数量
        """
        statement = select(Alarm).where(Alarm.is_resolved == False)
        if allowed_device_ids is not None:
            if not allowed_device_ids:
                return 0
            statement = statement.where(Alarm.device_id.in_(allowed_device_ids))

        unresolved = session.exec(statement).all()
        
        if not unresolved:
            return 0
        
        count = 0
        for alarm in unresolved:
            alarm.is_resolved = True
            alarm.resolved_at = datetime.now()
            alarm.resolved_by = resolved_by
            if handling_note:
                alarm.handling_note = handling_note
            session.add(alarm)
            count += 1
        
        session.commit()
        
        logger.info(f"批量处理了 {count} 条报警")
        return count
    
    @staticmethod
    def resolve_alarm(
        session: Session,
        alarm_id: int,
        resolved_by: Optional[str] = None,
        handling_note: Optional[str] = None,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> bool:
        """
        处理单个报警
        
        Args:
            session: 数据库会话
            alarm_id: 报警ID
            
        Returns:
            是否成功处理，如果报警不存在、不可访问或已处理则返回False
        """
        alarm = session.get(Alarm, alarm_id)
        if not alarm or alarm.is_resolved:
            return False

        if allowed_device_ids is not None and alarm.device_id not in allowed_device_ids:
            return False
        
        alarm.is_resolved = True
        alarm.resolved_at = datetime.now()
        alarm.resolved_by = resolved_by
        if handling_note:
            alarm.handling_note = handling_note
        session.add(alarm)
        session.commit()
        
        logger.info(f"报警 {alarm_id} 已标记为已处理")
        return True
    
    @staticmethod
    def get_alarm_count(session: Session, device_id: int = None, resolved: bool = None) -> int:
        """
        获取报警数量统计
        
        Args:
            session: 数据库会话
            device_id: 设备ID，如果指定则只统计该设备的报警
            resolved: 是否已解决，None表示统计所有报警
            
        Returns:
            报警数量
        """
        statement = select(Alarm)
        
        if device_id is not None:
            statement = statement.where(Alarm.device_id == device_id)
        
        if resolved is not None:
            statement = statement.where(Alarm.is_resolved == resolved)
        
        alarms = session.exec(statement).all()
        return len(list(alarms))
    
    @staticmethod
    def create_alarm(
        session: Session,
        device_id: int,
        message: str,
        timestamp: datetime = None,
        severity: str = "warning",
        category: str = "threshold",
        source: str = "telemetry",
        instance_key: Optional[str] = None,
        last_seen_at: Optional[datetime] = None,
        recovered_at: Optional[datetime] = None,
        auto_commit: bool = True,
    ) -> Alarm:
        """
        创建新的报警记录
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            message: 报警消息
            timestamp: 报警时间，如果为None则使用当前时间
            
        Returns:
            创建的报警对象
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        alarm = Alarm(
            device_id=device_id,
            instance_key=instance_key,
            message=message,
            severity=severity,
            category=category,
            source=source,
            timestamp=timestamp,
            last_seen_at=last_seen_at or timestamp,
            recovered_at=recovered_at,
            is_resolved=False,
        )
        
        session.add(alarm)
        if auto_commit:
            session.commit()
        else:
            session.flush()
        session.refresh(alarm)
        
        logger.info(f"创建报警: 设备 {device_id} - {message}")
        return alarm

    @staticmethod
    def build_instance_key(device_id: int, category: str, source: str = "telemetry") -> str:
        """构造稳定告警实例键。"""
        return f"{device_id}:{source}:{category}"

    @staticmethod
    def get_active_alarm(
        session: Session,
        device_id: int,
        category: str,
        source: str = "telemetry",
    ) -> Optional[Alarm]:
        """获取同设备/类别/来源下仍处于活跃态的实例。"""
        return session.exec(
            select(Alarm)
            .where(Alarm.device_id == device_id)
            .where(Alarm.category == category)
            .where(Alarm.source == source)
            .where(Alarm.recovered_at == None)
            .order_by(Alarm.timestamp.desc())
        ).first()

    @staticmethod
    def upsert_active_alarm(
        session: Session,
        device_id: int,
        message: str,
        timestamp: datetime,
        severity: str,
        category: str,
        source: str = "telemetry",
    ) -> tuple[Alarm, bool]:
        """
        创建或刷新活跃实例。

        Returns:
            (alarm, created)
        """
        instance_key = AlarmService.build_instance_key(device_id, category, source)
        existing_alarm = AlarmService.get_active_alarm(
            session=session,
            device_id=device_id,
            category=category,
            source=source,
        )

        if existing_alarm is not None:
            existing_alarm.instance_key = existing_alarm.instance_key or instance_key
            existing_alarm.message = message
            existing_alarm.severity = severity
            existing_alarm.last_seen_at = timestamp
            session.add(existing_alarm)
            return existing_alarm, False

        alarm = AlarmService.create_alarm(
            session=session,
            device_id=device_id,
            message=message,
            timestamp=timestamp,
            severity=severity,
            category=category,
            source=source,
            instance_key=instance_key,
            last_seen_at=timestamp,
            auto_commit=False,
        )
        return alarm, True

    @staticmethod
    def mark_recovered_alarms(
        session: Session,
        device_id: int,
        active_instance_keys: set[str],
        timestamp: datetime,
        categories: set[str],
        source: str = "telemetry",
    ) -> int:
        """将本轮未再命中的活跃实例标记为系统已恢复。"""
        if not categories:
            return 0

        active_alarms = session.exec(
            select(Alarm)
            .where(Alarm.device_id == device_id)
            .where(Alarm.source == source)
            .where(Alarm.category.in_(categories))
            .where(Alarm.recovered_at == None)
        ).all()

        recovered_count = 0
        for alarm in active_alarms:
            expected_key = alarm.instance_key or AlarmService.build_instance_key(
                alarm.device_id,
                alarm.category,
                alarm.source,
            )
            if alarm.instance_key != expected_key:
                alarm.instance_key = expected_key
            if expected_key in active_instance_keys:
                continue
            alarm.recovered_at = timestamp
            session.add(alarm)
            recovered_count += 1
        return recovered_count

    @staticmethod
    def check_svg_faults(
        session: Session,
        device_id: int,
        svg_data: dict,
        timestamp: datetime,
    ) -> list:
        """
        检查 SVG 遥测数据中的故障位并触发/恢复告警。

        故障位为 True 时创建/刷新告警；为 False 时恢复告警。
        当前告警代码非空也视为故障。
        """
        # (字段名, category, severity, 消息模板)
        FAULT_RULES: list[tuple[str, str, str, str]] = [
            ("overvoltage_fault",  "svg_overvoltage",  "critical", "SVG 过压故障"),
            ("undervoltage_fault", "svg_undervoltage",  "critical", "SVG 欠压故障"),
            ("overcurrent_fault",  "svg_overcurrent",   "critical", "SVG 过流故障"),
            ("overtemp_fault",     "svg_overtemp",      "warning",  "SVG 过温告警"),
            ("module_fault",       "svg_module_fault",  "critical", "SVG 模块故障"),
            ("fan_fault",          "svg_fan_fault",     "warning",  "SVG 风机故障"),
            ("comm_fault",         "svg_comm_fault",    "warning",  "SVG 通信故障"),
        ]

        alarms: list = []
        active_instance_keys: set[str] = set()
        managed_categories: set[str] = {rule[1] for rule in FAULT_RULES} | {"svg_fault_code"}

        for field, category, severity, base_msg in FAULT_RULES:
            value = svg_data.get(field)
            if value is True:
                alarm, created = AlarmService.upsert_active_alarm(
                    session=session,
                    device_id=device_id,
                    message=base_msg,
                    timestamp=timestamp,
                    severity=severity,
                    category=category,
                    source="svg_telemetry",
                )
                active_instance_keys.add(alarm.instance_key or "")
                if created:
                    alarms.append(alarm)
                    logger.warning(f"SVG 设备 {device_id} {base_msg}")

        # 当前故障代码非空视为有效故障
        fault_code = svg_data.get("current_fault_code")
        if fault_code:
            msg = f"SVG 故障代码: {fault_code}"
            alarm, created = AlarmService.upsert_active_alarm(
                session=session,
                device_id=device_id,
                message=msg,
                timestamp=timestamp,
                severity="critical",
                category="svg_fault_code",
                source="svg_telemetry",
            )
            active_instance_keys.add(alarm.instance_key or "")
            if created:
                alarms.append(alarm)

        AlarmService.mark_recovered_alarms(
            session=session,
            device_id=device_id,
            active_instance_keys={k for k in active_instance_keys if k},
            timestamp=timestamp,
            categories=managed_categories,
            source="svg_telemetry",
        )

        return alarms

    @staticmethod
    def check_capacitor_bank_faults(
        session: Session,
        device_id: int,
        cap_data: dict[str, Any],
        timestamp: datetime,
        profile_data: Optional[dict[str, Any]] = None,
    ) -> list[Alarm]:
        """
        检查电容补偿控制器专属状态位/阈值并触发或恢复告警。

        当前覆盖：
        - 温度超限
        - 各相过压
        - 各相电压谐波超限
        - 各相电流谐波超限
        - 各相欠流
        - 过补偿（Q 持续为负且至少两相超前）
        """
        alarms: list[Alarm] = []
        active_instance_keys: set[str] = set()
        mutated = False
        source = "capacitor_bank_telemetry"
        profile_data = profile_data or {}

        def _to_float(value: Any) -> Optional[float]:
            if value is None:
                return None
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        def _activate(category: str, severity: str, message: str) -> None:
            nonlocal mutated
            alarm, created = AlarmService.upsert_active_alarm(
                session=session,
                device_id=device_id,
                message=message,
                timestamp=timestamp,
                severity=severity,
                category=category,
                source=source,
            )
            active_instance_keys.add(alarm.instance_key or "")
            mutated = True
            if created:
                alarms.append(alarm)

        managed_categories: set[str] = {
            "cap_temp_alarm",
            "cap_overcompensation",
            *(f"cap_overvoltage_{phase}" for phase in ("a", "b", "c")),
            *(f"cap_voltage_thd_{phase}" for phase in ("a", "b", "c")),
            *(f"cap_current_thd_{phase}" for phase in ("a", "b", "c")),
            *(f"cap_undercurrent_{phase}" for phase in ("a", "b", "c")),
        }

        temperature = _to_float(cap_data.get("temperature"))
        temp_limit = _to_float(profile_data.get("temperature_upper_limit"))
        if cap_data.get("temp_alarm") is True or (
            temperature is not None and temp_limit is not None and temperature >= temp_limit
        ):
            detail = f"{temperature:.1f}°C" if temperature is not None else "状态位触发"
            limit_text = f"（上限 {temp_limit:.1f}°C）" if temp_limit is not None else ""
            _activate("cap_temp_alarm", "warning", f"电容补偿柜温度超限：{detail}{limit_text}")

        overvoltage_limit = _to_float(profile_data.get("overvoltage_threshold"))
        voltage_harmonic_limit = _to_float(profile_data.get("voltage_harmonic_threshold"))
        current_harmonic_limit = _to_float(profile_data.get("current_harmonic_threshold"))
        for phase in ("a", "b", "c"):
            phase_upper = phase.upper()
            phase_voltage = _to_float(cap_data.get(f"voltage_{phase}"))
            if cap_data.get(f"overvoltage_alarm_{phase}") is True or (
                phase_voltage is not None and overvoltage_limit is not None and phase_voltage >= overvoltage_limit
            ):
                detail = f"{phase_voltage:.1f}V" if phase_voltage is not None else "状态位触发"
                limit_text = f"（门限 {overvoltage_limit:.1f}V）" if overvoltage_limit is not None else ""
                _activate(
                    f"cap_overvoltage_{phase}",
                    "warning",
                    f"{phase_upper} 相过压告警：{detail}{limit_text}",
                )

            phase_voltage_thd = _to_float(cap_data.get(f"voltage_thd_{phase}"))
            if cap_data.get(f"voltage_thd_alarm_{phase}") is True or (
                phase_voltage_thd is not None
                and voltage_harmonic_limit is not None
                and phase_voltage_thd >= voltage_harmonic_limit
            ):
                detail = f"{phase_voltage_thd:.2f}%" if phase_voltage_thd is not None else "状态位触发"
                limit_text = f"（门限 {voltage_harmonic_limit:.2f}%）" if voltage_harmonic_limit is not None else ""
                _activate(
                    f"cap_voltage_thd_{phase}",
                    "warning",
                    f"{phase_upper} 相电压谐波超限：{detail}{limit_text}",
                )

            phase_current_harmonic = _to_float(cap_data.get(f"current_harmonic_{phase}"))
            if cap_data.get(f"current_thd_alarm_{phase}") is True or (
                phase_current_harmonic is not None
                and current_harmonic_limit is not None
                and phase_current_harmonic >= current_harmonic_limit
            ):
                detail = f"{phase_current_harmonic:.2f}A" if phase_current_harmonic is not None else "状态位触发"
                limit_text = f"（门限 {current_harmonic_limit:.2f}A）" if current_harmonic_limit is not None else ""
                _activate(
                    f"cap_current_thd_{phase}",
                    "warning",
                    f"{phase_upper} 相电流谐波超限：{detail}{limit_text}",
                )

            if cap_data.get(f"undercurrent_{phase}") is True:
                _activate(
                    f"cap_undercurrent_{phase}",
                    "info",
                    f"{phase_upper} 相欠流告警",
                )

        reactive_power = _to_float(cap_data.get("reactive_power"))
        leading_count = sum(
            1
            for field in ("leading_a", "leading_b", "leading_c")
            if cap_data.get(field) is True
        )
        rated_capacity = session.exec(
            select(Device.rated_capacity).where(Device.id == device_id)
        ).first()
        overcomp_limit = max(5.0, float(rated_capacity or 0) * 0.1)
        if reactive_power is not None and reactive_power <= -overcomp_limit and leading_count >= 2:
            _activate(
                "cap_overcompensation",
                "warning",
                f"电容补偿器过补偿：Q={reactive_power:.2f}kVar，{leading_count} 相超前",
            )

        recovered_count = AlarmService.mark_recovered_alarms(
            session=session,
            device_id=device_id,
            active_instance_keys={key for key in active_instance_keys if key},
            timestamp=timestamp,
            categories=managed_categories,
            source=source,
        )
        if recovered_count:
            mutated = True

        return alarms

    @staticmethod
    def infer_severity(message: str) -> str:
        if any(keyword in message for keyword in ("故障", "中断", "离线")):
            return "critical"
        if any(keyword in message for keyword in ("过载", "异常", "超限", "偏高", "偏低")):
            return "warning"
        return "info"

    @staticmethod
    def load_thresholds() -> Dict:
        """
        加载报警阈值配置
        从 config/settings.json 读取
        """
        from app.core.settings import settings
        
        path = settings.settings_json_path or os.path.join(
            settings.config_dir, "settings.json"
        )
        
        try:
            if not os.path.exists(path):
                logger.warning(f"阈值配置文件不存在: {path}")
                return {}
            
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"阈值配置文件读取失败: {e}")
            return {}
    
    @staticmethod
    def check_and_create_alarm(
        session: Session,
        device_id: int,
        data: dict,
        timestamp: datetime
    ) -> list:
        """
        检查数据并创建报警
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            data: 数据字典
            timestamp: 时间戳
            
        Returns:
            创建的报警列表
        """
        alarms = []
        active_instance_keys: set[str] = set()
        managed_categories: set[str] = set()
        mutated = False
        cfg = AlarmService.load_thresholds()
        defaults = cfg.get("default", {})
        dev_cfg = cfg.get("device_thresholds", {}).get(str(device_id), {})
        
        # 电流过载检测
        if "current" in data and data["current"] is not None:
            current = float(data["current"])
            limit = dev_cfg.get("current_max", defaults.get("current_max", 45.0))
            managed_categories.add("current_overload")
            
            if current > limit:
                message = f"⚠️ 过载报警! 当前: {current}A (上限: {limit}A)"
                alarm, created = AlarmService.upsert_active_alarm(
                    session=session,
                    device_id=device_id,
                    message=message,
                    timestamp=timestamp,
                    severity="critical",
                    category="current_overload",
                )
                active_instance_keys.add(alarm.instance_key or "")
                mutated = True
                if created:
                    alarms.append(alarm)
                logger.warning(f"设备 {device_id} 电流过载: {current}A > {limit}A")
        
        # 电压异常检测
        if "voltage" in data and data["voltage"] is not None:
            voltage = float(data["voltage"])
            # 支持设备个性化电压配置，优先使用设备配置，否则使用默认值
            v_max = dev_cfg.get("voltage_max", defaults.get("voltage_max", 250.0))
            v_min = dev_cfg.get("voltage_min", defaults.get("voltage_min", 190.0))
            managed_categories.add("voltage_out_of_range")
            
            if voltage > v_max or voltage < v_min:
                message = f"⚡ 电压异常! 读数: {voltage}V (范围: {v_min}-{v_max}V)"
                alarm, created = AlarmService.upsert_active_alarm(
                    session=session,
                    device_id=device_id,
                    message=message,
                    timestamp=timestamp,
                    severity="warning",
                    category="voltage_out_of_range",
                )
                active_instance_keys.add(alarm.instance_key or "")
                mutated = True
                if created:
                    alarms.append(alarm)
                logger.warning(f"设备 {device_id} 电压异常: {voltage}V")

        recovered_count = AlarmService.mark_recovered_alarms(
            session=session,
            device_id=device_id,
            active_instance_keys={key for key in active_instance_keys if key},
            timestamp=timestamp,
            categories=managed_categories,
        )
        if recovered_count:
            mutated = True
            logger.info(f"设备 {device_id} 有 {recovered_count} 条告警实例已恢复")

        if mutated:
            session.commit()
            for alarm in alarms:
                session.refresh(alarm)
        
        return alarms
