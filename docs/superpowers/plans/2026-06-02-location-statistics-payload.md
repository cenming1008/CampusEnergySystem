# Location Statistics Payload Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move location statistics payload and device-count aggregation out of `LocationService` into `app/domain/location_rules.py` without changing API responses.

**Architecture:** `LocationService.get_location_statistics` remains responsible for loading the location, devices, and child locations. The domain helper receives row-like objects and builds the stable response dictionary. This slice does not move recursive device lookup or database access.

**Tech Stack:** Python, pytest/unittest, existing SQLModel service layer.

---

### Task 1: RED Domain Test

**Files:**
- Modify: `tests/test_location_domain.py`

- [ ] **Step 1: Write the failing test**

Update `tests/test_location_domain.py`:

```python
from app.domain.location_rules import (
    build_location_statistics_payload,
    build_location_tree_node,
    calculate_location_path_fields,
)


def test_build_location_statistics_payload_counts_devices_and_children():
    location = SimpleNamespace(
        id=3,
        name="北区",
        location_type="area",
        full_path="/园区/北区",
        level=1,
        area_sqm=3000.0,
        manager="alice",
    )
    devices = [
        SimpleNamespace(energy_type="electricity", device_category="load", is_active=True),
        SimpleNamespace(energy_type="electricity", device_category="load", is_active=False),
        SimpleNamespace(energy_type="water", device_category="water_meter", is_active=True),
        SimpleNamespace(energy_type=None, device_category=None, is_active=True),
    ]
    child_locations = [SimpleNamespace(id=10), SimpleNamespace(id=11)]

    payload = build_location_statistics_payload(location, devices, child_locations)

    assert payload == {
        "location": {
            "id": 3,
            "name": "北区",
            "type": "area",
            "full_path": "/园区/北区",
            "level": 1,
        },
        "device_count": {
            "total": 4,
            "active": 3,
            "by_energy_type": {"electricity": 2, "water": 1, None: 1},
            "by_category": {"load": 2, "water_meter": 1, None: 1},
        },
        "child_locations_count": 2,
        "area_sqm": 3000.0,
        "manager": "alice",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./venv/bin/python -m pytest tests/test_location_domain.py::test_build_location_statistics_payload_counts_devices_and_children -q`

Expected: FAIL with `ImportError` because `build_location_statistics_payload` is not exported by `app.domain.location_rules`.

- [ ] **Step 3: Commit RED test**

Run:

```bash
git add tests/test_location_domain.py
git commit -m "test: capture location statistics payload"
```

### Task 2: GREEN Domain Helper and Service Delegation

**Files:**
- Modify: `app/domain/location_rules.py`
- Modify: `app/services/location_service.py`

- [ ] **Step 1: Add pure domain helper**

Add this function to `app/domain/location_rules.py`:

```python
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
```

- [ ] **Step 2: Delegate statistics payload construction**

In `app/services/location_service.py`, import `build_location_statistics_payload` from `app.domain.location_rules`.

Inside `get_location_statistics`, remove the inline energy/category counting and return dictionary, then return:

```python
return build_location_statistics_payload(location, devices, child_locations)
```

Leave `get_location_by_id`, `get_devices_by_location`, and `get_child_locations` calls unchanged.

- [ ] **Step 3: Run tests to verify GREEN**

Run: `./venv/bin/python -m pytest tests/test_location_domain.py::test_build_location_statistics_payload_counts_devices_and_children -q`

Expected: PASS.

- [ ] **Step 4: Run location regression tests**

Run: `./venv/bin/python -m pytest tests/test_location_domain.py tests/test_location_application_use_cases.py tests/test_endpoint_application_convergence.py -q`

Expected: PASS.

- [ ] **Step 5: Commit implementation**

Run:

```bash
git add app/domain/location_rules.py app/services/location_service.py tests/test_location_domain.py
git commit -m "refactor: move location statistics payload to domain"
```

### Task 3: Documentation Sync

**Files:**
- Modify: `docs/plans/backend-architecture-audit-inventory.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Record the completed slice**

Update docs to record that location statistics payload moved to `domain/location_rules.py`, while device/child queries remain in `LocationService`.

- [ ] **Step 2: Update status and handoff**

Record test evidence and note that `LocationService` still owns recursive traversal and DB access.

- [ ] **Step 3: Commit docs**

Run:

```bash
git add docs/plans/backend-architecture-audit-inventory.md docs/plans/current-status.md docs/plans/handoff.md docs/superpowers/plans/2026-06-02-location-statistics-payload.md
git commit -m "docs: record location statistics domain cleanup"
```

### Task 4: Final Verification

**Files:**
- Verify only.

- [ ] **Step 1: Run focused verification**

Run: `./venv/bin/python -m pytest tests/test_location_domain.py tests/test_location_application_use_cases.py tests/test_endpoint_application_convergence.py tests/test_backend_architecture_audit_docs.py -q`

Expected: PASS.

- [ ] **Step 2: Inspect references**

Run: `rg -n "build_location_statistics_payload|get_location_statistics|location_rules" app/services/location_service.py app/domain/location_rules.py tests/test_location_domain.py`

Expected: service imports and uses the domain helper; queries remain in `get_location_statistics`.

- [ ] **Step 3: Inspect git status**

Run: `git status --short`

Expected: no tracked changes; `.understand-anything/` may remain untracked and unrelated.
