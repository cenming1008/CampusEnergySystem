# Compensation Monitor SVG Payload Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move SVG compensation monitor payload calculation out of `CompensationMonitorService` and into pure domain rules.

**Architecture:** Add `build_svg_monitor_payload_parts(...)` to `app/domain/compensation_rules.py`. Keep DB queries, SVG profile lookup, control mode resolution, capabilities lookup, and final monitor dict assembly in `app/services/devices/compensation/monitor_service.py`.

**Tech Stack:** Python, pytest, SQLModel test fixtures.

---

### Task 1: Add SVG Monitor Domain Rule Test

**Files:**
- Modify: `tests/test_compensation_domain.py`

- [ ] **Step 1: Import the new helper**

Add `build_svg_monitor_payload_parts` to the import list from `app.domain.compensation_rules`.

- [ ] **Step 2: Write the failing telemetry/profile behavior test**

Add this test near `test_resolve_svg_control_mode_preserves_telemetry_and_placeholder_payloads`:

```python
def test_build_svg_monitor_payload_parts_uses_telemetry_and_profile_counts():
    parts = build_svg_monitor_payload_parts(
        capacity_utilization=40.0,
        profile_module_count=10,
        rated_capacity=150.0,
        reactive_power=30.0,
        cabinet_temperature=36.5,
        realtime_temperature=32.0,
    )

    assert parts["capacity_utilization_metric"] == {
        "value": 40.0,
        "source": "telemetry",
        "state": "live",
    }
    assert parts["circuit_summary"] == {
        "running_count": 4,
        "total_count": 10,
        "has_realtime_state": True,
        "source": "telemetry",
        "state": "live",
    }
    assert parts["compensation_level_metric"] == {
        "value": 4,
        "source": "telemetry",
        "state": "live",
    }
    assert parts["cabinet_temperature_metric"] == {
        "value": 36.5,
        "source": "telemetry",
        "state": "live",
    }
```

- [ ] **Step 3: Write fallback and missing behavior tests**

Add these tests:

```python
def test_build_svg_monitor_payload_parts_estimates_capacity_from_reactive_power():
    parts = build_svg_monitor_payload_parts(
        capacity_utilization=None,
        profile_module_count=8,
        rated_capacity=200.0,
        reactive_power=-50.0,
        cabinet_temperature=None,
        realtime_temperature=31.2,
    )

    assert parts["capacity_utilization_metric"] == {
        "value": 25.0,
        "source": "estimated",
        "state": "mock",
    }
    assert parts["circuit_summary"] == {
        "running_count": 2,
        "total_count": 8,
        "has_realtime_state": True,
        "source": "estimated",
        "state": "mock",
    }
    assert parts["cabinet_temperature_metric"] == {
        "value": 31.2,
        "source": "realtime",
        "state": "live",
    }


def test_build_svg_monitor_payload_parts_marks_missing_capacity_and_temperature():
    parts = build_svg_monitor_payload_parts(
        capacity_utilization=None,
        profile_module_count=0,
        rated_capacity=0.0,
        reactive_power=None,
        cabinet_temperature=None,
        realtime_temperature=None,
    )

    assert parts["capacity_utilization_metric"] == {
        "value": None,
        "source": "missing",
        "state": "missing",
    }
    assert parts["circuit_summary"] == {
        "running_count": None,
        "total_count": None,
        "has_realtime_state": False,
        "source": "missing",
        "state": "missing",
    }
    assert parts["compensation_level_metric"] == {
        "value": None,
        "source": "missing",
        "state": "missing",
    }
    assert parts["cabinet_temperature_metric"] == {
        "value": None,
        "source": "missing",
        "state": "missing",
    }
```

- [ ] **Step 4: Run the focused test and verify RED**

Run:

```bash
./venv/bin/python -m pytest tests/test_compensation_domain.py::test_build_svg_monitor_payload_parts_uses_telemetry_and_profile_counts -q
```

Expected: FAIL because `build_svg_monitor_payload_parts` does not exist.

### Task 2: Implement Pure Domain Helper

**Files:**
- Modify: `app/domain/compensation_rules.py`

- [ ] **Step 1: Add a reusable metric helper**

Add:

```python
def build_monitor_metric(value: Any, *, source: str, state: str) -> dict[str, Any]:
    return {
        "value": value,
        "source": source,
        "state": state,
    }
```

- [ ] **Step 2: Add SVG payload helper**

Add:

```python
def build_svg_monitor_payload_parts(
    *,
    capacity_utilization: Any,
    profile_module_count: Any,
    rated_capacity: Any,
    reactive_power: Any,
    cabinet_temperature: Any,
    realtime_temperature: Any,
) -> dict[str, Any]:
    total_count = int(profile_module_count or 0)
    total_count = total_count if total_count > 0 else None

    resolved_capacity = optional_float(capacity_utilization)
    capacity_source = "telemetry"
    capacity_state = "live"
    if resolved_capacity is None:
        normalized_rated_capacity = optional_float(rated_capacity) or 0.0
        normalized_reactive_power = optional_float(reactive_power)
        if normalized_rated_capacity > 0 and normalized_reactive_power is not None:
            resolved_capacity = round(
                min(100.0, max(0.0, (abs(normalized_reactive_power) / normalized_rated_capacity) * 100.0)),
                1,
            )
            capacity_source = "estimated"
            capacity_state = "mock"
        else:
            capacity_source = "missing"
            capacity_state = "missing"

    running_count = None
    circuit_source = "profile" if total_count is not None else "missing"
    circuit_state = "live" if total_count is not None else "missing"
    if resolved_capacity is not None and total_count is not None:
        running_count = max(0, min(total_count, round((float(resolved_capacity) / 100.0) * total_count)))
        circuit_source = capacity_source
        circuit_state = "live" if capacity_state == "live" else "mock"

    resolved_temperature = optional_float(cabinet_temperature)
    temperature_source = "telemetry" if resolved_temperature is not None else "realtime"
    temperature_state = "live" if resolved_temperature is not None else "missing"
    if resolved_temperature is None:
        resolved_temperature = optional_float(realtime_temperature)
        if resolved_temperature is not None:
            temperature_state = "live"
        else:
            temperature_source = "missing"

    return {
        "capacity_utilization_metric": build_monitor_metric(
            resolved_capacity,
            source=capacity_source,
            state=capacity_state,
        ),
        "cabinet_temperature_metric": build_monitor_metric(
            resolved_temperature,
            source=temperature_source,
            state=temperature_state,
        ),
        "compensation_level_metric": build_monitor_metric(
            running_count,
            source=circuit_source,
            state=circuit_state,
        ),
        "circuit_summary": {
            "running_count": running_count,
            "total_count": total_count,
            "has_realtime_state": resolved_capacity is not None and total_count is not None,
            "source": circuit_source,
            "state": circuit_state,
        },
    }
```

- [ ] **Step 3: Run domain tests and verify GREEN**

Run:

```bash
./venv/bin/python -m pytest tests/test_compensation_domain.py -q
```

Expected: PASS.

### Task 3: Use Domain Helper in Service

**Files:**
- Modify: `app/services/devices/compensation/monitor_service.py`

- [ ] **Step 1: Import helper**

Add `build_svg_monitor_payload_parts` to the `from app.domain.compensation_rules import (...)` list.

- [ ] **Step 2: Replace inline SVG payload calculations**

Inside `_build_svg_monitor()`, replace the inline capacity, circuit and cabinet temperature calculation block with:

```python
        svg_payload_parts = build_svg_monitor_payload_parts(
            capacity_utilization=getattr(telemetry, "capacity_utilization", None),
            profile_module_count=getattr(profile, "module_count", 0),
            rated_capacity=getattr(device, "rated_capacity", None),
            reactive_power=realtime.get("reactive_power"),
            cabinet_temperature=getattr(telemetry, "cabinet_temp", None),
            realtime_temperature=realtime.get("temperature"),
        )
```

Use `svg_payload_parts["circuit_summary"]` and `svg_payload_parts["*_metric"]` in the returned dict.

- [ ] **Step 3: Run service boundary tests**

Run:

```bash
./venv/bin/python -m pytest tests/test_compensation_monitor_service_boundary.py -q
```

Expected: PASS.

### Task 4: Update Theme Handoff Docs

**Files:**
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Add current status checklist item**

Add:

```markdown
- [x] `app/services/devices/compensation/monitor_service.py` 第八轮 SVG payload 泄漏点已收口：SVG 容量利用率、回路摘要和柜温 metric 来源判断迁入 `domain/compensation_rules.py`。
```

- [ ] **Step 2: Add handoff phase conclusion**

Add:

```markdown
- `app/services/devices/compensation/monitor_service.py` 第八轮 SVG payload 泄漏点已收口：SVG 容量利用率、回路摘要和柜温 metric 来源判断迁入 `domain/compensation_rules.py`，SVG telemetry/profile 查询、控制模式解析调用和最终 monitor 响应装配仍保留在 service。
```

- [ ] **Step 3: Add verification lines**

Add the final verification command:

```markdown
- `./venv/bin/python -m pytest tests/test_compensation_domain.py tests/test_compensation_monitor_service_boundary.py -q` 通过。
```

### Task 5: Final Verification

**Files:**
- Verify only.

- [ ] **Step 1: Run final verification**

Run:

```bash
./venv/bin/python -m pytest tests/test_compensation_domain.py tests/test_compensation_monitor_service_boundary.py -q
```

Expected: PASS.

- [ ] **Step 2: Inspect diff**

Run:

```bash
git diff -- app/domain/compensation_rules.py app/services/devices/compensation/monitor_service.py tests/test_compensation_domain.py docs/plans/current-status.md docs/plans/handoff.md docs/superpowers/plans/2026-06-04-compensation-monitor-svg-payload.md
```

Expected: diff only covers SVG payload rule extraction, tests, handoff docs, and this plan.
