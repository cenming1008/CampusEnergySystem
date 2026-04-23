"""
SVG 业务服务

统一管理补偿类设备中 SVG 子类型的运维档案（人工维护）与其兼容写入逻辑。
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from sqlmodel import Session, select

from app.models.tables import SVGAssetProfile


SVG_PROFILE_DATE_FIELDS = {"install_date", "commission_date", "warranty_expiry"}


class SVGService:
    """SVG 统一运维档案服务。"""

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
