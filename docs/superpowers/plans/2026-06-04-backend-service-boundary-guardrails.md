# Backend Service Boundary Guardrails Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent service-layer reverse imports and remove the current `DeviceMonitorService` -> `application` dependency.

**Architecture:** `application/device_monitoring.py` keeps access control and delegates to `DeviceMonitorService.get_monitor_overview(...)`. `DeviceMonitorService` owns monitor overview aggregation. A lightweight AST test protects service modules from importing `app.api` or `app.application`.

**Tech Stack:** Python, pytest, AST import scanning.

---

### Task 1: Extend Layer Boundary Test

**Files:**
- Modify: `tests/test_backend_layer_boundaries.py`

- [ ] **Step 1: Add recursive file iterator**

Change:

```python
def iter_python_files(relative_dir: str):
    return sorted((ROOT / relative_dir).glob("*.py"))
```

to:

```python
def iter_python_files(relative_dir: str, *, recursive: bool = False):
    root = ROOT / relative_dir
    pattern = "**/*.py" if recursive else "*.py"
    return sorted(root.glob(pattern))
```

- [ ] **Step 2: Add service reverse dependency test**

Add:

```python
def test_service_layer_does_not_import_api_or_application_layers():
    forbidden_prefixes = (
        "app.api",
        "app.application",
    )
    violations: list[str] = []

    for path in iter_python_files("app/services", recursive=True):
        for module in imported_module_names(path):
            if module.startswith(forbidden_prefixes):
                violations.append(f"{path.relative_to(ROOT)} imports {module}")

    assert violations == []
```

- [ ] **Step 3: Run boundary test and verify RED**

Run:

```bash
./venv/bin/python -m pytest tests/test_backend_layer_boundaries.py::test_service_layer_does_not_import_api_or_application_layers -q
```

Expected: FAIL with `app/services/device_monitor_service.py imports app.application.device_monitoring`.

### Task 2: Move Overview Aggregation Back To Service

**Files:**
- Modify: `app/services/device_monitor_service.py`
- Modify: `app/application/device_monitoring.py`

- [ ] **Step 1: Add monitor support imports to service**

In `app/services/device_monitor_service.py`, add:

```python
from app.services.devices.monitor_plugin_registry import DeviceMonitorContext, DeviceMonitorPluginRegistry
from app.services.devices.monitor_template_service import MonitorTemplateService
```

- [ ] **Step 2: Replace `get_monitor_overview` implementation**

Replace the method body with the aggregation logic currently in `get_device_monitor_overview_use_case(...)`, excluding access control.

- [ ] **Step 3: Simplify application use case**

Change `get_device_monitor_overview_use_case(...)` so it:

```python
    if current_user is not None:
        ensure_device_access(session, current_user, device_id)

    from app.services.device_monitor_service import DeviceMonitorService

    return DeviceMonitorService.get_monitor_overview(session, device_id)
```

- [ ] **Step 4: Run boundary test and verify GREEN**

Run:

```bash
./venv/bin/python -m pytest tests/test_backend_layer_boundaries.py -q
```

Expected: PASS.

### Task 3: Update Application README

**Files:**
- Modify: `app/application/README.md`

- [ ] **Step 1: Replace compatibility wrapper wording**

Update references that say `DeviceMonitorService.get_monitor_overview(...)` is a wrapper around application. It should say the service owns monitor aggregation and the application use case adds access control before delegating.

### Task 4: Verification And Handoff

**Files:**
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`
- Modify: `docs/plans/daily/2026-06/2026-06-04-status.md`
- Modify: `docs/plans/daily/2026-06/2026-06-04-handoff.md`

- [ ] **Step 1: Run focused verification**

Run:

```bash
./venv/bin/python -m pytest tests/test_backend_layer_boundaries.py tests/test_device_monitor_service.py tests/test_endpoint_application_convergence.py::DeviceMonitoringEndpointConvergenceTest -q
```

Expected: PASS.

- [ ] **Step 2: Record handoff**

Document that service-layer reverse import guardrail is in place and `DeviceMonitorService.get_monitor_overview()` now owns aggregation while application keeps access control.
