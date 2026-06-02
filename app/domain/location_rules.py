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


def build_location_statistics_payload(
    location: Any,
    devices: list[Any],
    child_locations: list[Any],
) -> dict[str, Any]:
    """Build the public statistics payload for one location."""
    device_count_by_energy: dict[Any, int] = {}
    for device in devices:
        energy_type = getattr(device, "energy_type")
        device_count_by_energy[energy_type] = device_count_by_energy.get(energy_type, 0) + 1

    device_count_by_category: dict[Any, int] = {}
    for device in devices:
        category = getattr(device, "device_category")
        device_count_by_category[category] = device_count_by_category.get(category, 0) + 1

    return {
        "location": {
            "id": getattr(location, "id"),
            "name": getattr(location, "name"),
            "type": getattr(location, "location_type"),
            "full_path": getattr(location, "full_path"),
            "level": getattr(location, "level"),
        },
        "device_count": {
            "total": len(devices),
            "active": sum(1 for device in devices if getattr(device, "is_active")),
            "by_energy_type": device_count_by_energy,
            "by_category": device_count_by_category,
        },
        "child_locations_count": len(child_locations),
        "area_sqm": getattr(location, "area_sqm"),
        "manager": getattr(location, "manager"),
    }
