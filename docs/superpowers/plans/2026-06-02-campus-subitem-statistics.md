# Campus Subitem Statistics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the campus subitem statistics aggregation out of `CampusService` into the existing pure campus domain rules module without changing API responses.

**Architecture:** `CampusService` stays responsible for database reads and request-facing orchestration. `app/domain/campus_rules.py` owns deterministic campus aggregation helpers and shared campus labels. This slice only moves subitem statistics and its label map; location rankings, realtime load trends, and alarm summary remain in service.

**Tech Stack:** Python, FastAPI service layer, pytest, existing SQLModel model shapes.

---

### Task 1: RED Domain Test

**Files:**
- Modify: `tests/test_campus_domain.py`

- [ ] **Step 1: Write the failing test**

Append this test to `tests/test_campus_domain.py`:

```python
from types import SimpleNamespace

from app.domain.campus_rules import build_subitem_statistics


def test_build_subitem_statistics_groups_by_device_category_and_ignores_missing_devices():
    summaries = [
        Summary(device_id=1, energy_type="electricity", total_consumption=20.555, load_sum=6.0, load_count=2),
        Summary(device_id=1, energy_type="water", total_consumption=4.0, load_sum=2.0, load_count=0),
        Summary(device_id=2, energy_type="gas", total_consumption=10.0, load_sum=3.0, load_count=1),
        Summary(device_id=99, energy_type="electricity", total_consumption=100.0, load_sum=100.0, load_count=1),
    ]
    device_by_id = {
        1: SimpleNamespace(id=1, device_category="load", device_type="meter"),
        2: SimpleNamespace(id=2, device_category=None, device_type="gas_meter"),
    }

    result = build_subitem_statistics(summaries, device_by_id)

    assert result == [
        {
            "sub_item": "load",
            "label": "动力/普通负荷",
            "total_consumption": 24.555,
            "avg_load": 4.0,
            "device_count": 1,
            "energy_categories": ["electricity", "water"],
        },
        {
            "sub_item": "gas_meter",
            "label": "燃气计量",
            "total_consumption": 10.0,
            "avg_load": 3.0,
            "device_count": 1,
            "energy_categories": ["gas"],
        },
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_subitem_statistics_groups_by_device_category_and_ignores_missing_devices -q`

Expected: FAIL with `ImportError` because `build_subitem_statistics` is not exported by `app.domain.campus_rules`.

- [ ] **Step 3: Commit RED test**

Run:

```bash
git add tests/test_campus_domain.py
git commit -m "test: capture campus subitem statistics"
```

### Task 2: GREEN Domain Helper and Service Delegation

**Files:**
- Modify: `app/domain/campus_rules.py`
- Modify: `app/services/campus_service.py`
- Modify: `app/services/analysis_service.py`

- [ ] **Step 1: Move subitem labels and helper to domain**

Add this to `app/domain/campus_rules.py` after `ENERGY_CATEGORY_LABELS`:

```python
SUB_ITEM_LABELS = {
    "load": "动力/普通负荷",
    "solar": "光伏",
    "wind": "风电",
    "water_meter": "给排水计量",
    "gas_meter": "燃气计量",
    "heat_meter": "供热计量",
    "cooling_meter": "供冷计量",
    "storage": "储能",
    "charger": "充电桩",
}
```

Add this function after `build_energy_category_summary`:

```python
def build_subitem_statistics(summaries: Iterable[Any], device_by_id: dict[int, Any]) -> list[dict]:
    """Aggregate period energy summaries by device category or type."""
    items: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "consumption": 0.0,
            "load": 0.0,
            "load_count": 0,
            "device_ids": set(),
            "energy_categories": set(),
        }
    )
    for summary in summaries:
        device = device_by_id.get(getattr(summary, "device_id"))
        if not device:
            continue
        sub_item = getattr(device, "device_category", None) or getattr(device, "device_type", None) or "device"
        item = items[sub_item]
        item["consumption"] += float(getattr(summary, "total_consumption", 0.0) or 0.0)
        item["load"] += float(getattr(summary, "load_sum", 0.0) or 0.0)
        item["load_count"] += int(getattr(summary, "load_count", 0) or 0)
        item["device_ids"].add(getattr(device, "id"))
        item["energy_categories"].add(getattr(summary, "energy_type"))

    result = []
    for sub_item, value in sorted(items.items(), key=lambda item: item[1]["consumption"], reverse=True):
        result.append(
            {
                "sub_item": sub_item,
                "label": SUB_ITEM_LABELS.get(sub_item, sub_item),
                "total_consumption": round(float(value["consumption"]), 3),
                "avg_load": round(float(value["load"]) / max(int(value["load_count"]), 1), 3),
                "device_count": len(value["device_ids"]),
                "energy_categories": sorted(value["energy_categories"]),
            }
        )
    return result
```

- [ ] **Step 2: Delegate campus service calls to the domain helper**

In `app/services/campus_service.py`, import:

```python
from app.domain.campus_rules import build_energy_category_summary, build_subitem_statistics
```

Update the two service call sites:

```python
subitem_statistics = build_subitem_statistics(period_summaries, context.device_by_id)
```

```python
"items": build_subitem_statistics(period_summaries, context.device_by_id),
```

Remove the old `SUB_ITEM_LABELS` constant and `_build_subitem_statistics` static method from `CampusService`.

- [ ] **Step 3: Update analysis service label import**

In `app/services/analysis_service.py`, import `SUB_ITEM_LABELS` from `app.domain.campus_rules` with `ENERGY_CATEGORY_LABELS`, and remove `SUB_ITEM_LABELS` from the `app.services.campus_service` import list.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_subitem_statistics_groups_by_device_category_and_ignores_missing_devices -q`

Expected: PASS.

- [ ] **Step 5: Run campus regression tests**

Run: `./venv/bin/python -m pytest tests/test_campus_domain.py tests/test_campus_endpoints.py tests/test_application_use_cases.py -q`

Expected: PASS.

- [ ] **Step 6: Commit implementation**

Run:

```bash
git add app/domain/campus_rules.py app/services/campus_service.py app/services/analysis_service.py tests/test_campus_domain.py
git commit -m "refactor: move campus subitem statistics to domain"
```

### Task 3: Documentation Sync

**Files:**
- Modify: `docs/plans/backend-architecture-audit-inventory.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Record the completed slice**

Update the audit inventory follow-up list so it records that `campus_service.py` subitem statistics moved to `domain/campus_rules.py`, and leave a follow-up line saying further campus cleanup must choose one remaining helper.

- [ ] **Step 2: Update status and handoff**

Record that the campus subitem statistics slice is complete, including test command evidence and the remaining risk that location rankings, realtime trend, and alarm summary still live in service.

- [ ] **Step 3: Commit docs**

Run:

```bash
git add docs/plans/backend-architecture-audit-inventory.md docs/plans/current-status.md docs/plans/handoff.md docs/superpowers/plans/2026-06-02-campus-subitem-statistics.md
git commit -m "docs: record campus subitem domain cleanup"
```

### Task 4: Final Verification

**Files:**
- Verify only.

- [ ] **Step 1: Run focused verification**

Run: `./venv/bin/python -m pytest tests/test_campus_domain.py tests/test_campus_endpoints.py tests/test_application_use_cases.py tests/test_backend_architecture_audit_docs.py -q`

Expected: PASS.

- [ ] **Step 2: Inspect imports and remaining references**

Run: `rg -n "build_subitem_statistics|SUB_ITEM_LABELS|_build_subitem_statistics" app/services/campus_service.py app/services/analysis_service.py app/domain/campus_rules.py tests/test_campus_domain.py`

Expected: service imports and calls the domain helper; label constants live in `app/domain/campus_rules.py`; no `_build_subitem_statistics` remains in `CampusService`.

- [ ] **Step 3: Inspect git status**

Run: `git status --short`

Expected: no tracked changes; `.understand-anything/` may remain untracked and unrelated.
