# Alarm Threshold Managed Categories Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move generic/media threshold managed-category derivation out of `AlarmService` and into pure alarm domain rules without changing API behavior.

**Architecture:** `app/services/alarm_service.py` should orchestrate telemetry loading, profile resolution, fault evaluation, and persistence. The mapping from present telemetry fields to platform-rule alarm categories is deterministic domain logic, so it belongs in `app/domain/alarm_rules.py` beside storage/SVG/capacitor managed-category helpers. Existing service behavior stays compatible: only fields present with non-`None` values are included.

**Tech Stack:** Python, FastAPI service layer, pytest.

---

### Task 1: Capture Threshold Managed Categories

**Files:**
- Modify: `tests/test_alarm_rule_profiles.py`

- [ ] **Step 1: Write the failing test**

Append this test after `test_storage_managed_categories_follow_present_payload_fields`:

```python
def test_threshold_managed_categories_follow_present_payload_fields():
    from app.domain.alarm_rules import get_threshold_managed_categories

    assert get_threshold_managed_categories(
        {
            "current": 51.0,
            "voltage": None,
            "flow_rate": 0,
            "pressure": 1.2,
            "temperature": None,
            "irrelevant": 123,
        }
    ) == {
        "current_overload",
        "flow_rate_out_of_range",
        "pressure_out_of_range",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py::test_threshold_managed_categories_follow_present_payload_fields -q
```

Expected: FAIL with `ImportError` because `get_threshold_managed_categories` does not exist yet.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/plans/2026-06-02-alarm-threshold-managed-categories.md tests/test_alarm_rule_profiles.py
git commit -m "test: capture threshold managed categories"
```

### Task 2: Move Managed Category Rule to Domain

**Files:**
- Modify: `app/domain/alarm_rules.py`
- Modify: `app/services/alarm_service.py`

- [ ] **Step 1: Add the domain helper**

Add this constant and helper near the other managed-category helpers in `app/domain/alarm_rules.py`:

```python
THRESHOLD_MANAGED_CATEGORY_FIELDS: dict[str, str] = {
    "current": "current_overload",
    "voltage": "voltage_out_of_range",
    "flow_rate": "flow_rate_out_of_range",
    "pressure": "pressure_out_of_range",
    "temperature": "temperature_out_of_range",
}


def get_threshold_managed_categories(data: dict[str, Any]) -> set[str]:
    """Return generic/media platform alarm categories managed by present telemetry fields."""
    return {
        category
        for field, category in THRESHOLD_MANAGED_CATEGORY_FIELDS.items()
        if field in data and data[field] is not None
    }
```

- [ ] **Step 2: Replace inline service logic**

Replace the inline `managed_categories` construction in `AlarmService.check_and_create_alarm` with:

```python
        # 仅对本次检测的字段做 recover 管理（保持原行为）
        managed_categories = alarm_rules.get_threshold_managed_categories(data)
```

- [ ] **Step 3: Run focused tests**

Run:

```bash
./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py::test_threshold_managed_categories_follow_present_payload_fields -q
```

Expected: PASS.

Run:

```bash
./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py tests/test_alarm_service.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add app/domain/alarm_rules.py app/services/alarm_service.py tests/test_alarm_rule_profiles.py
git commit -m "refactor: move threshold managed categories to domain"
```

### Task 3: Record Architecture Cleanup

**Files:**
- Modify: `docs/plans/backend-architecture-audit-inventory.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Update architecture docs**

Record that `AlarmService` no longer owns the generic/media managed-category mapping, and keep remaining alarm-service work scoped to lifecycle/query orchestration.

- [ ] **Step 2: Run verification**

Run:

```bash
./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py tests/test_alarm_service.py tests/test_backend_architecture_audit_docs.py -q
```

Expected: PASS.

Run:

```bash
rg -n "get_threshold_managed_categories|managed_categories: set|current_overload|flow_rate_out_of_range" app/services/alarm_service.py app/domain/alarm_rules.py tests/test_alarm_rule_profiles.py
```

Expected: `app/services/alarm_service.py` calls `alarm_rules.get_threshold_managed_categories(data)` and no longer builds these categories inline.

- [ ] **Step 3: Commit**

```bash
git add docs/plans/backend-architecture-audit-inventory.md docs/plans/current-status.md docs/plans/handoff.md
git commit -m "docs: record alarm threshold category cleanup"
```
