"""
报警管理服务层（编排层）

职责：调用 domain 层的纯业务规则，调用 repository 层的数据访问，
然后处理副作用（日志、commit）。

业务规则下沉到 app/domain/alarm_rules.py。
数据查询下沉到 app/repositories/alarm_repository.py。
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from sqlmodel import Session

from app.core.logger import logger
from app.domain import alarm_rules
from app.domain.alarm_rules import (
    ActiveAlarmState,
    AlarmCreateFields,
    FaultDetection,
)
from app.domain.alarm_rule_profiles import (
    DeviceRuleIdentity,
    resolve_capacitor_bank_profile,
    resolve_generic_threshold_profile,
    resolve_media_threshold_profile,
    resolve_storage_threshold_profile,
)
from app.models.tables import Alarm
from app.repositories.alarm_repository import AlarmRepository


class AlarmService:
    """
    报警管理服务类（编排层）

    每个公开方法的执行模式：
    1. 调 domain 函数获得业务决策
    2. 调 repository 完成持久化
    3. 处理副作用（日志、commit）
    """

    # 常量保留以保持向后兼容
    SOURCE_DEVICE_NATIVE = alarm_rules.SOURCE_DEVICE_NATIVE
    SOURCE_PLATFORM_RULE = alarm_rules.SOURCE_PLATFORM_RULE
    SOURCE_PLATFORM_COMM = alarm_rules.SOURCE_PLATFORM_COMM
    CATEGORY_COMMUNICATION_OFFLINE = "communication_offline"

    # ==================== 查询接口（仓储 pass-through） ====================

    @staticmethod
    def get_unresolved_alarms(session: Session, limit: int = 20) -> List[Alarm]:
        """获取未处理的报警列表，按时间倒序。"""
        return AlarmRepository.get_unresolved_alarms(session, limit=limit)

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
        """按条件查询告警列表。"""
        return AlarmRepository.list_alarms(
            session,
            device_id=device_id,
            resolved=resolved,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            allowed_device_ids=allowed_device_ids,
        )

    @staticmethod
    def get_alarm_count(
        session: Session,
        device_id: int = None,
        resolved: bool = None,
    ) -> int:
        """统计告警数量。"""
        return AlarmRepository.count_alarms(
            session,
            device_id=device_id,
            resolved=resolved,
        )

    @staticmethod
    def get_active_alarm_count(session: Session, device_id: int = None) -> int:
        """统计当前仍在触发中的告警数量。"""
        return AlarmRepository.count_active_alarms(session, device_id)

    @staticmethod
    def get_unresolved_category_counts(session: Session, device_id: int) -> dict[str, int]:
        """按类别统计设备未处理告警数量。"""
        return AlarmRepository.count_unresolved_by_category(session, device_id)

    @staticmethod
    def get_category_counts(session: Session, device_id: int) -> dict[str, int]:
        """按类别统计设备累计告警数量。"""
        return AlarmRepository.count_by_category(session, device_id)

    # ==================== 编排：人工处理 ====================

    @staticmethod
    def resolve_alarm(
        session: Session,
        alarm_id: int,
        resolved_by: Optional[str] = None,
        handling_note: Optional[str] = None,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> bool:
        """处理单个报警。返回是否成功。"""
        alarm = AlarmRepository.get_alarm_by_id(session, alarm_id)
        if not alarm or alarm.is_resolved:
            return False
        if allowed_device_ids is not None and alarm.device_id not in allowed_device_ids:
            return False

        transition = alarm_rules.compute_resolve_transition(
            resolved_by=resolved_by,
            handling_note=handling_note,
            timestamp=datetime.now(),
        )
        AlarmRepository.resolve_alarm(session, alarm, transition)
        session.commit()

        logger.info(f"报警 {alarm_id} 已标记为已处理")
        return True

    @staticmethod
    def resolve_all_alarms(
        session: Session,
        resolved_by: Optional[str] = None,
        handling_note: Optional[str] = None,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> int:
        """批量处理可访问范围内的所有未处理报警。"""
        if allowed_device_ids is not None and not allowed_device_ids:
            return 0

        unresolved = AlarmRepository.get_unresolved_alarms(
            session,
            limit=10_000,
            allowed_device_ids=allowed_device_ids,
        )
        if not unresolved:
            return 0

        timestamp = datetime.now()
        count = 0
        for alarm in unresolved:
            transition = alarm_rules.compute_resolve_transition(
                resolved_by=resolved_by,
                handling_note=handling_note,
                timestamp=timestamp,
            )
            AlarmRepository.resolve_alarm(session, alarm, transition)
            count += 1

        session.commit()
        logger.info(f"批量处理了 {count} 条报警")
        return count

    # ==================== 编排：故障检测 ====================

    @staticmethod
    def check_svg_faults(
        session: Session,
        device_id: int,
        svg_data: dict,
        timestamp: datetime,
    ) -> list:
        """检查 SVG 遥测数据中的故障位并触发/恢复告警。"""
        faults = alarm_rules.evaluate_svg_faults(svg_data)
        managed_categories = alarm_rules.get_svg_managed_categories()

        return AlarmService._apply_fault_detection(
            session=session,
            device_id=device_id,
            faults=faults,
            timestamp=timestamp,
            managed_categories=managed_categories,
            sources={alarm_rules.SOURCE_DEVICE_NATIVE},
            log_prefix=f"SVG 设备 {device_id}",
        )

    @staticmethod
    def check_capacitor_bank_faults(
        session: Session,
        device_id: int,
        cap_data: dict[str, Any],
        timestamp: datetime,
        profile_data: Optional[dict[str, Any]] = None,
    ) -> list[Alarm]:
        """检查电容补偿控制器专属状态位/阈值并触发或恢复告警。"""
        profile_data = profile_data or {}

        device_category, device_subtype = AlarmRepository.get_device_rule_identity(session, device_id)
        rule_profile = resolve_capacitor_bank_profile(
            AlarmService.load_thresholds(),
            DeviceRuleIdentity(
                device_id=device_id,
                device_category=device_category,
                device_subtype=device_subtype,
            ),
            profile_data,
        )
        rated_capacity = float(
            AlarmRepository.get_device_rated_capacity(session, device_id) or 0
        )

        faults = alarm_rules.evaluate_capacitor_bank_faults(
            cap_data=cap_data,
            thresholds=rule_profile.thresholds,
            rated_capacity=rated_capacity,
            platform_rules_enabled=rule_profile.platform_rules_enabled,
        )
        managed_categories = alarm_rules.get_capacitor_bank_managed_categories()

        return AlarmService._apply_fault_detection(
            session=session,
            device_id=device_id,
            faults=faults,
            timestamp=timestamp,
            managed_categories=managed_categories,
            sources={alarm_rules.SOURCE_DEVICE_NATIVE, alarm_rules.SOURCE_PLATFORM_RULE},
            log_prefix=None,
        )

    @staticmethod
    def check_storage_faults(
        session: Session,
        device_id: int,
        storage_data: dict[str, Any],
        timestamp: datetime,
    ) -> list[Alarm]:
        """检查储能平台规则并触发或恢复告警。"""
        device_category, device_subtype = AlarmRepository.get_device_rule_identity(session, device_id)
        rule_profile = resolve_storage_threshold_profile(
            AlarmService.load_thresholds(),
            DeviceRuleIdentity(
                device_id=device_id,
                device_category=device_category,
                device_subtype=device_subtype,
            ),
        )
        if not rule_profile.enabled:
            return []

        faults = alarm_rules.evaluate_storage_threshold_faults(
            storage_data,
            rule_profile.thresholds,
        )
        managed_categories = alarm_rules.get_storage_managed_categories(storage_data)

        return AlarmService._apply_fault_detection(
            session=session,
            device_id=device_id,
            faults=faults,
            timestamp=timestamp,
            managed_categories=managed_categories,
            sources={alarm_rules.SOURCE_PLATFORM_RULE},
            log_prefix=None,
        )

    @staticmethod
    def check_and_create_alarm(
        session: Session,
        device_id: int,
        data: dict,
        timestamp: datetime,
    ) -> list:
        """检查通用阈值数据（电压/电流）并创建/恢复告警。"""
        device_category, device_subtype = AlarmRepository.get_device_rule_identity(session, device_id)
        if device_category == "compensation":
            return []

        raw_rules = AlarmService.load_thresholds()
        identity = DeviceRuleIdentity(
            device_id=device_id,
            device_category=device_category,
            device_subtype=device_subtype,
        )
        rule_profile = resolve_generic_threshold_profile(raw_rules, identity)

        faults: list[FaultDetection] = []
        if rule_profile.enabled:
            faults.extend(alarm_rules.evaluate_threshold_faults(data, rule_profile.thresholds, device_category))

        media_profile = resolve_media_threshold_profile(raw_rules, identity)
        if media_profile.enabled:
            faults.extend(alarm_rules.evaluate_media_threshold_faults(data, media_profile.thresholds))

        # 仅对本次检测的字段做 recover 管理（保持原行为）
        managed_categories = alarm_rules.get_threshold_managed_categories(data)

        new_alarms = AlarmService._apply_fault_detection(
            session=session,
            device_id=device_id,
            faults=faults,
            timestamp=timestamp,
            managed_categories=managed_categories,
            sources={alarm_rules.SOURCE_PLATFORM_RULE},
            log_prefix=f"设备 {device_id}",
        )

        # 把检测中的告警值写入日志（与原实现一致）
        for fault in faults:
            if fault.category == "current_overload":
                logger.warning(
                    f"设备 {device_id} 电流过载: {data.get('current')}A > {rule_profile.thresholds.current_max}A"
                )
            elif fault.category == "voltage_out_of_range":
                logger.warning(f"设备 {device_id} 电压异常: {data.get('voltage')}V")

        return new_alarms

    # ==================== 编排：通讯告警 ====================

    @staticmethod
    def sync_platform_comm_alarm(
        session: Session,
        device_id: int,
        is_offline: bool,
        timestamp: datetime,
        last_success_at: Optional[datetime] = None,
    ) -> Union[tuple[Alarm, bool], int]:
        """创建或恢复平台通讯中断告警。"""
        category = AlarmService.CATEGORY_COMMUNICATION_OFFLINE
        source = AlarmService.SOURCE_PLATFORM_COMM

        if is_offline:
            detail = (
                f"最近成功接入时间 {last_success_at:%Y-%m-%d %H:%M:%S}"
                if last_success_at is not None
                else "暂无成功接入记录"
            )
            return AlarmService.upsert_active_alarm(
                session=session,
                device_id=device_id,
                message=f"设备通讯中断：{detail}",
                timestamp=timestamp,
                severity="critical",
                category=category,
                source=source,
            )

        recovered_count = AlarmService.mark_recovered_alarms(
            session=session,
            device_id=device_id,
            active_instance_keys=set(),
            timestamp=timestamp,
            categories={category},
            source=source,
        )
        if recovered_count:
            session.flush()
        return recovered_count

    # ==================== 兼容接口（编排层细粒度方法） ====================

    @staticmethod
    def build_instance_key(device_id: int, category: str, source: str = "telemetry") -> str:
        """构造稳定告警实例键。"""
        return alarm_rules.build_instance_key(device_id, category, source)

    @staticmethod
    def infer_severity(message: str) -> str:
        """根据消息内容推断告警级别。"""
        return alarm_rules.infer_severity(message)

    @staticmethod
    def get_active_alarm(
        session: Session,
        device_id: int,
        category: str,
        source: str = "telemetry",
    ) -> Optional[Alarm]:
        """获取同设备/类别/来源下仍处于活跃态的实例。"""
        return AlarmRepository.get_active_alarm(session, device_id, category, source)

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
        """创建新的报警记录（保留以兼容旧调用方）。"""
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
    def upsert_active_alarm(
        session: Session,
        device_id: int,
        message: str,
        timestamp: datetime,
        severity: str,
        category: str,
        source: str = "telemetry",
    ) -> tuple[Alarm, bool]:
        """创建或刷新活跃实例。返回 (alarm, created)。"""
        instance_key = alarm_rules.build_instance_key(device_id, category, source)
        existing = AlarmRepository.get_active_alarm(session, device_id, category, source)

        if existing is not None:
            existing.instance_key = existing.instance_key or instance_key
            existing.message = message
            existing.severity = severity
            existing.last_seen_at = timestamp
            session.add(existing)
            return existing, False

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

        active_alarms = AlarmRepository.get_active_alarms_by_device(
            session, device_id, source, categories,
        )
        recovered_count = 0
        for alarm in active_alarms:
            expected_key = alarm.instance_key or alarm_rules.build_instance_key(
                alarm.device_id, alarm.category, alarm.source,
            )
            if alarm.instance_key != expected_key:
                alarm.instance_key = expected_key
            if expected_key in active_instance_keys:
                continue
            alarm.recovered_at = timestamp
            session.add(alarm)
            recovered_count += 1
        return recovered_count

    # ==================== 阈值配置加载 ====================

    @staticmethod
    def load_thresholds() -> Dict:
        """从 config/settings.json 加载报警阈值配置。"""
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

    # ==================== 内部编排辅助 ====================

    @staticmethod
    def _apply_fault_detection(
        session: Session,
        device_id: int,
        faults: List[FaultDetection],
        timestamp: datetime,
        managed_categories: set[str],
        sources: set[str],
        log_prefix: Optional[str],
    ) -> List[Alarm]:
        """
        将故障检测结果应用到数据库：创建新告警、刷新已有告警、恢复未命中的告警。

        返回本次新建的告警列表。
        """
        new_alarms: List[Alarm] = []
        any_mutation = False

        # 1. 处理 create / refresh
        active_keys_by_source: dict[str, set[str]] = {src: set() for src in sources}
        for fault in faults:
            existing = AlarmRepository.get_active_alarm(
                session, device_id, fault.category, fault.source,
            )
            instance_key = alarm_rules.build_instance_key(
                device_id, fault.category, fault.source,
            )
            active_keys_by_source.setdefault(fault.source, set()).add(instance_key)

            if existing is not None:
                # 刷新
                existing.instance_key = existing.instance_key or instance_key
                existing.message = fault.message
                existing.severity = fault.severity
                existing.last_seen_at = timestamp
                session.add(existing)
                any_mutation = True
            else:
                # 创建
                fields = AlarmCreateFields(
                    device_id=device_id,
                    instance_key=instance_key,
                    message=fault.message,
                    severity=fault.severity,
                    category=fault.category,
                    source=fault.source,
                    timestamp=timestamp,
                    last_seen_at=timestamp,
                )
                alarm = AlarmRepository.create_alarm(session, fields, commit=False)
                new_alarms.append(alarm)
                any_mutation = True
                if log_prefix:
                    logger.warning(f"{log_prefix} {fault.message}")

        # 2. 处理 recover：每个 source 单独处理
        for source in sources:
            active_keys = active_keys_by_source.get(source, set())
            recovered = AlarmService.mark_recovered_alarms(
                session=session,
                device_id=device_id,
                active_instance_keys=active_keys,
                timestamp=timestamp,
                categories=managed_categories,
                source=source,
            )
            if recovered:
                any_mutation = True
                if log_prefix:
                    logger.info(f"{log_prefix} 有 {recovered} 条告警实例已恢复")

        if any_mutation:
            session.commit()
            for alarm in new_alarms:
                session.refresh(alarm)

        return new_alarms
