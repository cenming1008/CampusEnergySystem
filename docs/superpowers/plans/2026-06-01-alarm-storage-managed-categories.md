# Alarm Storage Managed Categories Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the storage alarm managed-category mapping out of `AlarmService.check_storage_faults()` into the pure domain alarm rules layer.

**Architecture:** Keep alarm lifecycle and repository orchestration in `app/services/alarm_service.py`. Add a pure function in `app/domain/alarm_rules.py` that maps present storage telemetry fields to managed alarm categories, then let `AlarmService` call that function. This is a single-leak cleanup and must not change alarm API behavior or storage threshold evaluation.

**Tech Stack:** Python, pytest, SQLModel-backed existing alarm service tests, domain pure-function tests.

---

### Task 1: Add RED Test For Storage Managed Categories

**Files:**
- Modify: `tests/test_alarm_rule_profiles.py`

- [ ] **Step 1: Add failing domain test**

Append this test to `tests/test_alarm_rule_profiles.py`:

```python


def test_storage_managed_categories_follow_present_payload_fields():
    from app.domain.alarm_rules import get_storage_managed_categories

    assert get_storage_managed_categories({"soc": 18.0}) == {
        "storage_soc_low",
        "storage_soc_out_of_range",
    }
    assert get_storage_managed_categories({"soh": 79.0, "cell_temp_max": 51.0}) == {
        "storage_soh_low",
        "storage_cell_temp_high",
    }
    assert get_storage_managed_categories({"active_power": -151.0, "soc": None}) == {
        "storage_active_power_out_of_range",
    }
```

- [ ] **Step 2: Run the new test to verify RED**

Run:

```bash
./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py::test_storage_managed_categories_follow_present_payload_fields -q
```

Expected: fail with `ImportError` because `get_storage_managed_categories` does not exist yet.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_alarm_rule_profiles.py
git commit -m "test: capture storage alarm managed categories"
```

### Task 2: Move Storage Managed Categories To Domain

**Files:**
- Modify: `app/domain/alarm_rules.py`
- Modify: `app/services/alarm_service.py`
- Test: `tests/test_alarm_rule_profiles.py`

- [ ] **Step 1: Add domain helper**

In `app/domain/alarm_rules.py`, after `get_capacitor_bank_managed_categories()`, add:

```python


def get_storage_managed_categories(storage_data: dict[str, Any]) -> set[str]:
    """Return storage platform alarm categories managed by present telemetry fields."""
    managed_categories: set[str] = set()
    if storage_data.get("soc") is not None:
        managed_categories.update({"storage_soc_low", "storage_soc_out_of_range"})
    if storage_data.get("soh") is not None:
        managed_categories.add("storage_soh_low")
    if storage_data.get("cell_temp_max") is not None:
        managed_categories.add("storage_cell_temp_high")
    if storage_data.get("active_power") is not None:
        managed_categories.add("storage_active_power_out_of_range")
    return managed_categories
```

- [ ] **Step 2: Update AlarmService to call domain helper**

In `app/services/alarm_service.py`, inside `check_storage_faults()`, replace:

```python
        managed_categories: set[str] = set()
        if storage_data.get("soc") is not None:
            managed_categories.update({"storage_soc_low", "storage_soc_out_of_range"})
        if storage_data.get("soh") is not None:
            managed_categories.add("storage_soh_low")
        if storage_data.get("cell_temp_max") is not None:
            managed_categories.add("storage_cell_temp_high")
        if storage_data.get("active_power") is not None:
            managed_categories.add("storage_active_power_out_of_range")
```

with:

```python
        managed_categories = alarm_rules.get_storage_managed_categories(storage_data)
```

- [ ] **Step 3: Run the new domain test to verify GREEN**

Run:

```bash
./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py::test_storage_managed_categories_follow_present_payload_fields -q
```

Expected: pass with `1 passed`.

- [ ] **Step 4: Run alarm regression tests**

Run:

```bash
./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py tests/test_alarm_service.py -q
```

Expected: pass. Existing urllib3/LibreSSL warnings are acceptable if all tests pass.

- [ ] **Step 5: Commit the domain move**

```bash
git add app/domain/alarm_rules.py app/services/alarm_service.py
git commit -m "refactor: move storage alarm managed categories to domain"
```

### Task 3: Update Audit Status For Alarm Service Slice

**Files:**
- Modify: `docs/plans/backend-architecture-audit-inventory.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Update inventory execution order**

In `docs/plans/backend-architecture-audit-inventory.md`, under `后续建议`, replace:

```markdown
1. `alarm_service.py` 中一个纯规则泄漏点迁入 `domain`。
2. `device_service.py` 中一个 profile/default 归一职责拆出。
3. `campus_service.py` 聚合计算 helper 的可测试性整理。
```

with:

```markdown
1. 已完成：`alarm_service.py` 中 storage managed categories 纯映射已迁入 `domain/alarm_rules.py`。
2. `alarm_service.py` 后续如继续整理，只能再选择一个独立纯规则泄漏点。
3. `device_service.py` 中一个 profile/default 归一职责拆出。
4. `campus_service.py` 聚合计算 helper 的可测试性整理。
```

- [ ] **Step 2: Update current status**

In `docs/plans/current-status.md`, add this checklist item under `## 当前阶段`:

```markdown
- [x] `alarm_service.py` 第一轮纯规则泄漏点已收口：storage managed categories 映射迁入 `domain/alarm_rules.py`。
```

In `## 当前验证结论`, add:

```markdown
- `./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py::test_storage_managed_categories_follow_present_payload_fields -q` 通过。
- `./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py tests/test_alarm_service.py -q` 通过。
```

- [ ] **Step 3: Update handoff**

In `docs/plans/handoff.md`, under `## 阶段结论`, add:

```markdown
- `alarm_service.py` 第一轮纯规则泄漏点已收口：storage managed categories 映射迁入 `domain/alarm_rules.py`，告警生命周期编排仍保留在 service。
```

In `## 剩余风险`, add:

```markdown
- `alarm_service.py` 仍是 `split_candidate`，但本轮只处理 storage managed categories 纯映射；后续继续整理时仍必须一次只选一个独立规则泄漏点。
```

- [ ] **Step 4: Run documentation marker check**

Run:

```bash
rg -n "storage managed categories|domain/alarm_rules.py|test_storage_managed_categories|alarm_service.py" docs/plans/backend-architecture-audit-inventory.md docs/plans/current-status.md docs/plans/handoff.md
```

Expected: inventory, current status, and handoff all mention the alarm service storage managed-category cleanup.

- [ ] **Step 5: Commit documentation updates**

```bash
git add docs/plans/backend-architecture-audit-inventory.md docs/plans/current-status.md docs/plans/handoff.md
git commit -m "docs: record alarm storage category cleanup"
```

### Task 4: Final Verification

**Files:**
- No file changes expected unless verification reveals a problem.

- [ ] **Step 1: Run planned checks**

Run:

```bash
./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py tests/test_alarm_service.py tests/test_backend_architecture_audit_docs.py -q
```

Expected: all tests pass. Existing urllib3/LibreSSL warnings are acceptable if all tests pass.

- [ ] **Step 2: Check service delegates managed categories to domain**

Run:

```bash
rg -n "get_storage_managed_categories|managed_categories: set\\[str\\] = set\\(\\)|storage_soc_low|storage_active_power_out_of_range" app/services/alarm_service.py app/domain/alarm_rules.py
```

Expected: `AlarmService.check_storage_faults()` calls `alarm_rules.get_storage_managed_categories(storage_data)`, and the storage category literals live in `app/domain/alarm_rules.py`.

- [ ] **Step 3: Check git status**

Run:

```bash
git status --short
```

Expected: only unrelated pre-existing untracked files remain. In the current workspace, `.understand-anything/` may remain untracked and should not be touched unless the user explicitly asks.
