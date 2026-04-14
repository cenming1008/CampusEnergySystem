"""
设备监控 serializer。

目前只承载监控列表类响应的统一包装，避免 endpoint 内重复拼装。
"""

from __future__ import annotations

from typing import Any


def serialize_items_payload(items: Any) -> dict[str, Any]:
    """统一包装列表型监控响应。"""

    return {"items": items}


__all__ = ["serialize_items_payload"]
