# Location Path Rules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move location `level/full_path` calculation out of `LocationService` into a pure domain helper without changing create/update behavior.

**Architecture:** `LocationService` remains responsible for loading the parent location, mutating the SQLModel object, committing, and refreshing. A new `app/domain/location_rules.py` module owns deterministic path calculation from a location name and optional parent-like object. This slice only handles path fields; tree queries, statistics, delete behavior, and device assignment remain in service.

**Tech Stack:** Python, pytest/unittest, existing SQLModel service layer.

---

### Task 1: RED Domain Test

**Files:**
- Create: `tests/test_location_domain.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_location_domain.py`:

```python
from types import SimpleNamespace

from app.domain.location_rules import calculate_location_path_fields


def test_calculate_location_path_fields_uses_parent_path_and_level():
    parent = SimpleNamespace(level=2, full_path="/园区/北区/一号楼")

    fields = calculate_location_path_fields("三层", parent)

    assert fields == {"level": 3, "full_path": "/园区/北区/一号楼/三层"}


def test_calculate_location_path_fields_defaults_to_root_when_parent_missing():
    fields = calculate_location_path_fields("北区", None)

    assert fields == {"level": 0, "full_path": "/北区"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./venv/bin/python -m pytest tests/test_location_domain.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'app.domain.location_rules'`.

- [ ] **Step 3: Commit RED test**

Run:

```bash
git add tests/test_location_domain.py
git commit -m "test: capture location path rules"
```

### Task 2: GREEN Domain Helper and Service Delegation

**Files:**
- Create: `app/domain/location_rules.py`
- Modify: `app/services/location_service.py`

- [ ] **Step 1: Add pure domain helper**

Create `app/domain/location_rules.py`:

```python
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
```

- [ ] **Step 2: Delegate `_recalculate_path` to the helper**

In `app/services/location_service.py`, import:

```python
from app.domain.location_rules import calculate_location_path_fields
```

Then replace the body of `_recalculate_path` with:

```python
parent = session.get(Location, location.parent_id) if location.parent_id else None
path_fields = calculate_location_path_fields(location.name, parent)
location.level = path_fields["level"]
location.full_path = path_fields["full_path"]
return location
```

This preserves the existing fallback: if `parent_id` points at a missing parent, the path becomes root-level.

- [ ] **Step 3: Run tests to verify GREEN**

Run: `./venv/bin/python -m pytest tests/test_location_domain.py -q`

Expected: PASS.

- [ ] **Step 4: Run location regression tests**

Run: `./venv/bin/python -m pytest tests/test_location_domain.py tests/test_location_application_use_cases.py tests/test_endpoint_application_convergence.py -q`

Expected: PASS.

- [ ] **Step 5: Commit implementation**

Run:

```bash
git add app/domain/location_rules.py app/services/location_service.py tests/test_location_domain.py
git commit -m "refactor: move location path calculation to domain"
```

### Task 3: Documentation Sync

**Files:**
- Modify: `docs/plans/backend-architecture-audit-inventory.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Record the completed slice**

Update the audit inventory follow-up list to record that `location_service.py` path calculation moved to `domain/location_rules.py`, while tree queries and statistics remain future single-slice candidates.

- [ ] **Step 2: Update status and handoff**

Record test evidence and note that `LocationService` remains a `split_candidate` for tree/statistics cleanup.

- [ ] **Step 3: Commit docs**

Run:

```bash
git add docs/plans/backend-architecture-audit-inventory.md docs/plans/current-status.md docs/plans/handoff.md docs/superpowers/plans/2026-06-02-location-path-rules.md
git commit -m "docs: record location path domain cleanup"
```

### Task 4: Final Verification

**Files:**
- Verify only.

- [ ] **Step 1: Run focused verification**

Run: `./venv/bin/python -m pytest tests/test_location_domain.py tests/test_location_application_use_cases.py tests/test_endpoint_application_convergence.py tests/test_backend_architecture_audit_docs.py -q`

Expected: PASS.

- [ ] **Step 2: Inspect references**

Run: `rg -n "calculate_location_path_fields|_recalculate_path|location_rules" app/services/location_service.py app/domain/location_rules.py tests/test_location_domain.py`

Expected: service imports and uses the domain helper; `_recalculate_path` remains only as the service wrapper.

- [ ] **Step 3: Inspect git status**

Run: `git status --short`

Expected: no tracked changes; `.understand-anything/` may remain untracked and unrelated.
