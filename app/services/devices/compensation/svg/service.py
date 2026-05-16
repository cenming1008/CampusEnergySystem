"""
SVG 业务服务

统一管理补偿类设备中 SVG 子类型的运维档案（人工维护）与其兼容写入逻辑。
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from sqlmodel import Session, select

from app.models.tables import SVGAssetProfile, SVGTelemetry


SVG_PROFILE_DATE_FIELDS = {"install_date", "commission_date", "warranty_expiry"}


class SVGService:
    """SVG 统一运维档案服务。"""

    @staticmethod
    def _sample_history_records(records: list, limit: int):
        if len(records) <= limit or limit < 3:
            return records

        sampled = [records[0]]
        interior_target = limit - 2
        last_index = len(records) - 1

        for index in range(1, interior_target + 1):
            point_index = round((index * last_index) / (interior_target + 1))
            point = records[min(last_index - 1, max(1, point_index))]
            if sampled[-1] is not point:
                sampled.append(point)

        if sampled[-1] is not records[last_index]:
            sampled.append(records[last_index])

        return sampled

    @staticmethod
    def get_control_capabilities() -> dict[str, bool]:
        """返回 SVG 当前开放能力。

        当前 SVG 子型在平台内仅开放监视与运维档案维护，不开放协议写控制或远程控制。
        这里的 `supports_write=False` 属于明确业务边界，而不是遗漏实现；若后续接入
        真实 SVG 控制协议，应统一从这里收口能力开关，而不是在监控聚合层零散改布尔值。
        """
        return {
            "supports_read": True,
            "supports_write": False,
            "supports_remote_control": False,
        }

    @staticmethod
    def get_operations_profile(session: Session, device_id: int) -> Optional[SVGAssetProfile]:
        return session.exec(
            select(SVGAssetProfile).where(SVGAssetProfile.device_id == device_id)
        ).first()

    @staticmethod
    def get_latest_telemetry(session: Session, device_id: int) -> Optional[SVGTelemetry]:
        return session.exec(
            select(SVGTelemetry)
            .where(SVGTelemetry.device_id == device_id)
            .order_by(SVGTelemetry.timestamp.desc())
            .limit(1)
        ).first()

    @staticmethod
    def list_telemetry_history(
        session: Session,
        device_id: int,
        *,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 200,
    ) -> list[SVGTelemetry]:
        stmt = select(SVGTelemetry).where(SVGTelemetry.device_id == device_id)
        if start_time:
            stmt = stmt.where(SVGTelemetry.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(SVGTelemetry.timestamp <= end_time)
        records = list(session.exec(stmt.order_by(SVGTelemetry.timestamp.asc())).all())
        return SVGService._sample_history_records(records, limit)

    @staticmethod
    def upsert_operations_profile(
        session: Session,
        device_id: int,
        payload: dict[str, Any],
    ) -> SVGAssetProfile:
        profile = SVGService.get_operations_profile(session, device_id)
        if profile is None:
            profile = SVGAssetProfile(device_id=device_id)

        for field, value in payload.items():
            if value is None or not hasattr(profile, field):
                continue
            if field in SVG_PROFILE_DATE_FIELDS and isinstance(value, str):
                value = date.fromisoformat(value)
            setattr(profile, field, value)

        profile.updated_at = datetime.now()
        session.add(profile)
        session.commit()
        session.refresh(profile)
        return profile
