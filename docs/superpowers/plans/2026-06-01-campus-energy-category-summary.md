# Campus Energy Category Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the campus energy category summary aggregation out of `CampusService` into a pure domain helper without changing API responses.

**Architecture:** `CampusService` remains responsible for database queries, context building, and endpoint-facing orchestration. A new `app/domain/campus_rules.py` module owns the deterministic energy category summary calculation so it can be tested without a session or models. This slice only handles one helper and leaves location rankings, subitem statistics, realtime trend, and alarm summary untouched.

**Tech Stack:** Python, FastAPI service layer, pytest, existing SQLModel models.

---

### Task 1: RED Domain Test

**Files:**
- Create: `tests/test_campus_domain.py`

- [ ] **Step 1: Write the failing test**

```python
from dataclasses import dataclass

from app.domain.campus_rules import build_energy_category_summary


@dataclass
class Summary:
    energy_type: str
    total_consumption: float
    load_sum: float
    load_count: int


def test_build_energy_category_summary_sorts_and_preserves_response_shape():
    summaries = [
        Summary("water", 12.3456, 3.0, 0),
        Summary("electricity", 30.1111, 15.0, 3),
        Summary("electricity", 5.0, 2.0, 1),
    ]

    result = build_energy_category_summary(summaries)

    assert result == [
        {
            "energy_category": "electricity",
            "label": "电",
            "total_consumption": 35.111,
            "avg_load": 4.25,
            "ratio": 0.7453,
            "estimated_carbon": 27.562,
        },
        {
            "energy_category": "water",
            "label": "水",
            "total_consumption": 12.346,
            "avg_load": 3.0,
            "ratio": 0.2547,
            "estimated_carbon": 0.0,
        },
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_energy_category_summary_sorts_and_preserves_response_shape -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'app.domain.campus_rules'`.

- [ ] **Step 3: Commit RED test**

Run:

```bash
git add tests/test_campus_domain.py
git commit -m "test: capture campus energy category summary"
```

### Task 2: GREEN Domain Helper and Service Delegation

**Files:**
- Create: `app/domain/campus_rules.py`
- Modify: `app/services/campus_service.py`

- [ ] **Step 1: Add the pure domain helper**

Create `app/domain/campus_rules.py`:

```python
"""Pure campus EMS aggregation rules."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

ENERGY_CATEGORY_LABELS = {
    "electricity": "电",
    "water": "水",
    "gas": "气",
    "cooling": "冷",
    "heat": "热",
    "steam": "蒸汽",
}


def build_energy_category_summary(summaries: Iterable[Any]) -> list[dict]:
    """Aggregate period energy summaries by energy category."""
    totals: dict[str, dict[str, float]] = defaultdict(
        lambda: {"consumption": 0.0, "load": 0.0, "load_count": 0.0}
    )
    total_consumption = 0.0
    for summary in summaries:
        consumption = float(getattr(summary, "total_consumption", 0.0) or 0.0)
        energy_type = getattr(summary, "energy_type")
        item = totals[energy_type]
        item["consumption"] += consumption
        item["load"] += float(getattr(summary, "load_sum", 0.0) or 0.0)
        item["load_count"] += float(getattr(summary, "load_count", 0) or 0)
        total_consumption += consumption

    items = []
    for energy_type, value in sorted(
        totals.items(),
        key=lambda item: item[1]["consumption"],
        reverse=True,
    ):
        consumption = round(value["consumption"], 3)
        ratio = round((consumption / total_consumption) if total_consumption else 0.0, 4)
        load_count = max(int(value["load_count"]), 1)
        items.append(
            {
                "energy_category": energy_type,
                "label": ENERGY_CATEGORY_LABELS.get(energy_type, energy_type),
                "total_consumption": consumption,
                "avg_load": round(value["load"] / load_count, 3),
                "ratio": ratio,
                "estimated_carbon": round(consumption * 0.785, 3)
                if energy_type == "electricity"
                else 0.0,
            }
        )
    return items
```

- [ ] **Step 2: Delegate campus service calls to the domain helper**

In `app/services/campus_service.py`:

```python
from app.domain.campus_rules import build_energy_category_summary
```

Then update the two call sites:

```python
energy_category_summary = build_energy_category_summary(period_summaries)
```

```python
"items": build_energy_category_summary(period_summaries),
```

Remove the old `ENERGY_CATEGORY_LABELS` constant and the `_build_energy_category_summary` static method from `CampusService`.

- [ ] **Step 3: Run tests to verify GREEN**

Run: `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_energy_category_summary_sorts_and_preserves_response_shape -q`

Expected: PASS.

- [ ] **Step 4: Run campus regression tests**

Run: `./venv/bin/python -m pytest tests/test_campus_domain.py tests/test_campus_endpoints.py tests/test_application_use_cases.py -q`

Expected: PASS.

- [ ] **Step 5: Commit implementation**

Run:

```bash
git add app/domain/campus_rules.py app/services/campus_service.py
git commit -m "refactor: move campus energy category summary to domain"
```

### Task 3: Documentation Sync

**Files:**
- Modify: `docs/plans/backend-architecture-audit-inventory.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Record the completed slice**

Update the audit inventory follow-up list so item 5 records that `campus_service.py` energy category summary moved to `domain/campus_rules.py`, and add a new follow-up line saying further campus cleanup must choose one remaining helper.

- [ ] **Step 2: Update status and handoff**

Record that the campus energy category summary slice is complete, including the test command evidence and the remaining risk that other campus aggregation helpers still live in service.

- [ ] **Step 3: Commit docs**

Run:

```bash
git add docs/plans/backend-architecture-audit-inventory.md docs/plans/current-status.md docs/plans/handoff.md
git commit -m "docs: record campus summary domain cleanup"
```

### Task 4: Final Verification

**Files:**
- Verify only.

- [ ] **Step 1: Run focused verification**

Run: `./venv/bin/python -m pytest tests/test_campus_domain.py tests/test_campus_endpoints.py tests/test_application_use_cases.py tests/test_backend_architecture_audit_docs.py -q`

Expected: PASS.

- [ ] **Step 2: Inspect imports and remaining references**

Run: `rg -n "build_energy_category_summary|ENERGY_CATEGORY_LABELS|estimated_carbon" app/services/campus_service.py app/domain/campus_rules.py tests/test_campus_domain.py`

Expected: service imports and calls the domain helper; label constants and carbon formula live in `app/domain/campus_rules.py`.

- [ ] **Step 3: Inspect git status**

Run: `git status --short`

Expected: no tracked changes; `.understand-anything/` may remain untracked and unrelated.
