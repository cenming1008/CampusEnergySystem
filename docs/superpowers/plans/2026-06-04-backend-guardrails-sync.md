# Backend Guardrails Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Synchronize backend architecture docs and add lightweight tests that keep backend layer rules executable.

**Architecture:** Keep `docs/guides/backend-guidelines.md` as the single backend rulebook. Update reader-facing docs and audit inventory, then add pytest guardrails for documentation freshness and domain-layer dependency direction.

**Tech Stack:** Python, pytest, pathlib text scans.

---

### Task 1: Add Documentation Freshness Tests

**Files:**
- Modify: `tests/test_backend_architecture_audit_docs.py`

- [ ] **Step 1: Add README endpoint layout test**

Add:

```python
def test_app_readme_describes_current_endpoint_layout():
    content = read_doc("app/README.md")

    assert "`ingestion_health.py` | 设备接入健康" in content
    assert "`health.py` | 单设备与概览维度的 MQTT 接入健康状态。" not in content
    assert "`schemas.py` | 能源与碳相关请求/响应模型。" in content
    assert "`constants.py` | 能源与碳相关常量。" in content
    assert "`serializers.py` | 能源与碳相关轻量转换函数。" in content
    assert "`shared.py` | 能源与碳相关请求/响应模型及字段提取工具。" not in content
```

- [ ] **Step 2: Add inventory latest compensation slice test**

Add:

```python
def test_backend_architecture_inventory_records_latest_compensation_svg_payload_slice():
    content = read_doc("docs/plans/backend-architecture-audit-inventory.md")

    assert "SVG payload metric 来源判断" in content
    assert "build_svg_monitor_payload_parts" in content
```

- [ ] **Step 3: Run tests and verify RED**

Run:

```bash
./venv/bin/python -m pytest tests/test_backend_architecture_audit_docs.py::test_app_readme_describes_current_endpoint_layout tests/test_backend_architecture_audit_docs.py::test_backend_architecture_inventory_records_latest_compensation_svg_payload_slice -q
```

Expected: FAIL because README and inventory are stale.

### Task 2: Add Domain Import Boundary Test

**Files:**
- Create: `tests/test_backend_layer_boundaries.py`

- [ ] **Step 1: Add domain import scanner**

Create:

```python
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def iter_python_files(relative_dir: str):
    return sorted((ROOT / relative_dir).glob("*.py"))


def imported_module_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_domain_layer_does_not_import_outer_layers():
    forbidden_prefixes = (
        "app.api",
        "app.application",
        "app.services",
        "app.integrations",
    )
    violations: list[str] = []

    for path in iter_python_files("app/domain"):
        for module in imported_module_names(path):
            if module.startswith(forbidden_prefixes):
                violations.append(f"{path.relative_to(ROOT)} imports {module}")

    assert violations == []
```

- [ ] **Step 2: Run test and verify result**

Run:

```bash
./venv/bin/python -m pytest tests/test_backend_layer_boundaries.py -q
```

Expected: PASS if current domain boundaries are clean.

### Task 3: Sync README and Inventory

**Files:**
- Modify: `app/README.md`
- Modify: `docs/plans/backend-architecture-audit-inventory.md`

- [ ] **Step 1: Update app README endpoint tables**

Update `api/endpoints/devices/` so it lists `ingestion_health.py`, `monitoring.py`, compensation child routers, `schemas.py`, and `serializers.py` instead of stale `health.py` / `shared.py`.

Update `api/endpoints/energy/` so it lists `schemas.py`, `constants.py`, and `serializers.py`, and makes `shared.py` clearly a compatibility export only.

- [ ] **Step 2: Update inventory compensation monitor section**

Add completed item:

```markdown
39. 已完成：`app/services/devices/compensation/monitor_service.py` 中 SVG payload metric 来源判断已迁入 `domain/compensation_rules.py`，service 仅抽取 telemetry/profile/realtime/device 基础值并调用 `build_svg_monitor_payload_parts`。
40. `app/services/devices/compensation/monitor_service.py` 后续如继续整理，需重新选择新的独立泄漏点；控制命令相关逻辑保持 `plan_required` 边界。
```

- [ ] **Step 3: Run documentation tests and verify GREEN**

Run:

```bash
./venv/bin/python -m pytest tests/test_backend_architecture_audit_docs.py -q
```

Expected: PASS.

### Task 4: Final Verification

**Files:**
- Verify only.

- [ ] **Step 1: Run focused final verification**

Run:

```bash
./venv/bin/python -m pytest tests/test_backend_architecture_audit_docs.py tests/test_backend_layer_boundaries.py -q
```

Expected: PASS.

- [ ] **Step 2: Inspect git status and diff**

Run:

```bash
git status --short
git diff --stat
```

Expected: changes limited to README, inventory, tests, and this plan.
