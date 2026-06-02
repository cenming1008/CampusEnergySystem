# Campus Realtime Load Trend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move realtime load trend aggregation out of `CampusService` into the pure campus domain rules module without changing API responses.

**Architecture:** `CampusService` remains responsible for database queries and endpoint-facing orchestration. `app/domain/campus_rules.py` owns deterministic campus aggregation helpers that operate on row-like objects. This slice only moves realtime load trend; location rankings and alarm summary remain in service.

**Tech Stack:** Python, FastAPI service layer, pytest, existing row-like SQLModel object shapes.

---

### Task 1: RED Domain Test

**Files:**
- Modify: `tests/test_campus_domain.py`

- [ ] **Step 1: Write the failing test**

Append this import and test to `tests/test_campus_domain.py`:

```python
from datetime import datetime

from app.domain.campus_rules import build_realtime_load_trend


def test_build_realtime_load_trend_groups_rows_and_ignores_negative_deltas():
    t1 = datetime(2026, 6, 2, 8, 0, 0)
    t2 = datetime(2026, 6, 2, 8, 15, 0)
    t3 = datetime(2026, 6, 2, 8, 30, 0)
    rows = [
        SimpleNamespace(device_id=1, energy_type="electricity", timestamp=t2, flow_rate=3.3333, consumption=12.5),
        SimpleNamespace(device_id=1, energy_type="electricity", timestamp=t1, flow_rate=2.0, consumption=10.0),
        SimpleNamespace(device_id=2, energy_type="water", timestamp=t2, flow_rate=None, consumption=4.0),
        SimpleNamespace(device_id=2, energy_type="water", timestamp=t3, flow_rate=1.25, consumption=2.0),
    ]

    result = build_realtime_load_trend(rows)

    assert result == [
        {"timestamp": t1, "total_load": 2.0, "total_consumption": 0.0},
        {"timestamp": t2, "total_load": 3.333, "total_consumption": 2.5},
        {"timestamp": t3, "total_load": 1.25, "total_consumption": 0.0},
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_realtime_load_trend_groups_rows_and_ignores_negative_deltas -q`

Expected: FAIL with `ImportError` because `build_realtime_load_trend` is not exported by `app.domain.campus_rules`.

- [ ] **Step 3: Commit RED test**

Run:

```bash
git add tests/test_campus_domain.py
git commit -m "test: capture campus realtime load trend"
```

### Task 2: GREEN Domain Helper and Service Delegation

**Files:**
- Modify: `app/domain/campus_rules.py`
- Modify: `app/services/campus_service.py`

- [ ] **Step 1: Add the pure domain helper**

Add this function to `app/domain/campus_rules.py`:

```python
def build_realtime_load_trend(rows: Iterable[Any]) -> list[dict]:
    """Aggregate row-like realtime readings into timestamp buckets."""
    buckets: dict[Any, dict[str, float]] = defaultdict(lambda: {"load": 0.0, "consumption": 0.0})
    grouped_rows: dict[tuple[Any, Any], list[Any]] = defaultdict(list)
    for row in rows:
        grouped_rows[(getattr(row, "device_id"), getattr(row, "energy_type"))].append(row)

    for group_rows in grouped_rows.values():
        ordered_rows = sorted(group_rows, key=lambda row: getattr(row, "timestamp"))
        previous_consumption = None
        for row in ordered_rows:
            timestamp = getattr(row, "timestamp")
            bucket = buckets[timestamp]
            bucket["load"] += float(getattr(row, "flow_rate", 0.0) or 0.0)
            current_consumption = float(getattr(row, "consumption", 0.0) or 0.0)
            if previous_consumption is not None:
                bucket["consumption"] += max(0.0, current_consumption - previous_consumption)
            previous_consumption = current_consumption

    return [
        {
            "timestamp": timestamp,
            "total_load": round(values["load"], 3),
            "total_consumption": round(values["consumption"], 3),
        }
        for timestamp, values in sorted(buckets.items(), key=lambda item: item[0])
    ]
```

- [ ] **Step 2: Delegate campus service calls to the domain helper**

In `app/services/campus_service.py`, import:

```python
from app.domain.campus_rules import (
    build_energy_category_summary,
    build_realtime_load_trend,
    build_subitem_statistics,
)
```

Update both call sites:

```python
realtime_load_trend = build_realtime_load_trend(trend_rows)
```

```python
"items": build_realtime_load_trend(rows),
```

Remove the old `_build_realtime_load_trend` static method from `CampusService`.

- [ ] **Step 3: Run tests to verify GREEN**

Run: `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_realtime_load_trend_groups_rows_and_ignores_negative_deltas -q`

Expected: PASS.

- [ ] **Step 4: Run campus regression tests**

Run: `./venv/bin/python -m pytest tests/test_campus_domain.py tests/test_campus_endpoints.py tests/test_application_use_cases.py -q`

Expected: PASS.

- [ ] **Step 5: Commit implementation**

Run:

```bash
git add app/domain/campus_rules.py app/services/campus_service.py tests/test_campus_domain.py
git commit -m "refactor: move campus realtime load trend to domain"
```

### Task 3: Documentation Sync

**Files:**
- Modify: `docs/plans/backend-architecture-audit-inventory.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Record the completed slice**

Update the audit inventory follow-up list so it records that realtime load trend moved to `domain/campus_rules.py`, and leave a follow-up line saying further campus cleanup must choose one remaining helper.

- [ ] **Step 2: Update status and handoff**

Record that the realtime load trend slice is complete, including test command evidence and the remaining risk that location rankings and alarm summary still live in service.

- [ ] **Step 3: Commit docs**

Run:

```bash
git add docs/plans/backend-architecture-audit-inventory.md docs/plans/current-status.md docs/plans/handoff.md docs/superpowers/plans/2026-06-02-campus-realtime-load-trend.md
git commit -m "docs: record campus realtime trend domain cleanup"
```

### Task 4: Final Verification

**Files:**
- Verify only.

- [ ] **Step 1: Run focused verification**

Run: `./venv/bin/python -m pytest tests/test_campus_domain.py tests/test_campus_endpoints.py tests/test_application_use_cases.py tests/test_backend_architecture_audit_docs.py -q`

Expected: PASS.

- [ ] **Step 2: Inspect imports and remaining references**

Run: `rg -n "build_realtime_load_trend|_build_realtime_load_trend" app/services/campus_service.py app/domain/campus_rules.py tests/test_campus_domain.py`

Expected: service imports and calls the domain helper; no `_build_realtime_load_trend` remains in `CampusService`.

- [ ] **Step 3: Inspect git status**

Run: `git status --short`

Expected: no tracked changes; `.understand-anything/` may remain untracked and unrelated.
