# Campus Alarm Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move campus alarm summary aggregation out of `CampusService` into the pure campus domain rules module without changing API responses.

**Architecture:** `CampusService` keeps alarm queries, context building, and location ancestor lookup. `app/domain/campus_rules.py` owns deterministic summary aggregation once the service passes row-like alarms, device/location maps, target location types, and a pure ancestor lookup callback. This slice does not modify `alarm_service.py` lifecycle or rule evaluation.

**Tech Stack:** Python, FastAPI service layer, pytest, row-like SQLModel object shapes.

---

### Task 1: RED Domain Test

**Files:**
- Modify: `tests/test_campus_domain.py`

- [ ] **Step 1: Write the failing test**

Add `build_alarm_summary` to the campus rules import and append this test:

```python
def test_build_alarm_summary_counts_status_severity_locations_and_latest():
    t1 = datetime(2026, 6, 2, 9, 0, 0)
    t2 = datetime(2026, 6, 2, 9, 5, 0)
    t3 = datetime(2026, 6, 2, 9, 10, 0)
    locations_by_id = {
        1: SimpleNamespace(id=1, name="North Area", location_type="area", full_path="Campus/North", parent_id=None),
        2: SimpleNamespace(id=2, name="Lab A", location_type="building", full_path="Campus/North/Lab A", parent_id=1),
    }
    device_by_id = {
        101: SimpleNamespace(id=101, location_id=2),
        102: SimpleNamespace(id=102, location_id=None),
    }
    alarms = [
        SimpleNamespace(id=1, device_id=101, message="High load", severity="warning", category="energy", timestamp=t1, is_resolved=False),
        SimpleNamespace(id=2, device_id=101, message="Meter offline", severity="critical", category="device", timestamp=t2, is_resolved=True),
        SimpleNamespace(id=3, device_id=102, message="No location", severity="warning", category="device", timestamp=t3, is_resolved=False),
    ]

    def find_ancestor(locations, location_id, target_types):
        current_id = location_id
        while current_id is not None:
            location = locations.get(current_id)
            if not location:
                return None
            if location.location_type in target_types:
                return location
            current_id = location.parent_id
        return None

    result = build_alarm_summary(
        alarms,
        device_by_id,
        locations_by_id,
        {"area", "building"},
        find_ancestor=find_ancestor,
    )

    assert result == {
        "total_count": 3,
        "unresolved_count": 2,
        "resolved_count": 1,
        "by_severity": {"critical": 1, "warning": 2},
        "top_locations": [
            {"location_id": 2, "name": "Lab A", "location_type": "building", "alarm_count": 2},
        ],
        "latest": [
            {"id": 1, "device_id": 101, "message": "High load", "severity": "warning", "category": "energy", "timestamp": t1, "is_resolved": False},
            {"id": 2, "device_id": 101, "message": "Meter offline", "severity": "critical", "category": "device", "timestamp": t2, "is_resolved": True},
            {"id": 3, "device_id": 102, "message": "No location", "severity": "warning", "category": "device", "timestamp": t3, "is_resolved": False},
        ],
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_alarm_summary_counts_status_severity_locations_and_latest -q`

Expected: FAIL with `ImportError` because `build_alarm_summary` is not exported by `app.domain.campus_rules`.

- [ ] **Step 3: Commit RED test**

Run:

```bash
git add tests/test_campus_domain.py
git commit -m "test: capture campus alarm summary"
```

### Task 2: GREEN Domain Helper and Service Delegation

**Files:**
- Modify: `app/domain/campus_rules.py`
- Modify: `app/services/campus_service.py`

- [ ] **Step 1: Add the pure domain helper**

Add this function to `app/domain/campus_rules.py`:

```python
def build_alarm_summary(
    rows: Iterable[Any],
    device_by_id: dict[int, Any],
    locations_by_id: dict[int, Any],
    target_types: set[str],
    find_ancestor: Any,
) -> dict:
    """Aggregate row-like alarms into a campus alarm summary."""
    rows = list(rows)
    by_severity: dict[str, int] = defaultdict(int)
    by_location: dict[int, int] = defaultdict(int)

    unresolved_count = 0
    for alarm in rows:
        by_severity[getattr(alarm, "severity")] += 1
        if not getattr(alarm, "is_resolved"):
            unresolved_count += 1
        device = device_by_id.get(getattr(alarm, "device_id"))
        location_id = getattr(device, "location_id", None) if device else None
        if location_id is not None:
            target = find_ancestor(locations_by_id, location_id, target_types)
            if target:
                by_location[getattr(target, "id")] += 1

    top_locations = []
    for location_id, count in sorted(by_location.items(), key=lambda item: item[1], reverse=True)[:5]:
        location = locations_by_id.get(location_id)
        if location:
            top_locations.append(
                {
                    "location_id": getattr(location, "id"),
                    "name": getattr(location, "name"),
                    "location_type": getattr(location, "location_type"),
                    "alarm_count": count,
                }
            )

    latest = [
        {
            "id": getattr(alarm, "id"),
            "device_id": getattr(alarm, "device_id"),
            "message": getattr(alarm, "message"),
            "severity": getattr(alarm, "severity"),
            "category": getattr(alarm, "category"),
            "timestamp": getattr(alarm, "timestamp"),
            "is_resolved": getattr(alarm, "is_resolved"),
        }
        for alarm in rows[:10]
    ]

    return {
        "total_count": len(rows),
        "unresolved_count": unresolved_count,
        "resolved_count": len(rows) - unresolved_count,
        "by_severity": dict(sorted(by_severity.items())),
        "top_locations": top_locations,
        "latest": latest,
    }
```

- [ ] **Step 2: Delegate campus service calls to the domain helper**

In `app/services/campus_service.py`, import `build_alarm_summary` from `app.domain.campus_rules`.

Update both service call sites:

```python
alarm_summary = build_alarm_summary(
    alarm_rows,
    context.device_by_id,
    context.locations_by_id,
    AREA_LOCATION_TYPES | BUILDING_LOCATION_TYPES,
    find_ancestor=CampusService._find_ancestor_location,
)
```

```python
summary = build_alarm_summary(
    rows,
    context.device_by_id,
    context.locations_by_id,
    AREA_LOCATION_TYPES | BUILDING_LOCATION_TYPES,
    find_ancestor=CampusService._find_ancestor_location,
)
```

Remove the old `_build_alarm_summary` static method from `CampusService`.

- [ ] **Step 3: Run tests to verify GREEN**

Run: `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_alarm_summary_counts_status_severity_locations_and_latest -q`

Expected: PASS.

- [ ] **Step 4: Run campus regression tests**

Run: `./venv/bin/python -m pytest tests/test_campus_domain.py tests/test_campus_endpoints.py tests/test_application_use_cases.py -q`

Expected: PASS.

- [ ] **Step 5: Commit implementation**

Run:

```bash
git add app/domain/campus_rules.py app/services/campus_service.py tests/test_campus_domain.py
git commit -m "refactor: move campus alarm summary to domain"
```

### Task 3: Documentation Sync

**Files:**
- Modify: `docs/plans/backend-architecture-audit-inventory.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Record the completed slice**

Update the audit inventory follow-up list so it records that campus alarm summary moved to `domain/campus_rules.py`, while noting alarm lifecycle and rule triggering remain in `alarm_service.py`.

- [ ] **Step 2: Update status and handoff**

Record that the campus alarm summary slice is complete, including test command evidence and the remaining risk that `campus_service.py` is still a large query/orchestration service even after pure helper cleanup.

- [ ] **Step 3: Commit docs**

Run:

```bash
git add docs/plans/backend-architecture-audit-inventory.md docs/plans/current-status.md docs/plans/handoff.md docs/superpowers/plans/2026-06-02-campus-alarm-summary.md
git commit -m "docs: record campus alarm summary domain cleanup"
```

### Task 4: Final Verification

**Files:**
- Verify only.

- [ ] **Step 1: Run focused verification**

Run: `./venv/bin/python -m pytest tests/test_campus_domain.py tests/test_campus_endpoints.py tests/test_application_use_cases.py tests/test_backend_architecture_audit_docs.py -q`

Expected: PASS.

- [ ] **Step 2: Inspect imports and remaining references**

Run: `rg -n "build_alarm_summary|_build_alarm_summary" app/services/campus_service.py app/domain/campus_rules.py tests/test_campus_domain.py`

Expected: service imports and calls the domain helper; no `_build_alarm_summary` remains in `CampusService`.

- [ ] **Step 3: Inspect git status**

Run: `git status --short`

Expected: no tracked changes; `.understand-anything/` may remain untracked and unrelated.
