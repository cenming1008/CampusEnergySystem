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
