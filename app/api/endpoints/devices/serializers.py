"""
设备域通用 serializer。

只放跨设备子模块复用的轻量转换函数，不放业务判断。
"""

from __future__ import annotations

from app.models.tables import SVGAssetProfile

from .compensation_schemas import SVGOperationsProfileResponse


def serialize_svg_operations_profile(profile: SVGAssetProfile) -> dict:
    """将 SVG 运维档案中的日期字段序列化为 ISO 字符串。"""
    data = {}
    date_fields = {"install_date", "commission_date", "warranty_expiry"}
    for field in SVGOperationsProfileResponse.model_fields:
        value = getattr(profile, field, None)
        if field in date_fields and value is not None:
            value = value.isoformat()
        data[field] = value
    return data


__all__ = ["serialize_svg_operations_profile"]
