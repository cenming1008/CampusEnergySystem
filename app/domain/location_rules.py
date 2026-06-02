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
