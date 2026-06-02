# Device Category Normalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move compensation device category normalization into `app/domain/device_payloads.py` so `DeviceService` does not own duplicated pure rules.

**Architecture:** `DeviceService` should keep object-copying and repository orchestration. The decision that SVG / capacitor-bank / legacy compensator devices should expose `device_category="compensation"` is domain identity logic and should be reused by both registry-default patching and service read normalization.

**Tech Stack:** Python, pytest/unittest.

---

### Task 1: Capture Public Domain Category Normalization

**Files:**
- Modify: `tests/test_device_domain.py`

- [ ] **Step 1: Write the failing test**

Add `normalize_device_category` to the import list and append this test to `TestDeviceDomainHelpers`:

```python
    def test_normalize_device_category_maps_legacy_compensation_load(self):
        self.assertEqual(
            normalize_device_category(
                device_type="reactive_power_compensator",
                device_subtype=None,
                current_category="load",
            ),
            "compensation",
        )
        self.assertEqual(
            normalize_device_category(
                device_type="water_meter",
                device_subtype=None,
                current_category="water_meter",
            ),
            "water_meter",
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
./venv/bin/python -m pytest tests/test_device_domain.py::TestDeviceDomainHelpers::test_normalize_device_category_maps_legacy_compensation_load -q
```

Expected: FAIL with `ImportError` because `normalize_device_category` is not public yet.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/plans/2026-06-02-device-category-normalization.md tests/test_device_domain.py
git commit -m "test: capture device category normalization"
```

### Task 2: Move Category Normalization Rule to Domain

**Files:**
- Modify: `app/domain/device_payloads.py`
- Modify: `app/services/device_service.py`

- [ ] **Step 1: Add public helper in domain**

Replace `_normalize_device_category_for_defaults` with:

```python
def normalize_device_category(
    device_type: Optional[str],
    device_subtype: Optional[str],
    current_category: Optional[str],
) -> Optional[str]:
    """Normalize legacy compensation devices to the public compensation category."""
    if not is_compensation_device(device_type, device_subtype, current_category):
        return current_category
    if current_category == DeviceCategory.COMPENSATION.value:
        return current_category
    if current_category in (None, "", DeviceCategory.LOAD.value):
        return DeviceCategory.COMPENSATION.value
    return current_category
```

Update `build_device_registry_default_patch` to call `normalize_device_category(...)`.

- [ ] **Step 2: Reuse helper in service**

Import `normalize_device_category` in `app/services/device_service.py` and replace `DeviceService._normalize_device_category(...)` usage with:

```python
        normalized_category = normalize_device_category(
            getattr(device, "device_type", None),
            getattr(device, "device_subtype", None),
            getattr(device, "device_category", None),
        )
```

Remove the private `DeviceService._normalize_device_category` method.

- [ ] **Step 3: Run focused tests**

Run:

```bash
./venv/bin/python -m pytest tests/test_device_domain.py::TestDeviceDomainHelpers::test_normalize_device_category_maps_legacy_compensation_load -q
```

Expected: PASS.

Run:

```bash
./venv/bin/python -m pytest tests/test_device_domain.py tests/test_device_service_round2.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add app/domain/device_payloads.py app/services/device_service.py tests/test_device_domain.py
git commit -m "refactor: move device category normalization to domain"
```

### Task 3: Record Architecture Cleanup

**Files:**
- Modify: `docs/plans/backend-architecture-audit-inventory.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Update architecture docs**

Record that `device_service.py` no longer owns the pure compensation category normalization rule. Keep remaining device service work scoped to object-copying, persistence, statistics delegation, or profile/default orchestration.

- [ ] **Step 2: Run verification**

Run:

```bash
./venv/bin/python -m pytest tests/test_device_domain.py tests/test_device_service_round2.py tests/test_backend_architecture_audit_docs.py -q
```

Expected: PASS.

Run:

```bash
rg -n "_normalize_device_category|normalize_device_category" app/services/device_service.py app/domain/device_payloads.py tests/test_device_domain.py
```

Expected: no private `DeviceService._normalize_device_category`; service imports and calls `normalize_device_category`.

- [ ] **Step 3: Commit**

```bash
git add docs/plans/backend-architecture-audit-inventory.md docs/plans/current-status.md docs/plans/handoff.md
git commit -m "docs: record device category normalization cleanup"
```
