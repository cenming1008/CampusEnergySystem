# Campus Location Rankings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move campus location ranking aggregation out of `CampusService` into the pure campus domain rules module without changing API responses.

**Architecture:** `CampusService` keeps database reads, context building, and location ancestor lookup. `app/domain/campus_rules.py` owns deterministic aggregation once the service passes row-like summaries, device/location maps, target location types, and a pure ancestor lookup callback. This slice only moves location ranking aggregation; alarm summary remains in service.

**Tech Stack:** Python, FastAPI service layer, pytest, existing row-like SQLModel object shapes.

---

### Task 1: RED Domain Test

**Files:**
- Modify: `tests/test_campus_domain.py`

- [ ] **Step 1: Write the failing test**

Add `build_location_rankings` to the campus rules import and append this test:

```python
def test_build_location_rankings_rolls_summaries_up_to_target_locations():
    locations_by_id = {
        1: SimpleNamespace(id=1, name="North Area", location_type="area", full_path="Campus/North", parent_id=None),
        2: SimpleNamespace(id=2, name="South Area", location_type="area", full_path="Campus/South", parent_id=None),
        10: SimpleNamespace(id=10, name="Lab A", location_type="building", full_path="Campus/North/Lab A", parent_id=1),
    }
    device_by_id = {
        101: SimpleNamespace(id=101, location_id=10),
        102: SimpleNamespace(id=102, location_id=2),
        103: SimpleNamespace(id=103, location_id=None),
    }
    summaries = [
        Summary("electricity", 18.1234, 6.0, 2, device_id=101),
        Summary("water", 4.0, 2.0, 0, device_id=101),
        Summary("gas", 30.0, 5.0, 1, device_id=102),
        Summary("electricity", 99.0, 99.0, 1, device_id=103),
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

    result = build_location_rankings(
        summaries,
        device_by_id,
        locations_by_id,
        {"area"},
        top_n=1,
        find_ancestor=find_ancestor,
    )

    assert result == [
        {
            "location_id": 2,
            "name": "South Area",
            "location_type": "area",
            "full_path": "Campus/South",
            "total_consumption": 30.0,
            "avg_load": 5.0,
            "energy_breakdown": {"gas": 30.0},
        }
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_location_rankings_rolls_summaries_up_to_target_locations -q`

Expected: FAIL with `ImportError` because `build_location_rankings` is not exported by `app.domain.campus_rules`.

- [ ] **Step 3: Commit RED test**

Run:

```bash
git add tests/test_campus_domain.py
git commit -m "test: capture campus location rankings"
```

### Task 2: GREEN Domain Helper and Service Delegation

**Files:**
- Modify: `app/domain/campus_rules.py`
- Modify: `app/services/campus_service.py`

- [ ] **Step 1: Add the pure domain helper**

Add this function to `app/domain/campus_rules.py`:

```python
def build_location_rankings(
    summaries: Iterable[Any],
    device_by_id: dict[int, Any],
    locations_by_id: dict[int, Any],
    target_types: set[str],
    top_n: int,
    find_ancestor: Any,
) -> list[dict]:
    """Aggregate period summaries into ranked target locations."""
    aggregates: dict[int, dict[str, Any]] = defaultdict(
        lambda: {
            "consumption": 0.0,
            "load": 0.0,
            "load_count": 0,
            "energy_breakdown": defaultdict(float),
        }
    )

    for summary in summaries:
        device = device_by_id.get(getattr(summary, "device_id"))
        location_id = getattr(device, "location_id", None) if device else None
        if location_id is None:
            continue
        target = find_ancestor(locations_by_id, location_id, target_types)
        if not target:
            continue
        item = aggregates[getattr(target, "id")]
        consumption = float(getattr(summary, "total_consumption", 0.0) or 0.0)
        item["consumption"] += consumption
        item["load"] += float(getattr(summary, "load_sum", 0.0) or 0.0)
        item["load_count"] += int(getattr(summary, "load_count", 0) or 0)
        item["energy_breakdown"][getattr(summary, "energy_type")] += consumption

    ranked_items = []
    for location_id, value in aggregates.items():
        location = locations_by_id.get(location_id)
        if not location:
            continue
        ranked_items.append(
            {
                "location_id": getattr(location, "id"),
                "name": getattr(location, "name"),
                "location_type": getattr(location, "location_type"),
                "full_path": getattr(location, "full_path"),
                "total_consumption": round(float(value["consumption"]), 3),
                "avg_load": round(float(value["load"]) / max(int(value["load_count"]), 1), 3),
                "energy_breakdown": {
                    energy_type: round(amount, 3)
                    for energy_type, amount in sorted(
                        value["energy_breakdown"].items(),
                        key=lambda item: item[1],
                        reverse=True,
                    )
                },
            }
        )

    ranked_items.sort(key=lambda item: item["total_consumption"], reverse=True)
    return ranked_items[:top_n]
```

- [ ] **Step 2: Delegate campus service calls to the domain helper**

In `app/services/campus_service.py`, import `build_location_rankings` from `app.domain.campus_rules`.

Update all three service call sites:

```python
area_rankings = build_location_rankings(
    period_summaries,
    context.device_by_id,
    context.locations_by_id,
    AREA_LOCATION_TYPES,
    top_n=5,
    find_ancestor=CampusService._find_ancestor_location,
)
```

```python
building_rankings = build_location_rankings(
    period_summaries,
    context.device_by_id,
    context.locations_by_id,
    BUILDING_LOCATION_TYPES,
    top_n=5,
    find_ancestor=CampusService._find_ancestor_location,
)
```

```python
rankings = build_location_rankings(
    period_summaries,
    context.device_by_id,
    context.locations_by_id,
    target_types,
    top_n=20,
    find_ancestor=CampusService._find_ancestor_location,
)
```

Remove the old `_build_location_rankings` static method from `CampusService`.

- [ ] **Step 3: Run tests to verify GREEN**

Run: `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_location_rankings_rolls_summaries_up_to_target_locations -q`

Expected: PASS.

- [ ] **Step 4: Run campus regression tests**

Run: `./venv/bin/python -m pytest tests/test_campus_domain.py tests/test_campus_endpoints.py tests/test_application_use_cases.py -q`

Expected: PASS.

- [ ] **Step 5: Commit implementation**

Run:

```bash
git add app/domain/campus_rules.py app/services/campus_service.py tests/test_campus_domain.py
git commit -m "refactor: move campus location rankings to domain"
```

### Task 3: Documentation Sync

**Files:**
- Modify: `docs/plans/backend-architecture-audit-inventory.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Record the completed slice**

Update the audit inventory follow-up list so it records that location rankings moved to `domain/campus_rules.py`, and leave a follow-up line saying the remaining campus cleanup target is alarm summary.

- [ ] **Step 2: Update status and handoff**

Record that the location rankings slice is complete, including test command evidence and the remaining risk that alarm summary still lives in service.

- [ ] **Step 3: Commit docs**

Run:

```bash
git add docs/plans/backend-architecture-audit-inventory.md docs/plans/current-status.md docs/plans/handoff.md docs/superpowers/plans/2026-06-02-campus-location-rankings.md
git commit -m "docs: record campus location ranking domain cleanup"
```

### Task 4: Final Verification

**Files:**
- Verify only.

- [ ] **Step 1: Run focused verification**

Run: `./venv/bin/python -m pytest tests/test_campus_domain.py tests/test_campus_endpoints.py tests/test_application_use_cases.py tests/test_backend_architecture_audit_docs.py -q`

Expected: PASS.

- [ ] **Step 2: Inspect imports and remaining references**

Run: `rg -n "build_location_rankings|_build_location_rankings" app/services/campus_service.py app/domain/campus_rules.py tests/test_campus_domain.py`

Expected: service imports and calls the domain helper; no `_build_location_rankings` remains in `CampusService`.

- [ ] **Step 3: Inspect git status**

Run: `git status --short`

Expected: no tracked changes; `.understand-anything/` may remain untracked and unrelated.
