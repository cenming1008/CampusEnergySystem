# Compensation Health Rules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move compensation monitor health-score primitive rules from `CompensationMonitorService` into `app/domain/compensation_rules.py`.

**Architecture:** `CompensationMonitorService` should keep telemetry/profile field extraction and monitor payload assembly. Primitive health calculations such as score clamping, threshold scoring, communication scoring, switching scoring, voltage stability scoring, and rating labels are pure compensation-domain rules and should live in `app/domain/compensation_rules.py`. This slice does not change monitor response shape or control-command behavior.

**Tech Stack:** Python, pytest/unittest.

---

### Task 1: Capture Health Primitive Domain Rules

**Files:**
- Modify: `tests/test_compensation_domain.py`

- [ ] **Step 1: Write the failing tests**

Update the import in `tests/test_compensation_domain.py`:

```python
from app.domain.compensation_rules import (
    build_pq_reference_line,
    clamp_health_score,
    comm_health_score,
    health_rating,
    max_defined_number,
    normalize_power_factor,
    score_by_threshold,
    switching_health_score,
    voltage_stability_score,
)
```

Append these tests:

```python
def test_health_score_primitives_preserve_monitor_threshold_behavior():
    assert clamp_health_score(99.6) == 100
    assert clamp_health_score(-4) == 0
    assert score_by_threshold(2.5, 5.0) == 90
    assert score_by_threshold(6.0, 5.0) == 72
    assert score_by_threshold(None, 5.0) == 0
    assert max_defined_number((None, 3.2, 5.1, None)) == 5.1
    assert max_defined_number((None, None)) is None


def test_health_status_primitives_preserve_monitor_payload_values():
    assert comm_health_score("online", True) == 100
    assert comm_health_score("online", False) == 70
    assert comm_health_score("degraded", True) == 55
    assert comm_health_score("offline", True) == 15
    assert comm_health_score(None, True) == 0
    assert voltage_stability_score(220.0) == 100
    assert voltage_stability_score(None) == 0
    assert switching_health_score((True, False, None)) == 82
    assert switching_health_score((None, None)) == 0
    assert health_rating(92) == {"rating": "优秀", "ratingTone": "success"}
    assert health_rating(55) == {"rating": "关注", "ratingTone": "warning"}
    assert health_rating(15) == {"rating": "异常", "ratingTone": "danger"}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./venv/bin/python -m pytest tests/test_compensation_domain.py::test_health_score_primitives_preserve_monitor_threshold_behavior -q
```

Expected: FAIL with `ImportError` because the health helper functions do not exist in `app.domain.compensation_rules` yet.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/plans/2026-06-02-compensation-health-rules.md tests/test_compensation_domain.py
git commit -m "test: capture compensation health rules"
```

### Task 2: Move Health Primitive Rules to Domain

**Files:**
- Modify: `app/domain/compensation_rules.py`
- Modify: `app/services/devices/compensation/monitor_service.py`

- [ ] **Step 1: Add domain helpers**

Add these constants and functions to `app/domain/compensation_rules.py`:

```python
HEALTH_NOMINAL_VOLTAGE = 220.0


def clamp_health_score(value: float) -> int:
    return max(0, min(100, int(value + 0.5)))


def score_by_threshold(value: Optional[float], threshold: float) -> Optional[int]:
    if value is None:
        return 0
    ratio = float(value) / threshold
    if ratio <= 1:
        return clamp_health_score(100 - ratio * 20)
    return clamp_health_score(80 - (ratio - 1) * 40)


def max_defined_number(values: tuple[Optional[float], ...]) -> Optional[float]:
    defined = [float(value) for value in values if value is not None]
    return max(defined) if defined else None


def comm_health_score(ingestion_status: Optional[str], is_realtime_fresh: bool) -> Optional[int]:
    if ingestion_status == "online":
        return 100 if is_realtime_fresh else 70
    if ingestion_status == "degraded":
        return 55
    if ingestion_status == "offline":
        return 15
    return 0


def voltage_stability_score(voltage: Optional[float], nominal_voltage: float = HEALTH_NOMINAL_VOLTAGE) -> Optional[int]:
    if voltage is None:
        return 0
    deviation_pct = (abs(float(voltage) - nominal_voltage) / nominal_voltage) * 100
    return clamp_health_score(100 - deviation_pct * 4)


def switching_health_score(flags: tuple[Optional[bool], ...]) -> Optional[int]:
    if all(flag is None for flag in flags):
        return 0
    active_count = sum(1 for flag in flags if flag is True)
    return clamp_health_score(100 - active_count * 18)


def health_rating(score: Optional[int]) -> dict[str, str]:
    if score is None:
        return {"rating": "暂无评级", "ratingTone": "neutral"}
    if score >= 85:
        return {"rating": "优秀", "ratingTone": "success"}
    if score >= 70:
        return {"rating": "良好", "ratingTone": "success"}
    if score >= 50:
        return {"rating": "关注", "ratingTone": "warning"}
    return {"rating": "异常", "ratingTone": "danger"}
```

- [ ] **Step 2: Reuse helpers in service**

Import the new helpers in `app/services/devices/compensation/monitor_service.py` and replace service-private calls:

```python
from app.domain.compensation_rules import (
    build_pq_reference_line,
    clamp_health_score,
    comm_health_score,
    health_rating,
    max_defined_number,
    normalize_power_factor,
    optional_float,
    score_by_threshold,
    switching_health_score,
    voltage_stability_score,
)
```

Remove service-private `_clamp_health_score`, `_score_by_threshold`, `_max_defined_number`, `_comm_health_score`, `_voltage_stability_score`, `_switching_health_score`, and `_health_rating`.

- [ ] **Step 3: Run focused tests**

Run:

```bash
./venv/bin/python -m pytest tests/test_compensation_domain.py tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_returns_backend_health_model tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_health_model_defaults_missing_dimensions_to_zero -q
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add app/domain/compensation_rules.py app/services/devices/compensation/monitor_service.py tests/test_compensation_domain.py
git commit -m "refactor: move compensation health rules to domain"
```

### Task 3: Record Architecture Cleanup

**Files:**
- Modify: `docs/plans/backend-architecture-audit-inventory.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Update architecture docs**

Record that `CompensationMonitorService` now delegates health primitive rules to `domain/compensation_rules.py`; monitor payload assembly and telemetry reads remain in service.

- [ ] **Step 2: Run verification**

Run:

```bash
./venv/bin/python -m pytest tests/test_compensation_domain.py tests/test_compensation_monitor_service_boundary.py tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_returns_backend_health_model tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_health_model_defaults_missing_dimensions_to_zero tests/test_backend_architecture_audit_docs.py -q
```

Expected: PASS.

Run:

```bash
rg -n "_clamp_health_score|_score_by_threshold|_max_defined_number|_comm_health_score|_voltage_stability_score|_switching_health_score|_health_rating|clamp_health_score|score_by_threshold|health_rating" app/services/devices/compensation/monitor_service.py app/domain/compensation_rules.py tests/test_compensation_domain.py
```

Expected: service imports and calls public domain helpers, with no private service health primitive definitions.

- [ ] **Step 3: Commit**

```bash
git add docs/plans/backend-architecture-audit-inventory.md docs/plans/current-status.md docs/plans/handoff.md
git commit -m "docs: record compensation health rules cleanup"
```
