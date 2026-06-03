"""Pure location hierarchy rules."""

from __future__ import annotations

from typing import Any, Callable, Iterable


def calculate_location_path_fields(name: str, parent: Any | None) -> dict[str, int | str]:
    """Calculate level and full_path for a location under an optional parent."""
    if parent:
        return {
            "level": int(getattr(parent, "level")) + 1,
            "full_path": f"{getattr(parent, 'full_path')}/{name}",
        }
    return {"level": 0, "full_path": f"/{name}"}


def resolve_location_reference_match(
    *,
    raw_value: str | None,
    by_full_path: Any | None,
    by_code: Any | None,
    by_name: Iterable[Any],
) -> Any | None:
    """Choose the matching location from service-provided lookup results."""
    normalized = raw_value.strip() if raw_value else ""
    if not normalized:
        return None
    if by_full_path:
        return by_full_path
    if by_code:
        return by_code

    name_matches = list(by_name)
    if len(name_matches) == 1:
        return name_matches[0]
    return None


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


def build_location_tree(
    roots: Iterable[Any],
    *,
    max_depth: int | None,
    get_device_count: Callable[[Any], int],
    get_child_locations: Callable[[Any], Iterable[Any]],
) -> list[dict[str, Any]]:
    """Build a nested location tree using service-provided query callbacks."""

    def build_node(location: Any, current_depth: int = 0) -> dict[str, Any]:
        node = build_location_tree_node(
            location,
            device_count=get_device_count(location),
        )

        if max_depth is None or current_depth < max_depth:
            for child in get_child_locations(location):
                node["children"].append(build_node(child, current_depth + 1))

        return node

    return [build_node(root) for root in roots]


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
