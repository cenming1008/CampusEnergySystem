"""Pure location hierarchy rules."""

from __future__ import annotations

from typing import Any


def calculate_location_path_fields(name: str, parent: Any | None) -> dict[str, int | str]:
    """Calculate level and full_path for a location under an optional parent."""
    if parent:
        return {
            "level": int(getattr(parent, "level")) + 1,
            "full_path": f"{getattr(parent, 'full_path')}/{name}",
        }
    return {"level": 0, "full_path": f"/{name}"}


def build_location_tree_node(location: Any, device_count: int) -> dict[str, Any]:
    """Build the public tree payload for one location node."""
    return {
        "id": getattr(location, "id"),
        "name": getattr(location, "name"),
        "type": getattr(location, "location_type"),
        "code": getattr(location, "code"),
        "full_path": getattr(location, "full_path"),
        "level": getattr(location, "level"),
        "device_count": device_count,
        "area_sqm": getattr(location, "area_sqm"),
        "manager": getattr(location, "manager"),
        "children": [],
    }
