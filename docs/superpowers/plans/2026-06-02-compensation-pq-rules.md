# Compensation PQ Rules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move compensation monitor PQ helper rules out of `CompensationMonitorService` into a focused domain module.

**Architecture:** `app/services/devices/compensation/monitor_service.py` should orchestrate telemetry/profile reads and assemble the monitor payload. Numeric rules such as power-factor normalization and PQ reference-line formatting are pure compensation-domain logic, so they belong in `app/domain/compensation_rules.py`. This slice does not change API payload shape or remote-control behavior.

**Tech Stack:** Python, pytest/unittest.

---

### Task 1: Capture Compensation PQ Domain Rules

**Files:**
- Create: `tests/test_compensation_domain.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_compensation_domain.py`:

```python
from app.domain.compensation_rules import build_pq_reference_line, normalize_power_factor


def test_normalize_power_factor_accepts_percent_and_ratio_values():
    assert normalize_power_factor(95) == 0.95
    assert normalize_power_factor(0.92) == 0.92
    assert normalize_power_factor("98") == 0.98
    assert normalize_power_factor(0) is None
    assert normalize_power_factor("bad") is None


def test_build_pq_reference_line_preserves_existing_payload_shape():
    assert build_pq_reference_line(0.9, role="threshold") == {
        "powerFactor": 0.9,
        "label": "PF 0.90",
        "role": "threshold",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./venv/bin/python -m pytest tests/test_compensation_domain.py -q
```

Expected: FAIL with `ModuleNotFoundError` because `app.domain.compensation_rules` does not exist yet.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/plans/2026-06-02-compensation-pq-rules.md tests/test_compensation_domain.py
git commit -m "test: capture compensation pq rules"
```

### Task 2: Move PQ Helpers to Domain

**Files:**
- Create: `app/domain/compensation_rules.py`
- Modify: `app/services/devices/compensation/monitor_service.py`

- [ ] **Step 1: Add domain rules**

Create `app/domain/compensation_rules.py`:

```python
"""Pure compensation-device domain rules."""

from __future__ import annotations

from typing import Any, Optional


def optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_power_factor(value: Any) -> Optional[float]:
    numeric = optional_float(value)
    if numeric is None:
        return None
    if numeric > 2:
        numeric = numeric / 100.0
    if numeric <= 0:
        return None
    return min(0.999, numeric)


def build_pq_reference_line(power_factor: float, *, role: str) -> dict[str, Any]:
    normalized = round(power_factor, 3)
    return {
        "powerFactor": normalized,
        "label": f"PF {normalized:.2f}",
        "role": role,
    }
```

- [ ] **Step 2: Reuse rules in service**

Import from `app.domain.compensation_rules`:

```python
from app.domain.compensation_rules import build_pq_reference_line, normalize_power_factor, optional_float
```

Remove service-private `_optional_float`, `_normalize_power_factor`, and `_build_pq_reference_line`, then replace calls with the imported functions.

- [ ] **Step 3: Run focused tests**

Run:

```bash
./venv/bin/python -m pytest tests/test_compensation_domain.py tests/test_compensation_monitor_service_boundary.py -q
```

Expected: PASS.

Run:

```bash
./venv/bin/python -m pytest tests/test_device_monitor_service.py::DeviceMonitorServiceTest::test_monitor_overview_capacitor_bank_pq_model_uses_profile_thresholds -q
```

Expected: PASS if the test exists under that class name; if the node id differs, run the containing file and verify the PQ model assertion passes.

- [ ] **Step 4: Commit**

```bash
git add app/domain/compensation_rules.py app/services/devices/compensation/monitor_service.py tests/test_compensation_domain.py
git commit -m "refactor: move compensation pq rules to domain"
```

### Task 3: Record Architecture Cleanup

**Files:**
- Modify: `docs/plans/backend-architecture-audit-inventory.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Update architecture docs**

Record that `app/services/devices/compensation/monitor_service.py` now delegates pure PQ formatting/normalization rules to `app/domain/compensation_rules.py`; telemetry queries and monitor payload assembly remain in service.

- [ ] **Step 2: Run verification**

Run:

```bash
./venv/bin/python -m pytest tests/test_compensation_domain.py tests/test_compensation_monitor_service_boundary.py tests/test_backend_architecture_audit_docs.py -q
```

Expected: PASS.

Run:

```bash
rg -n "_normalize_power_factor|_build_pq_reference_line|normalize_power_factor|build_pq_reference_line|optional_float" app/services/devices/compensation/monitor_service.py app/domain/compensation_rules.py tests/test_compensation_domain.py
```

Expected: service imports and calls public domain helpers, with no private `_normalize_power_factor` or `_build_pq_reference_line` definitions.

- [ ] **Step 3: Commit**

```bash
git add docs/plans/backend-architecture-audit-inventory.md docs/plans/current-status.md docs/plans/handoff.md
git commit -m "docs: record compensation pq rules cleanup"
```
