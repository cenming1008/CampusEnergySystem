# Device Registry Default Patch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move legacy device registry default-field resolution out of `DeviceService.create_device()` into the device domain helper layer.

**Architecture:** Keep persistence, rollback handling, and duplicate-SN compatibility in `app/services/device_service.py`. Add a pure domain helper in `app/domain/device_payloads.py` that calculates the default field patch for legacy `create_device()` inputs. `DeviceService.create_device()` applies that patch before saving the device.

**Tech Stack:** Python, pytest, existing device domain and device service unit tests.

---

### Task 1: Add RED Test For Device Registry Default Patch

**Files:**
- Modify: `tests/test_device_domain.py`

- [ ] **Step 1: Add failing domain test**

Update the import list in `tests/test_device_domain.py` to include `build_device_registry_default_patch`:

```python
from app.domain.device_payloads import (
    build_device_create_fields,
    build_device_registry_default_patch,
    describe_device_type_semantics,
    describe_energy_data_fields,
    get_device_type_config,
    normalize_device_report_payload,
)
```

Then append this test to `TestDeviceDomainHelpers`:

```python
    def test_build_device_registry_default_patch_normalizes_legacy_compensation_device(self):
        patch = build_device_registry_default_patch(
            device_type="svg",
            device_subtype=None,
            device_category="load",
            energy_type=None,
            unit=None,
            rated_capacity=None,
        )

        self.assertEqual(patch["device_category"], "compensation")
        self.assertEqual(patch["device_subtype"], "svg")
        self.assertEqual(patch["energy_type"], "electricity")
        self.assertEqual(patch["unit"], "kVAR")
        self.assertGreater(patch["rated_capacity"], 0)
```

- [ ] **Step 2: Run the new test to verify RED**

Run:

```bash
./venv/bin/python -m pytest tests/test_device_domain.py::TestDeviceDomainHelpers::test_build_device_registry_default_patch_normalizes_legacy_compensation_device -q
```

Expected: fail with `ImportError` because `build_device_registry_default_patch` does not exist yet.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_device_domain.py
git commit -m "test: capture device registry default patch"
```

### Task 2: Move Registry Default Patch To Domain

**Files:**
- Modify: `app/domain/device_payloads.py`
- Modify: `app/services/device_service.py`
- Test: `tests/test_device_domain.py`

- [ ] **Step 1: Add domain helper**

In `app/domain/device_payloads.py`, after `build_device_create_fields()`, add:

```python


def build_device_registry_default_patch(
    device_type: Optional[str],
    device_subtype: Optional[str] = None,
    device_category: Optional[str] = None,
    energy_type: Optional[str] = None,
    unit: Optional[str] = None,
    rated_capacity: Optional[float] = None,
) -> dict[str, Any]:
    """Build missing legacy Device fields from registry defaults."""
    effective_subtype = resolve_compensation_subtype(device_type, device_subtype)
    effective_type = effective_subtype or normalize_device_type_alias(device_type)
    if not effective_type:
        return {}

    config = device_registry.get(effective_type)
    if not config:
        return {}

    patch: dict[str, Any] = {}
    normalized_category = _normalize_device_category_for_defaults(
        effective_type,
        device_subtype,
        device_category,
    )
    if normalized_category:
        patch["device_category"] = normalized_category
    elif not device_category:
        patch["device_category"] = config.category.value

    if not energy_type:
        patch["energy_type"] = config.energy_type.value
    if not unit:
        patch["unit"] = config.unit
    if not rated_capacity and config.default_capacity:
        patch["rated_capacity"] = config.default_capacity

    compensation_subtype = (
        resolve_compensation_subtype(device_type, device_subtype)
        or resolve_compensation_subtype(effective_type)
    )
    if compensation_subtype and not device_subtype:
        patch["device_subtype"] = compensation_subtype

    return patch


def _normalize_device_category_for_defaults(
    device_type: Optional[str],
    device_subtype: Optional[str],
    current_category: Optional[str],
) -> Optional[str]:
    if not is_compensation_device(device_type, device_subtype, current_category):
        return current_category
    if current_category == DeviceCategory.COMPENSATION.value:
        return current_category
    if current_category in (None, "", DeviceCategory.LOAD.value):
        return DeviceCategory.COMPENSATION.value
    return current_category
```

- [ ] **Step 2: Update DeviceService imports**

In `app/services/device_service.py`, add `build_device_registry_default_patch` to the existing `from app.domain.device_payloads import (...)` list:

```python
    build_device_create_fields,
    build_device_registry_default_patch,
```

- [ ] **Step 3: Update DeviceService.create_device()**

Inside `DeviceService.create_device()`, replace this block:

```python
            # 如果提供了 device_type，尝试自动配置
            if device.device_type:
                effective_type = DeviceService._effective_device_type(device) or device.device_type
                config = device_registry.get(effective_type)
                if config:
                    normalized_category = DeviceService._normalize_device_category(
                        effective_type,
                        getattr(device, "device_subtype", None),
                        device.device_category,
                    )
                    # 自动填充未设置的字段
                    if normalized_category:
                        device.device_category = normalized_category
                    elif not device.device_category:
                        device.device_category = config.category.value
                    if not device.energy_type:
                        device.energy_type = config.energy_type.value
                    if not device.unit:
                        device.unit = config.unit
                    if not device.rated_capacity and config.default_capacity:
                        device.rated_capacity = config.default_capacity
                    compensation_subtype = resolve_compensation_subtype(
                        getattr(device, "device_type", None),
                        getattr(device, "device_subtype", None),
                    ) or resolve_compensation_subtype(effective_type)
                    if compensation_subtype and not getattr(device, "device_subtype", None):
                        device.device_subtype = compensation_subtype
```

with:

```python
            # 如果提供了 device_type，尝试自动配置
            if device.device_type:
                default_patch = build_device_registry_default_patch(
                    device_type=getattr(device, "device_type", None),
                    device_subtype=getattr(device, "device_subtype", None),
                    device_category=getattr(device, "device_category", None),
                    energy_type=getattr(device, "energy_type", None),
                    unit=getattr(device, "unit", None),
                    rated_capacity=getattr(device, "rated_capacity", None),
                )
                for field_name, value in default_patch.items():
                    setattr(device, field_name, value)
```

- [ ] **Step 4: Remove unused service import**

If `app/services/device_service.py` no longer uses `device_registry`, remove this import:

```python
from app.core.device_registry import device_registry
```

- [ ] **Step 5: Run the new domain test to verify GREEN**

Run:

```bash
./venv/bin/python -m pytest tests/test_device_domain.py::TestDeviceDomainHelpers::test_build_device_registry_default_patch_normalizes_legacy_compensation_device -q
```

Expected: pass with `1 passed`.

- [ ] **Step 6: Run device regression tests**

Run:

```bash
./venv/bin/python -m pytest tests/test_device_domain.py tests/test_device_service_round2.py tests/test_device_management_use_cases.py -q
```

Expected: pass. Existing urllib3/LibreSSL warnings are acceptable if all tests pass.

- [ ] **Step 7: Commit the domain move**

```bash
git add app/domain/device_payloads.py app/services/device_service.py
git commit -m "refactor: move device registry defaults to domain"
```

### Task 3: Update Audit Status For Device Service Slice

**Files:**
- Modify: `docs/plans/backend-architecture-audit-inventory.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Update inventory execution order**

In `docs/plans/backend-architecture-audit-inventory.md`, under `后续建议`, replace:

```markdown
3. `device_service.py` 中一个 profile/default 归一职责拆出。
4. `campus_service.py` 聚合计算 helper 的可测试性整理。
```

with:

```markdown
3. 已完成：`device_service.py` 中 legacy create registry defaults patch 已迁入 `domain/device_payloads.py`。
4. `device_service.py` 后续如继续整理，只能再选择一个独立 profile/default 泄漏点。
5. `campus_service.py` 聚合计算 helper 的可测试性整理。
```

- [ ] **Step 2: Update current status**

In `docs/plans/current-status.md`, add this checklist item under `## 当前阶段`:

```markdown
- [x] `device_service.py` 第一轮 profile/default 泄漏点已收口：legacy create registry defaults patch 迁入 `domain/device_payloads.py`。
```

In `## 当前验证结论`, add:

```markdown
- `./venv/bin/python -m pytest tests/test_device_domain.py::TestDeviceDomainHelpers::test_build_device_registry_default_patch_normalizes_legacy_compensation_device -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_domain.py tests/test_device_service_round2.py tests/test_device_management_use_cases.py -q` 通过。
```

- [ ] **Step 3: Update handoff**

In `docs/plans/handoff.md`, under `## 阶段结论`, add:

```markdown
- `device_service.py` 第一轮 profile/default 泄漏点已收口：legacy create registry defaults patch 迁入 `domain/device_payloads.py`，持久化、回滚和重复 SN 兼容仍保留在 service。
```

In `## 剩余风险`, add:

```markdown
- `device_service.py` 仍是 `split_candidate`，但本轮只处理 legacy create registry defaults patch；后续继续整理时仍必须一次只选一个独立 profile/default 泄漏点。
```

- [ ] **Step 4: Run documentation marker check**

Run:

```bash
rg -n "registry defaults patch|domain/device_payloads.py|test_build_device_registry_default_patch|device_service.py" docs/plans/backend-architecture-audit-inventory.md docs/plans/current-status.md docs/plans/handoff.md
```

Expected: inventory, current status, and handoff all mention the device service registry default patch cleanup.

- [ ] **Step 5: Commit documentation updates**

```bash
git add docs/plans/backend-architecture-audit-inventory.md docs/plans/current-status.md docs/plans/handoff.md
git commit -m "docs: record device registry default cleanup"
```

### Task 4: Final Verification

**Files:**
- No file changes expected unless verification reveals a problem.

- [ ] **Step 1: Run planned checks**

Run:

```bash
./venv/bin/python -m pytest tests/test_device_domain.py tests/test_device_service_round2.py tests/test_device_management_use_cases.py tests/test_backend_architecture_audit_docs.py -q
```

Expected: all tests pass. Existing urllib3/LibreSSL warnings are acceptable if all tests pass.

- [ ] **Step 2: Check DeviceService delegates registry defaults to domain**

Run:

```bash
rg -n "build_device_registry_default_patch|device_registry\\.get|default_patch|config.default_capacity" app/services/device_service.py app/domain/device_payloads.py
```

Expected: `DeviceService.create_device()` calls `build_device_registry_default_patch(...)`; registry/default-capacity details live in `app/domain/device_payloads.py`.

- [ ] **Step 3: Check git status**

Run:

```bash
git status --short
```

Expected: only unrelated pre-existing untracked files remain. In the current workspace, `.understand-anything/` may remain untracked and should not be touched unless the user explicitly asks.
