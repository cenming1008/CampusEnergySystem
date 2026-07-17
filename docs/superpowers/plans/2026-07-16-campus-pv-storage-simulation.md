# Campus PV-Storage Simulation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the existing storage device path into one replaceable-source EMS: the simulator drives the original storage APIs and pages now, and a future vendor gateway replaces only the adapter.

**Architecture:** Maintain one storage device model, persistence path, service layer, API family, and original `StorageMonitorView`. Both the simulator and a future vendor gateway implement the same canonical MQTT contract; system-level PV-storage analytics are added as a `光储 EMS` workspace inside the existing `EnergyManagement` page, not as a parallel route. Pure battery, rule, and dispatch mathematics remain focused domain modules while services orchestrate persistence, control, scheduling, permissions, and safe simulated-to-real cutover.

**Tech Stack:** Python 3.10+, FastAPI, SQLModel, Alembic, APScheduler, paho-mqtt, PuLP/CBC, PostgreSQL/TimescaleDB, Redis, Vue 3, TypeScript, Pinia, Element Plus, ECharts, pytest, Vitest.

---

## Convergence source of truth

This plan implements `docs/superpowers/specs/2026-07-17-single-storage-system-convergence-design.md`. It supersedes earlier plan wording that implied a separate simulated storage business system, a simulated-device page, or a standalone `/storage-energy` route. Tasks 1-5 remain completed and are not reimplemented; Tasks 6-15 extend the existing storage system only. 园区级光储分析统一放入现有“能耗分析”页面，设备级能力统一保留在原储能设备页面。

## Execution prerequisites

1. Do not start production-code tasks while `docs/plans/current-status.md` still names backend reliability phase 2A as the active main theme unless the rules role explicitly pauses or closes it.
2. Phase 2A is accepted and Task 3 has persistence admission. Its migration revision is `20260716_0002` with `down_revision = "20260716_0001"`; do not attach storage persistence to the archived legacy chain.
3. Preserve the existing user-owned `app/api/README.md` modification in the original `main` worktree.
4. Baseline evidence in the isolated worktree:
   - backend: `580 passed, 3 warnings`;
   - frontend: `355 passed, 4 failed` in existing `EnergyManagement.test.ts` and `DeviceTrendPanel.test.ts` cases. These four failures are recorded as pre-existing and are not success criteria for storage work; all new storage tests must pass, and no additional failures may be introduced.
5. Every simulated payload must include `data_source=simulated`. Never present simulator output as real hardware telemetry.

Use this reproducible shell environment for every Python and migration command in this plan:

```bash
export PATH=/Users/todo/CampusEnergySystem/venv/bin:$PATH
export DATABASE_URL=postgresql://admin:password123@localhost:5432/campus_energy
export MIGRATION_ADMIN_URL=postgresql://admin:password123@localhost:5432/postgres
```

After this preflight, invoke the shared virtual environment as `python`; do not assume that the isolated worktree contains its own `./venv` directory.

## Milestones

- **Milestone A — Simulated telemetry:** Tasks 1-5 produce a storage simulator that publishes realistic telemetry into the existing monitor path.
- **Milestone B — Closed-loop control:** Tasks 6-10 produce command, receipt, safety, rule-control, and device-workbench behavior.
- **Milestone C — Optimization and evidence:** Tasks 11-15 produce day-ahead dispatch, PV-storage overview, comparison reports, and a repeatable demo.

## File structure map

### Domain and models

- Create `app/domain/storage_simulation.py`: pure battery state transition and available-power calculations.
- Create `app/domain/storage_control_rules.py`: pure safety and real-time rule decision logic.
- Create `app/domain/storage_dispatch_optimizer.py`: pure 96-slot MILP formulation and result conversion.
- Modify `app/models/storage.py`: storage asset profile, telemetry extensions, dispatch plan records.
- Create `migrations/versions/20260716_0002_add_storage_simulation_contracts.py`: deterministic schema changes after the accepted `20260716_0001` root baseline.
- Create `migrations/versions/20260717_0003_add_storage_source_and_control_gates.py`: additive per-device automatic-control gate and dispatch source markers after `20260716_0002`.

### Backend orchestration

- Modify `app/integrations/mqtt/device_extensions.py`: persist new storage telemetry fields.
- Create `app/services/devices/storage/asset_profile_service.py`: storage profile reads and writes.
- Create `app/services/devices/storage/control_command_service.py`: storage command lifecycle.
- Create `app/services/devices/storage/ems_service.py`: safety-first rule execution and plan tracking.
- Create `app/services/devices/storage/dispatch_service.py`: optimizer invocation and plan persistence.
- Create `app/services/devices/storage/simulation_cutover_service.py`: preview and delete one device's simulated business data without touching its archive or real data.
- Modify `app/services/devices/storage/monitor_service.py`: expose plan, command, component, and source metrics.
- Create `app/integrations/mqtt/control_receipts.py`: category-aware receipt dispatch.
- Modify `app/integrations/mqtt/processor.py`: route control receipts through the category-aware dispatcher.
- Create `app/api/endpoints/devices/storage_schemas.py`: device-level request/response contracts.
- Modify `app/api/endpoints/devices/storage.py`: asset, command, plan, and scenario endpoints.
- Create `app/services/storage_energy_service.py`: system-level PV-storage overview and comparison aggregation.
- Create `app/api/endpoints/energy/storage.py`: energy-domain overview and comparison endpoints.
- Modify `app/api/endpoints/energy/__init__.py`: register storage energy routes.
- Modify `app/services/scheduler_jobs.py` and `app/services/scheduler_registry.py`: timeout, rule, and daily dispatch jobs.
- Modify `app/core/settings.py`, `env.example`, `env.local.example`, and `env.prod.example`: default-off simulation and automatic-control gates.

### Simulator and dependencies

- Create `scripts/python/storage_simulator.py`: reusable MQTT simulator CLI.
- Modify `scripts/python/README.md`: simulator command and data-source warning.
- Modify `requirements.txt` and `constraints-ci.txt`: pinned PuLP dependency.

### Frontend

- Modify `frontend/src/api/storage.ts`: telemetry extensions and control/plan APIs.
- Modify `frontend/src/features/device-monitor/composables/useStorageMonitor.ts`: control and plan state.
- Create `frontend/src/features/device-monitor/components/storage/StorageControlPanel.vue`: manual/auto controls and receipt state.
- Create `frontend/src/features/device-monitor/components/storage/StorageCommandTimeline.vue`: command lifecycle.
- Modify `frontend/src/features/device-monitor/views/StorageMonitorView.vue`: compose new storage panels.
- Create `frontend/src/api/storageEnergy.ts`: system-level overview APIs consumed by the existing energy page.
- Create `frontend/src/features/energy-management/storage-ems/StorageEmsWorkspace.vue`: energy-flow, trends, dispatch, scenario, and comparison workspace.
- Create focused components and `useStorageEms.ts` under `frontend/src/features/energy-management/storage-ems/`.
- Modify `frontend/src/views/EnergyManagement.vue`: add the `光储 EMS` workspace switch without a new route or menu entry.

### Tests and documentation

- Create focused backend tests named in each task.
- Create focused frontend tests beside each new component/composable.
- Create `tests/test_storage_simulator_e2e.py`: deterministic end-to-end simulation acceptance.
- Create `tests/test_storage_simulation_cutover.py`: exact-device preview and deletion acceptance.
- Create `scripts/python/storage_cutover.py`: explicit preview/execute simulated-data cutover entrypoint.
- Create `docs/guides/storage-simulation-demo.md`: five-minute demo and result interpretation.
- Update `README.md` only after the demo entrypoint is stable.

## Task 1: Establish theme governance and migration gate

**Files:**
- Create: `docs/plans/PLAN-20260716-campus-pv-storage-simulation.md`
- Modify only after rules-role approval: `docs/plans/current-status.md`
- Modify only after rules-role approval: `docs/plans/handoff.md`
- Read/Test: `docs/plans/backend-reliability-phase2-inventory.md`
- Test: `tests/test_backend_tooling_contracts.py`

- [x] **Step 1: Write the formal topic plan**

Create the topic plan with these fixed sections and decisions:

```markdown
# PLAN-20260716 园区光储协同仿真与 EMS 控制

## 目标
- 完成系统级储能仿真、MQTT 遥测、控制回执、规则 EMS、日前优化和收益对比。

## 前置门禁
- 后端可靠性阶段 2A 已通过或已由规则角色明确暂停并归档。
- offline SQL、fresh PostgreSQL 和两类 existing database migration 路径均通过。

## 非目标
- 不实现电化学、PCS 底层控制、配电网潮流或真实厂商协议。

## 固定契约
- device_category=storage
- device_subtype=battery_energy_storage_system
- 正功率充电，负功率放电。
- 仿真数据必须标记 data_source=simulated。

## 验收阶段
- A：仿真遥测
- B：控制与规则闭环
- C：日前优化与收益证据
```

- [x] **Step 2: Verify the migration prerequisite**

Run:

```bash
python -m pytest -q tests/test_backend_tooling_contracts.py
alembic upgrade head --sql
```

Expected before feature implementation: both commands exit `0`; offline SQL contains the accepted root revision `20260716_0001` and does not perform online database reads. Also run the fresh PostgreSQL, offline, and roundtrip acceptance commands established by the approved phase 2A plan; all three must pass with schema comparison enabled. Phase 2A has now supplied and passed those fixtures, so Task 3 has persistence admission.

- [x] **Step 3: Stop if the gate is not green**

If either command fails, do not edit models or migrations. Record the exact failing revision in the active backend reliability plan and return ownership to the rules/backend reliability role.

- [x] **Step 4: Switch the active topic only after approval**

Archive the previous status/handoff snapshot under `docs/plans/daily/2026-07/`, then replace the main sections with the storage topic. Do not append a second topic to the existing main-area files.

- [x] **Step 5: Commit governance changes**

```bash
git add docs/plans/PLAN-20260716-campus-pv-storage-simulation.md docs/plans/current-status.md docs/plans/handoff.md docs/plans/daily/2026-07
git commit -m "docs: start campus pv storage simulation"
```

## Task 2: Implement the pure battery state model

**Files:**
- Create: `app/domain/storage_simulation.py`
- Test: `tests/test_storage_simulation_domain.py`

- [x] **Step 1: Write failing energy-balance tests**

```python
from app.domain.storage_simulation import StorageAssetConfig, StorageState, step_storage


def test_charge_updates_soc_with_efficiency():
    config = StorageAssetConfig(energy_kwh=500, power_kw=250, charge_efficiency=0.95, discharge_efficiency=0.95)
    state = StorageState(soc=50.0, actual_power_kw=0.0, temperature_c=30.0, soh=100.0, throughput_kwh=0.0)
    result = step_storage(config, state, target_power_kw=100.0, seconds=900, ambient_temperature_c=25.0)
    assert result.actual_power_kw == 100.0
    assert result.soc == 54.75


def test_discharge_stops_at_soc_floor():
    config = StorageAssetConfig(energy_kwh=500, power_kw=250, soc_min=10.0, soc_max=90.0)
    state = StorageState(soc=10.0, actual_power_kw=0.0, temperature_c=30.0, soh=100.0, throughput_kwh=0.0)
    result = step_storage(config, state, target_power_kw=-200.0, seconds=60, ambient_temperature_c=25.0)
    assert result.actual_power_kw == 0.0
    assert result.run_state == "standby"
```

- [x] **Step 2: Run tests and verify failure**

Run: `python -m pytest -q tests/test_storage_simulation_domain.py`

Expected: FAIL with `ModuleNotFoundError: app.domain.storage_simulation`.

- [x] **Step 3: Implement the minimal pure model**

```python
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class StorageAssetConfig:
    energy_kwh: float
    power_kw: float
    charge_efficiency: float = 0.95
    discharge_efficiency: float = 0.95
    soc_min: float = 10.0
    soc_max: float = 90.0
    ramp_kw_per_second: float = 25.0


@dataclass(frozen=True)
class StorageState:
    soc: float
    actual_power_kw: float
    temperature_c: float
    soh: float
    throughput_kwh: float
    run_state: str = "standby"


def step_storage(config, state, *, target_power_kw, seconds, ambient_temperature_c):
    target = max(-config.power_kw, min(config.power_kw, float(target_power_kw)))
    if (target > 0 and state.soc >= config.soc_max) or (target < 0 and state.soc <= config.soc_min):
        target = 0.0
    ramp = config.ramp_kw_per_second * seconds
    actual = max(state.actual_power_kw - ramp, min(state.actual_power_kw + ramp, target))
    hours = seconds / 3600.0
    stored_delta = actual * config.charge_efficiency * hours if actual >= 0 else actual / config.discharge_efficiency * hours
    soc = max(0.0, min(100.0, state.soc + stored_delta / config.energy_kwh * 100.0))
    throughput = state.throughput_kwh + abs(actual) * hours
    run_state = "charging" if actual > 0 else "discharging" if actual < 0 else "standby"
    temperature = state.temperature_c + abs(actual) / config.power_kw * 0.02 * seconds - (state.temperature_c - ambient_temperature_c) * 0.001 * seconds
    return replace(state, soc=round(soc, 6), actual_power_kw=actual, temperature_c=temperature, throughput_kwh=throughput, run_state=run_state)
```

- [x] **Step 4: Add boundary tests**

Add tests for rated power clipping, ramping, direction change through zero, SOC ceiling, finite inputs, and `seconds > 0`. Reject invalid configuration with `ValueError` rather than returning NaN.

- [x] **Step 5: Run focused tests**

Run: `python -m pytest -q tests/test_storage_simulation_domain.py`

Expected: all storage simulation domain tests PASS.

- [x] **Step 6: Commit**

```bash
git add app/domain/storage_simulation.py tests/test_storage_simulation_domain.py
git commit -m "feat: add storage battery simulation model"
```

## Task 3: Add storage asset, telemetry, and dispatch persistence

**Files:**
- Modify: `app/models/storage.py`
- Create: `migrations/versions/20260716_0002_add_storage_simulation_contracts.py`
- Test: `tests/test_storage_model_contract.py`
- Test: `tests/test_migration_storage_contract.py`

- [x] **Step 1: Write failing migration contract tests**

Create `tests/test_migration_storage_contract.py` before editing the model or migration. Lock all of these facts:

- active migration filename is `20260716_0002_add_storage_simulation_contracts.py`;
- `revision = "20260716_0002"` and `down_revision = "20260716_0001"`;
- the accepted baseline owns the base `storage_telemetry` table, so Task 3 must not call `op.create_table("storage_telemetry", ...)`;
- Task 3 may create only `storage_asset_profile` and `storage_dispatch_plan` and may add only these eight approved telemetry extensions: `target_active_power`, `available_charge_power`, `available_discharge_power`, `bms_status`, `pcs_status`, `grid_status`, `command_source`, and `data_source`;
- downgrade removes exactly the Task 3 additions and does not drop the baseline-owned telemetry table.

- [x] **Step 2: Run migration contract tests and verify RED**

Run: `python -m pytest -q tests/test_migration_storage_contract.py`

Expected: FAIL because `20260716_0002` does not exist. This RED must be observed before modifying `app/models/storage.py` or creating the migration.

- [x] **Step 3: Write failing model contract tests**

```python
from datetime import date, datetime
from app.models.storage import StorageAssetProfile, StorageDispatchPlan, StorageTelemetry


def test_storage_contract_models_keep_power_direction_and_source():
    profile = StorageAssetProfile(device_id=1, rated_energy_kwh=500, rated_power_kw=250, soc_min=10, soc_max=90)
    telemetry = StorageTelemetry(device_id=1, timestamp=datetime(2026, 7, 16), target_active_power=-125, data_source="simulated")
    plan = StorageDispatchPlan(device_id=1, dispatch_date=date(2026, 7, 17), slot_index=0, target_active_power=100, strategy="day_ahead")
    assert profile.rated_energy_kwh == 500
    assert telemetry.target_active_power == -125
    assert plan.slot_index == 0
```

- [x] **Step 4: Run model contract tests and verify RED**

Run: `python -m pytest -q tests/test_storage_model_contract.py`

Expected: FAIL because the new models and fields do not exist.

- [x] **Step 5: Add focused SQLModel contracts**

The accepted root baseline already owns the 基础 `storage_telemetry` table. Task 3 must not recreate it（不得重建基础表）. Add `StorageAssetProfile` with unique `device_id`, rated energy/power, efficiencies, hard/soft SOC bounds, voltage, battery type, BMS/PCS model, protocol version, location, commission date, and timestamps.

Extend `StorageTelemetry` with nullable `target_active_power`, available charge/discharge power, BMS/PCS/grid states, command source, and `data_source` defaulting to `telemetry`.

Add `StorageDispatchPlan` with `(device_id, dispatch_date, slot_index)` uniqueness, 0-95 slot validation in service code, forecasts, tariff, target power, expected SOC, strategy/version, solver status, validity, failure reason, and generation timestamp.

- [x] **Step 6: Write the deterministic migration**

The migration must use only explicit Alembic operations. Set:

```python
revision = "20260716_0002"
down_revision = "20260716_0001"
```

Create `storage_asset_profile` and `storage_dispatch_plan`, add only the eight approved telemetry extensions to the baseline-owned `storage_telemetry`, create the unique dispatch-slot constraint, and implement a complete downgrade. Task 3 is limited to profile, dispatch, and those approved telemetry extensions; it must not recreate the base telemetry table. Do not import current SQLModel metadata or query application tables during migration.

- [x] **Step 7: Run focused tests and offline SQL**

Run:

```bash
python -m pytest -q tests/test_storage_model_contract.py tests/test_migration_storage_contract.py
alembic upgrade head --sql > /tmp/storage-upgrade.sql
rg "storage_asset_profile|storage_dispatch_plan|target_active_power" /tmp/storage-upgrade.sql
```

Expected: tests PASS; offline SQL generation exits `0`; all three schema names are present.

- [x] **Step 8: Run real three-path verification and inspect the preserved fresh database**

```bash
python scripts/python/verify_postgres_migrations.py \
  --keep-success \
  --json-output /tmp/storage-task3-migrations.json
python - <<'PY'
import os

import psycopg2
from sqlalchemy.engine import make_url

expected_tables = {"storage_asset_profile", "storage_dispatch_plan"}
expected_columns = {
    "target_active_power",
    "available_charge_power",
    "available_discharge_power",
    "bms_status",
    "pcs_status",
    "grid_status",
    "command_source",
    "data_source",
}
admin_url = make_url(os.environ["MIGRATION_ADMIN_URL"])
for database_name in (
    "ces_migration_fresh",
    "ces_migration_offline",
    "ces_migration_roundtrip",
):
    url = admin_url.set(database=database_name, drivername="postgresql")
    connection = psycopg2.connect(url.render_as_string(hide_password=False))
    with connection, connection.cursor() as cursor:
        cursor.execute("SELECT version_num FROM alembic_version")
        assert cursor.fetchone()[0] == "20260716_0002"
        cursor.execute(
            "SELECT hypertable_name FROM timescaledb_information.hypertables "
            "WHERE hypertable_schema='public' AND hypertable_name='energydata'"
        )
        assert cursor.fetchone()[0] == "energydata"
        if database_name == "ces_migration_fresh":
            cursor.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' "
                "AND table_name IN "
                "('storage_asset_profile', 'storage_dispatch_plan')"
            )
            assert {row[0] for row in cursor.fetchall()} == expected_tables
            cursor.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name='storage_telemetry'"
            )
            actual_columns = {row[0] for row in cursor.fetchall()}
            assert expected_columns <= actual_columns
    connection.close()
print("three-path revision/hypertable and fresh storage contract: verified")
PY
python scripts/python/verify_postgres_migrations.py --cleanup
```

Expected: verifier exits `0`; fresh, offline, and roundtrip fingerprints are identical; every path is at revision `20260716_0002`; preserved fresh contains both new storage tables, exactly the eight approved `storage_telemetry` extensions, and `public.energydata` remains a hypertable. The final cleanup command must exit `0` and remove all three fixed temporary databases. If inspection fails, run cleanup before reporting the blocker.

- [x] **Step 9: Commit**

```bash
git add app/models/storage.py migrations/versions/20260716_0002_add_storage_simulation_contracts.py tests/test_storage_model_contract.py tests/test_migration_storage_contract.py
git commit -m "feat: add storage simulation persistence contracts"
```

## Task 4: Persist extended simulator telemetry

**Files:**
- Modify: `app/integrations/mqtt/device_extensions.py`
- Modify: `app/services/devices/storage/monitor_service.py`
- Test: `tests/test_storage_ingestion.py`
- Test: `tests/test_storage_monitor_service.py`

- [x] **Step 1: Add a failing simulator-payload test**

```python
payload = {
    "soc": 68.4,
    "soh": 97.8,
    "active_power": -120.0,
    "target_active_power": -125.0,
    "available_charge_power": 250.0,
    "available_discharge_power": 180.0,
    "bms_state": "normal",
    "pcs_state": "running",
    "grid_connection_state": "connected",
    "command_source": "rule",
    "data_source": "simulated",
}
```

Persist it through `persist_device_extensions` and assert every field is stored without converting the negative discharge sign.

The MQTT payload keeps the device-facing design keys `bms_state`, `pcs_state`, and `grid_connection_state`. The ingestion adapter must map them to the persistence columns `bms_status`, `pcs_status`, and `grid_status`; do not attempt to write state-named columns that are not part of `StorageTelemetry`.

- [x] **Step 2: Run and verify failure**

Run: `python -m pytest -q tests/test_storage_ingestion.py tests/test_storage_monitor_service.py`

Expected: new field assertions FAIL.

- [x] **Step 3: Extend extraction and monitoring**

Add numeric fields to `_STORAGE_NUMERIC_FIELDS`, explicitly map the three device-facing state keys to their status columns, add command/source fields to the text extraction, and expose semantic metrics in `build_storage_monitor`:

```python
"target_active_power": m(target_power, **tm(target_power)),
"available_charge_power": m(available_charge, **tm(available_charge)),
"available_discharge_power": m(available_discharge, **tm(available_discharge)),
"bms_state": m(bms_state, source="telemetry" if bms_state else "missing", state="live" if bms_state else "missing"),
"pcs_state": m(pcs_state, source="telemetry" if pcs_state else "missing", state="live" if pcs_state else "missing"),
"data_source": m(data_source, source="telemetry", state="simulated" if data_source == "simulated" else "live"),
```

- [x] **Step 4: Run focused tests**

Run: `python -m pytest -q tests/test_storage_ingestion.py tests/test_storage_monitor_service.py tests/test_device_monitor_service.py`

Expected: PASS with no new warnings.

- [x] **Step 5: Commit**

```bash
git add app/integrations/mqtt/device_extensions.py app/services/devices/storage/monitor_service.py tests/test_storage_ingestion.py tests/test_storage_monitor_service.py
git commit -m "feat: ingest storage simulator telemetry"
```

## Task 5: Build the reusable MQTT storage simulator

**Files:**
- Create: `scripts/python/storage_simulator.py`
- Modify: `scripts/python/README.md`
- Modify: `app/core/settings.py`
- Modify: `env.example`
- Modify: `env.local.example`
- Modify: `env.prod.example`
- Test: `tests/test_storage_simulator_cli.py`
- Test: `tests/test_storage_settings.py`

- [x] **Step 1: Write failing CLI and payload tests**

```python
from scripts.python.storage_simulator import SimulatorConfig, build_telemetry_payload


def test_simulator_payload_is_explicitly_simulated():
    payload = build_telemetry_payload(SimulatorConfig(device_code="STO-001"), timestamp="2026-07-16T10:00:00+08:00")
    assert payload["device_category"] == "storage"
    assert payload["device_subtype"] == "battery_energy_storage_system"
    assert payload["data_source"] == "simulated"
    assert payload["active_power"] == 0.0
```

- [x] **Step 2: Run and verify failure**

Run: `python -m pytest -q tests/test_storage_simulator_cli.py`

Expected: FAIL because the simulator module does not exist.

- [x] **Step 3: Implement the simulator CLI**

Implement `SimulatorConfig`, five deterministic scenario curves, `build_telemetry_payload`, command subscription, receipt publication, acceleration factor, seeded randomness, and graceful shutdown. CLI arguments must include:

```text
--device-code STO-001
--scenario sunny_workday
--speed 60
--seed 20260716
--print-only
```

`--print-only` must emit one valid JSON payload without opening a network connection. Normal mode publishes telemetry and control receipts to `campus/device/{device_code}/telemetry`, subscribes to real-device commands on `campus/control/{device_code}`, and subscribes to simulator-only scenario commands on `campus/simulation/{device_code}/control`.

Add typed settings for `storage_ems_enabled`, `storage_simulation_enabled`, `storage_simulation_topic_prefix`, and daily dispatch time. Default both enable flags to false in Python settings and all environment examples. Starting the standalone simulator still requires an explicit CLI invocation; application APIs and scheduled automatic control remain unavailable while their flags are false.

- [x] **Step 4: Verify deterministic output**

Run:

```bash
python scripts/python/storage_simulator.py --print-only --seed 20260716
python -m pytest -q tests/test_storage_simulator_cli.py tests/test_storage_settings.py
```

Expected: JSON contains `data_source=simulated`; tests PASS; repeated runs with the same seed match after excluding the generated timestamp.

- [x] **Step 5: Document the entrypoint**

Add the exact command, MQTT topics, sign convention, supported scenarios, and a warning that the tool is a system-level simulator rather than real BMS/PCS firmware.

- [x] **Step 6: Commit Milestone A**

```bash
git add scripts/python/storage_simulator.py scripts/python/README.md app/core/settings.py env.example env.local.example env.prod.example tests/test_storage_simulator_cli.py tests/test_storage_settings.py
git commit -m "feat: add campus storage mqtt simulator"
```

## Task 6: Implement storage command lifecycle and receipt dispatch

**Files:**
- Create: `app/services/devices/storage/specs.py`
- Create: `app/services/devices/storage/control_command_service.py`
- Create: `app/integrations/mqtt/control_receipts.py`
- Modify: `app/integrations/mqtt/processor.py`
- Modify: `app/services/scheduler_jobs.py`
- Modify: `app/services/scheduler_registry.py`
- Test: `tests/test_storage_control_command_service.py`
- Test: `tests/test_storage_control_receipts.py`

- [x] **Step 1: Write failing command lifecycle tests**

```python
import json


def test_storage_power_command_uses_existing_sign_convention(session, storage_device):
    result = StorageControlCommandService.queue_command(
        session,
        device_id=storage_device.id,
        command="set_active_power",
        target_active_power=-125.0,
        operator="operator",
        source="manual",
    )
    assert result["status"] == "accepted"
    assert result["payload"]["target_active_power"] == -125.0
    assert json.loads(result["log"].reason)["data_source"] == "simulated"


def test_storage_receipt_dispatches_by_device_category(session, storage_device, pending_storage_log):
    log = process_device_control_receipt(
        session,
        {"message_type": "control_receipt", "command_id": str(pending_storage_log.id), "result": "success"},
        storage_device.id,
    )
    assert log.result == "success"
```

- [x] **Step 2: Run and verify failure**

Run: `python -m pytest -q tests/test_storage_control_command_service.py tests/test_storage_control_receipts.py`

Expected: FAIL because the storage command service and dispatcher do not exist.

- [x] **Step 3: Define fixed storage command specs**

Support only:

```python
SUPPORTED_STORAGE_COMMANDS = {"set_active_power", "set_control_mode", "stop"}
SUPPORTED_RESULTS = {"accepted", "running", "success", "failed", "timeout", "rejected"}
PENDING_RESULTS = {"accepted", "running"}
TERMINAL_RESULTS = {"success", "failed", "timeout", "rejected"}
```

Validate finite power, rated-power bounds from `StorageAssetProfile`, source in `manual/rule/day_ahead`, mode in `auto/manual`, and one pending storage command per device.

- [x] **Step 4: Implement storage control service**

Reuse `DeviceControlLog`, `publish_control_payload_async`, row locking, pending-command timeout, idempotent terminal receipts, and realtime control-log events. Use `command_source="storage-control-api"`; encode target power, manual/rule/day-ahead source, latest telemetry `data_source`, and optional `simulation_run_id` into structured JSON `reason`. These exact markers are required by Task 15 cutover preview; never infer simulated records from the device code.

- [x] **Step 5: Add category-aware receipt dispatch**

```python
def process_device_control_receipt(session, data, device_id):
    device = session.get(Device, device_id)
    if device is None:
        raise ValueError(f"控制回执设备不存在：device_id={device_id}")
    if device.device_category == "storage":
        return StorageControlCommandService.apply_control_receipt(session, device_id=device_id, command_id=data.get("command_id"), result=data.get("result"), detail=data.get("detail"))
    return CapacitorBankControlCommandService.apply_control_receipt(session, device_id=device_id, command_id=data.get("command_id"), result=data.get("result"), detail=data.get("detail"))
```

Modify the processor to call this function while retaining existing compensation behavior.

- [x] **Step 6: Add timeout job**

Create `expire_storage_control_timeouts()` in `scheduler_jobs.py` and register it at the same cadence as compensation timeout convergence. It must only update `storage-control-api` pending logs.

- [x] **Step 7: Run focused tests**

Run:

```bash
python -m pytest -q tests/test_storage_control_command_service.py tests/test_storage_control_receipts.py tests/test_mqtt_processor.py tests/test_capacitor_bank_control_command_service_boundary.py
```

Expected: all PASS; compensation receipt tests remain green.

- [x] **Step 8: Commit**

```bash
git add app/services/devices/storage/specs.py app/services/devices/storage/control_command_service.py app/integrations/mqtt/control_receipts.py app/integrations/mqtt/processor.py app/services/scheduler_jobs.py app/services/scheduler_registry.py tests/test_storage_control_command_service.py tests/test_storage_control_receipts.py tests/test_scheduler_jobs.py
git commit -m "feat: add storage control receipt lifecycle"
```

## Task 7: Expose storage asset and control APIs

**Files:**
- Modify: `app/models/storage.py`
- Modify: `app/integrations/mqtt/device_extensions.py`
- Modify: `app/services/devices/storage/control_command_service.py`
- Modify: `app/services/mqtt_publisher.py`
- Create: `migrations/versions/20260717_0003_add_storage_source_and_control_gates.py`
- Create: `app/api/endpoints/devices/storage_schemas.py`
- Create: `app/services/devices/storage/asset_profile_service.py`
- Modify: `app/api/endpoints/devices/storage.py`
- Test: `tests/test_storage_device_nested_api.py`
- Test: `tests/test_storage_single_system_migration.py`
- Test: `tests/test_storage_ingestion.py`
- Test: `tests/test_storage_asset_profile_service.py`

- [x] **Step 1: Write failing API boundary tests**

Test:

```text
GET  /devices/{id}/storage/profile
PUT  /devices/{id}/storage/profile
GET  /devices/{id}/storage/control/capabilities
POST /devices/{id}/storage/control
GET  /devices/{id}/storage/simulation/capabilities
POST /devices/{id}/storage/simulation/control
```

Assert viewers can read but cannot control; maintainer/operator/admin can control within location scope; invalid power returns 400; unknown device returns the existing access-control response; simulator endpoints return 404 while `STORAGE_SIMULATION_ENABLED=false`. Also assert `StorageAssetProfile.ems_auto_enabled` defaults to false, `StorageTelemetry.simulation_run_id` is nullable and populated from simulated MQTT payloads, `StorageDispatchPlan.data_source` defaults to `calculated`, and its `simulation_run_id` is nullable.

- [x] **Step 2: Run and verify failure**

Run: `python -m pytest -q tests/test_storage_single_system_migration.py tests/test_storage_device_nested_api.py`

Expected: endpoint tests FAIL with 404 or missing schema imports; model tests FAIL because the source/control-gate fields and `20260717_0003` migration do not exist.

- [x] **Step 3: Add explicit Pydantic/SQLModel schemas**

```python
class StorageControlRequest(SQLModel):
    command: Literal["set_active_power", "set_control_mode", "stop"]
    target_active_power: Optional[float] = None
    control_mode: Optional[Literal["auto", "manual"]] = None
    source: Literal["manual", "rule", "day_ahead"] = "manual"
    reason: Optional[str] = None


class StorageControlResponse(SQLModel):
    accepted: bool
    status: str
    command_id: str
    message: str


class StorageSimulationControlRequest(SQLModel):
    action: Literal["set_scenario", "set_speed", "inject_fault", "clear_fault"]
    scenario: Optional[Literal["sunny_workday", "cloudy_workday", "weekend_low_load", "pv_surplus", "evening_peak"]] = None
    speed: Optional[Literal[1, 10, 60, 288]] = None
    fault: Optional[Literal["low_soc", "overtemperature", "pcs_fault", "communication_loss", "pv_drop"]] = None
```

Add these single-system persistence fields:

```python
class StorageAssetProfile(SQLModel, table=True):
    ems_auto_enabled: bool = Field(default=False, description="设备级 EMS 自动控制授权")

class StorageTelemetry(SQLModel, table=True):
    simulation_run_id: Optional[str] = Field(default=None, index=True, description="模拟运行标识")

class StorageDispatchPlan(SQLModel, table=True):
    data_source: str = Field(default="calculated", description="计划来源：calculated/simulated/real")
    simulation_run_id: Optional[str] = Field(default=None, index=True, description="模拟运行标识")
```

Create static, offline-safe revision `20260717_0003` with `down_revision = "20260716_0002"`. It may add only these four columns and their approved source/run indexes. Extend `persist_device_extensions` to persist the optional run id, then let the control service copy it from latest telemetry into structured `reason`.

- [x] **Step 4: Verify the additive migration paths**

Run:

```bash
alembic upgrade head --sql
python scripts/python/verify_postgres_migrations.py --keep-success
python -m pytest -q tests/test_storage_single_system_migration.py tests/test_storage_ingestion.py
python scripts/python/verify_postgres_migrations.py --cleanup
```

Expected: offline SQL performs no online reads; fresh/offline/roundtrip fingerprints match at `20260717_0003`; the exact four columns and approved indexes exist; `energydata` remains a hypertable; focused tests PASS; cleanup removes only the three fixed temporary databases.

- [x] **Step 5: Implement thin endpoints**

Endpoints perform dependency injection, permission checks, audit logging, service calls, and response conversion only. Keep validation and command lifecycle in services. Simulator endpoints publish only to `campus/simulation/{device_code}/control`, require the explicit simulation flag, and never share the production device-control topic. Add an administrator-only update for `ems_auto_enabled`; enabling it must fail unless a current asset profile exists and the latest telemetry proves BMS normal, PCS available, grid connected, and non-stale data.

- [x] **Step 6: Run API tests**

Run: `python -m pytest -q tests/test_storage_single_system_migration.py tests/test_storage_ingestion.py tests/test_storage_device_nested_api.py tests/test_access_control.py`

Expected: PASS.

- [x] **Step 7: Commit**

```bash
git add app/models/storage.py app/integrations/mqtt/device_extensions.py app/services/devices/storage/control_command_service.py app/services/mqtt_publisher.py migrations/versions/20260717_0003_add_storage_source_and_control_gates.py app/api/endpoints/devices/storage_schemas.py app/services/devices/storage/asset_profile_service.py app/api/endpoints/devices/storage.py tests/test_storage_single_system_migration.py tests/test_storage_ingestion.py tests/test_storage_device_nested_api.py tests/test_storage_asset_profile_service.py
git commit -m "feat: expose storage profile and control api"
```

## Task 8: Implement safety-first real-time rules

**Files:**
- Create: `app/domain/storage_control_rules.py`
- Create: `app/services/devices/storage/ems_service.py`
- Modify: `app/services/scheduler_jobs.py`
- Modify: `app/services/scheduler_registry.py`
- Test: `tests/test_storage_control_rules.py`
- Test: `tests/test_storage_ems_service.py`
- Test: `tests/test_scheduler_jobs.py`

- [x] **Step 1: Write failing rule-priority tests**

```python
def test_fault_overrides_pv_surplus_and_peak_shaving():
    decision = decide_storage_power(StorageRuleInput(load_kw=420, pv_kw=500, tariff="peak", soc=60, temperature_c=58, bms_state="fault", pcs_state="running", grid_connected=True))
    assert decision.target_power_kw == 0
    assert decision.reason_code == "safety_fault"


def test_pv_surplus_charges_before_tariff_rule():
    decision = decide_storage_power(StorageRuleInput(load_kw=100, pv_kw=180, tariff="peak", soc=50, temperature_c=30, bms_state="normal", pcs_state="running", grid_connected=True, available_charge_kw=250))
    assert decision.target_power_kw == 80
    assert decision.reason_code == "pv_surplus"


def test_demand_limit_discharge_is_negative():
    decision = decide_storage_power(StorageRuleInput(load_kw=420, pv_kw=20, tariff="flat", demand_limit_kw=300, soc=70, temperature_c=30, bms_state="normal", pcs_state="running", grid_connected=True, available_discharge_kw=250))
    assert decision.target_power_kw == -100
```

- [x] **Step 2: Run and verify failure**

Run: `python -m pytest -q tests/test_storage_control_rules.py`

Expected: FAIL because the rule module does not exist.

- [x] **Step 3: Implement pure rules**

Use immutable input/decision dataclasses. Fixed priority is safety, PV surplus, demand limit, tariff, idle. Add 5 kW deadband, SOC/temperature hysteresis, minimum run/stop durations, and direction-change standby. Return both target power and a stable reason code.

- [x] **Step 4: Implement EMS orchestration**

`StorageEmsService.evaluate_device` loads latest telemetry/profile and current campus load/PV/tariff inputs, invokes the pure rule, and queues a command only when:

- both the global `STORAGE_EMS_ENABLED` gate and `StorageAssetProfile.ems_auto_enabled` are true;
- device is auto mode;
- no pending command exists;
- target differs from current target outside deadband;
- minimum timing constraints permit a transition.

The service does not publish directly if the rule returns a safety stop already represented by a pending stop command.

- [x] **Step 5: Register the 60-second rule job**

Register the job only when `STORAGE_EMS_ENABLED=true`, using the default-off typed setting introduced with the simulator. Each execution must independently skip profiles whose `ems_auto_enabled` remains false. Adding the rule service must not change the default runtime behavior.

- [x] **Step 6: Run focused tests**

Run: `python -m pytest -q tests/test_storage_control_rules.py tests/test_storage_ems_service.py tests/test_scheduler_registry.py`

Expected: PASS.

- [x] **Step 7: Commit**

```bash
git add app/domain/storage_control_rules.py app/services/devices/storage/ems_service.py app/services/scheduler_jobs.py app/services/scheduler_registry.py tests/test_storage_control_rules.py tests/test_storage_ems_service.py tests/test_scheduler_jobs.py
git commit -m "feat: add storage safety and realtime ems rules"
```

## Task 9: Complete simulator command execution and fault injection

**Files:**
- Modify: `scripts/python/storage_simulator.py`
- Test: `tests/test_storage_simulator_control.py`

- [x] **Step 1: Write failing command execution tests**

Cover `accepted -> running -> success`, SOC rejection, overtemperature rejection, timeout injection, duplicate `command_id`, manual/auto mode, stop, actual-power tolerance, scenario switching, speed changes, and fault injection over the separate simulator-only topic. Every telemetry and receipt message must carry `data_source=simulated` and the stable CLI-generated `simulation_run_id` for that process.

Use this success criterion:

```python
assert abs(actual_power_kw - target_power_kw) <= max(2.5, abs(target_power_kw) * 0.02)
```

and require it to hold for three consecutive simulator steps before `success`.

- [x] **Step 2: Run and verify failure**

Run: `python -m pytest -q tests/test_storage_simulator_control.py`

Expected: lifecycle assertions FAIL.

- [x] **Step 3: Implement command state machine**

Use states `accepted`, `running`, and one terminal result. Cache terminal results by `command_id` so duplicate delivery republishes the same receipt without applying the action twice. Generate one UUID `simulation_run_id` when the simulator starts and reuse it in all messages for that run. Fault injection accepts only the fixed scenario keys from the design rather than arbitrary code execution. Reject simulator-only messages unless `STORAGE_SIMULATION_ENABLED=true`; never accept `set_scenario`, `set_speed`, or `inject_fault` on the real-device control topic.

- [x] **Step 4: Run simulator control tests**

Run: `python -m pytest -q tests/test_storage_simulator_cli.py tests/test_storage_simulator_control.py`

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add scripts/python/storage_simulator.py tests/test_storage_simulator_control.py
git commit -m "feat: simulate storage command execution"
```

Task 9 实现提交为 `6254dd8a`。RED 由缺失仿真门禁、运行标识和命令状态机，以及真实控制主题错误接受 simulator-only 动作触发；GREEN 后聚焦测试为 `19 passed`，完整后端为 `811 passed, 2 skipped, 7 warnings`，Task 9 变更文件 Ruff 与差异检查通过。

## Task 10: Enhance the storage device workbench

**Files:**
- Modify: `frontend/src/api/storage.ts`
- Modify: `frontend/src/features/device-monitor/composables/useStorageMonitor.ts`
- Create: `frontend/src/features/device-monitor/components/storage/StorageControlPanel.vue`
- Create: `frontend/src/features/device-monitor/components/storage/StorageCommandTimeline.vue`
- Modify: `frontend/src/features/device-monitor/views/StorageMonitorView.vue`
- Test: `frontend/src/features/device-monitor/composables/__tests__/useStorageMonitor.test.ts`
- Test: `frontend/src/features/device-monitor/components/storage/__tests__/StorageControlPanel.test.ts`
- Test: `frontend/src/features/device-monitor/components/storage/__tests__/StorageCommandTimeline.test.ts`

- [x] **Step 1: Write failing frontend tests**

Assert:

- simulated telemetry shows a visible `仿真数据` badge;
- `data_source=real` shows `真实设备` without changing the route or component tree;
- positive target power is labeled charging and negative target power discharging;
- viewer controls are disabled;
- manual setpoint emits `set_active_power` with the unchanged sign;
- a pending command disables conflicting controls;
- rejected/timeout receipts show the backend reason.
- the administrator-only automatic-control authorization stays off by default and cannot be enabled from a viewer session.

- [x] **Step 2: Run focused tests and verify failure**

Run:

```bash
cd frontend
npm run test:unit -- src/features/device-monitor/composables/__tests__/useStorageMonitor.test.ts src/features/device-monitor/components/storage/__tests__/StorageControlPanel.test.ts src/features/device-monitor/components/storage/__tests__/StorageCommandTimeline.test.ts
```

Expected: FAIL because components and APIs do not exist.

- [x] **Step 3: Extend frontend contracts**

Add the eight telemetry fields, profile/capability types, simulator scenario types, and:

```typescript
export function sendStorageControl(deviceId: number, body: StorageControlRequest) {
  return request.post<never, StorageControlResponse>(`/devices/${deviceId}/storage/control`, body)
}
```

- [x] **Step 4: Add composable state and actions**

Keep requests in `useStorageMonitor`; components receive props and emit actions. On accepted commands, show accepted state and refresh overview/control logs. WebSocket control-log events update the timeline without fabricating success.

- [x] **Step 5: Compose the workbench**

Add target/actual power, deviation, available power, BMS/PCS/grid state, data source, manual/auto controls, per-device automatic-control authorization, stop, current plan slot, and command timeline. Extend the existing trend area with target-versus-actual and available-power series. Keep existing SOC/trends/status panels, route, archive, permissions, and refresh flow; do not create a simulated-device page or rewrite unrelated monitor components.

- [x] **Step 6: Run focused tests, typecheck, and build**

Run:

```bash
cd frontend
npm run test:unit -- src/features/device-monitor
npm run typecheck
npm run build
```

Expected: all storage/device-monitor tests PASS; typecheck and build exit `0`. Record the four unrelated baseline unit failures separately if a full unit run is repeated.

- [x] **Step 7: Commit Milestone B**

```bash
git add frontend/src/api/storage.ts frontend/src/features/device-monitor/composables/useStorageMonitor.ts frontend/src/features/device-monitor/components/storage frontend/src/features/device-monitor/views/StorageMonitorView.vue
git commit -m "feat: add storage control workbench"
```

Task 10 实现提交为 `a83cbc49`。RED 阶段为 `4 failed, 2 passed`；GREEN 后储能工作台及页面相关回归为 `27 passed`，设备监控目录为 `206 passed, 1 failed`，其中唯一失败是既有 `DeviceTrendPanel` 的 `el-segmented` 基线问题。前端全量为 `365 passed, 4 failed`，四项失败均为既有基线（`EnergyManagement` 三项、`DeviceTrendPanel` 一项）；typecheck、build 和 Task 10 变更文件 ESLint 均通过。

## Task 11: Implement the day-ahead MILP optimizer

**Files:**
- Modify: `requirements.txt`
- Modify: `constraints-ci.txt`
- Create: `app/domain/storage_dispatch_optimizer.py`
- Test: `tests/test_storage_dispatch_optimizer.py`

- [x] **Step 1: Pin PuLP**

Add one compatible pinned PuLP version to both dependency files and verify `pip check`. Do not add Gurobi or another commercial runtime.

- [x] **Step 2: Write failing optimizer tests**

Create a deterministic 96-slot sunny-day input and assert:

- 96 results are returned;
- no slot charges and discharges simultaneously;
- SOC stays within 15%-85%;
- end SOC meets target;
- grid import is non-negative;
- maximum grid import is lower than the no-storage baseline;
- repeated solve returns identical rounded results.

- [x] **Step 3: Run and verify failure**

Run: `python -m pytest -q tests/test_storage_dispatch_optimizer.py`

Expected: FAIL because the optimizer module does not exist.

- [x] **Step 4: Implement the MILP**

Use PuLP variables `charge_kw[t]`, `discharge_kw[t]`, `grid_kw[t]`, `soc[t]`, binary `is_charging[t]`, `is_discharging[t]`, `curtail_kw[t]`, and `peak_grid_kw`. Objective terms are energy cost, demand charge, throughput degradation, and curtailment penalty. Return a frozen result object containing solver status, slot results, total cost, peak demand, curtailment, and terminal SOC.

Keep the repository-wide sign convention explicit at the optimizer boundary:

```text
target_active_power[t] = charge_kw[t] - discharge_kw[t]
grid_kw[t] = load_kw[t] - pv_kw[t] + curtail_kw[t] + charge_kw[t] - discharge_kw[t]
```

Update SOC with charge/discharge efficiency at 0.25 h per slot, enforce the 15%-85% soft operating range, enforce mutually exclusive charge/discharge binaries, and require the configured terminal SOC target. Baseline comparison uses zero storage power against the same load/PV/tariff series.

- [x] **Step 5: Add infeasibility and validation tests**

Reject non-96-length inputs, non-finite values, invalid efficiency, and impossible initial SOC with `ValueError`. Convert non-optimal solver outcomes to `DispatchOptimizationError` with the solver status.

- [x] **Step 6: Run optimizer tests and dependency check**

Run:

```bash
python -m pip install --constraint constraints-ci.txt -r requirements.txt
python -m pip check
python -m pytest -q tests/test_storage_dispatch_optimizer.py
```

Expected: dependency check and tests PASS.

- [x] **Step 7: Commit**

```bash
git add requirements.txt constraints-ci.txt app/domain/storage_dispatch_optimizer.py tests/test_storage_dispatch_optimizer.py
git commit -m "feat: add storage day ahead optimizer"
```

Task 11 实现提交为 `48b91c90`。RED 因优化器模块不存在而按预期失败；GREEN 后聚焦测试 `6 passed`，完整后端 `817 passed, 2 skipped, 7 warnings`，变更文件 Ruff 通过。`PuLP 3.3.0` 同时固定在 requirements 与 CI constraints；干净 Python 3.12 环境完成全量依赖安装并通过 `pip check`。本机历史共享 venv 仍为非正式的 Python 3.9，无法重装既有 `python-multipart==0.0.32`，不作为 Python 3.10+ 正式基线验收结果。

## Task 12: Persist and execute dispatch plans with safe fallback

**Files:**
- Create: `app/services/devices/storage/dispatch_service.py`
- Modify: `app/services/devices/storage/ems_service.py`
- Modify: `app/services/scheduler_jobs.py`
- Modify: `app/services/scheduler_registry.py`
- Modify: `app/api/endpoints/devices/storage.py`
- Modify: `app/api/endpoints/devices/storage_schemas.py`
- Test: `tests/test_storage_dispatch_service.py`
- Test: `tests/test_storage_dispatch_api.py`

- [ ] **Step 1: Write failing service tests**

Test valid plan replacement in one transaction, retrieval of the current slot, plan/actual deviation reason, optimizer failure preserving the latest valid plan, expired-plan fallback to rules, and viewer read/operator generate permissions.

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest -q tests/test_storage_dispatch_service.py tests/test_storage_dispatch_api.py`

Expected: FAIL because dispatch service and routes do not exist.

- [ ] **Step 3: Implement transactional plan generation**

Persist all 96 rows only after an optimal result exists. Mark the prior plan invalid in the same transaction. Use strategy `day_ahead`, a semantic version string, and a generated-at timestamp. Set `data_source=simulated` plus the current `simulation_run_id` for synthetic scenario plans, and `data_source=calculated` with no run id for ordinary forecast plans; never infer plan source from strategy name.

- [ ] **Step 4: Integrate plan tracking into real-time EMS**

When auto mode is active and a valid plan exists, use the current plan target before applying live safety bounds. Record stable deviation codes such as `soc_protection`, `temperature_derate`, `forecast_deviation`, `device_fault`, `manual_takeover`, and `communication_loss`.

- [ ] **Step 5: Add daily generation job and APIs**

Register one configurable daily generation time. Add GET current plan, POST generate, and GET solver status endpoints. If generation fails, return the failure status without deleting the prior valid plan.

- [ ] **Step 6: Run focused tests**

Run: `python -m pytest -q tests/test_storage_dispatch_service.py tests/test_storage_dispatch_api.py tests/test_storage_ems_service.py tests/test_scheduler_registry.py`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add app/services/devices/storage/dispatch_service.py app/services/devices/storage/ems_service.py app/services/scheduler_jobs.py app/services/scheduler_registry.py app/api/endpoints/devices/storage.py app/api/endpoints/devices/storage_schemas.py tests/test_storage_dispatch_service.py tests/test_storage_dispatch_api.py
git commit -m "feat: execute storage day ahead plans"
```

## Task 13: Add system-level PV-storage overview and comparison APIs

**Files:**
- Create: `app/services/storage_energy_service.py`
- Create: `app/api/endpoints/energy/storage.py`
- Modify: `app/api/endpoints/energy/__init__.py`
- Test: `tests/test_storage_energy_service.py`
- Test: `tests/test_storage_energy_api.py`

- [ ] **Step 1: Write failing aggregation tests**

Given the same 96-slot scenario, assert the service returns:

```python
{
    "current": {"load_kw": 420.0, "pv_kw": 100.0, "grid_kw": 200.0, "storage_kw": -120.0, "soc": 68.4},
    "strategies": {
        "baseline": {"cost": 0.0, "peak_grid_kw": 0.0, "pv_self_use_rate": 0.0, "curtailment_kwh": 0.0, "equivalent_cycles": 0.0},
        "rule": {"cost": 0.0, "peak_grid_kw": 0.0, "pv_self_use_rate": 0.0, "curtailment_kwh": 0.0, "equivalent_cycles": 0.0},
        "day_ahead": {"cost": 0.0, "peak_grid_kw": 0.0, "pv_self_use_rate": 0.0, "curtailment_kwh": 0.0, "equivalent_cycles": 0.0},
    },
}
```

Use calculated expected values in the actual fixture; do not hardcode improvement percentages in production.

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest -q tests/test_storage_energy_service.py tests/test_storage_energy_api.py`

Expected: FAIL because service and routes do not exist.

- [ ] **Step 3: Implement comparison calculations**

Compute grid import, cost, peak, self-use, curtailment, throughput, equivalent cycles, terminal SOC, and plan execution rate. The comparison endpoint accepts a fixed `scenario_key`, `seed`, and `initial_soc`; the service builds one immutable 96-slot input series and deterministically replays baseline, rule, and day-ahead strategies against that exact series. Current-state and plan-execution metrics may read persisted telemetry/plan rows, but cross-strategy comparisons must not splice together observations from different runs. Return the replay parameters and input-series checksum so results are reproducible without adding a simulation-run table in this milestone.

- [ ] **Step 4: Add scoped read APIs**

Add `/energy/storage/overview` and `/energy/storage/comparison`; filter devices through existing access-control helpers. Return explicit `data_source`, `scenario_key`, `seed`, `initial_soc`, and input-series checksum metadata.

- [ ] **Step 5: Run focused tests**

Run: `python -m pytest -q tests/test_storage_energy_service.py tests/test_storage_energy_api.py`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/services/storage_energy_service.py app/api/endpoints/energy/storage.py app/api/endpoints/energy/__init__.py tests/test_storage_energy_service.py tests/test_storage_energy_api.py
git commit -m "feat: add pv storage overview analytics"
```

## Task 14: Add the PV-storage EMS workspace to existing energy management

**Files:**
- Create: `frontend/src/api/storageEnergy.ts`
- Create: `frontend/src/features/energy-management/storage-ems/StorageEmsWorkspace.vue`
- Create: `frontend/src/features/energy-management/storage-ems/components/StorageEnergyFlow.vue`
- Create: `frontend/src/features/energy-management/storage-ems/components/StoragePowerTrend.vue`
- Create: `frontend/src/features/energy-management/storage-ems/components/StorageDispatchPanel.vue`
- Create: `frontend/src/features/energy-management/storage-ems/components/StorageScenarioPanel.vue`
- Create: `frontend/src/features/energy-management/storage-ems/components/StorageStrategyComparison.vue`
- Create: `frontend/src/features/energy-management/storage-ems/composables/useStorageEms.ts`
- Modify: `frontend/src/views/EnergyManagement.vue`
- Test: `frontend/src/features/energy-management/storage-ems/__tests__/StorageEmsWorkspace.test.ts`
- Test: `frontend/src/views/__tests__/EnergyManagement.test.ts`

- [ ] **Step 1: Write failing workspace and reuse tests**

Add a focused component test that mounts `StorageEmsWorkspace` with calculated API fixtures and asserts load/PV/grid/storage flow values, target-versus-actual power, `仿真数据`, fallback reason, and baseline/rule/day-ahead comparison rows. Extend `EnergyManagement.test.ts` with this route-reuse assertion:

```typescript
it('opens 光储 EMS inside the existing energy management page', async () => {
  const wrapper = mountEnergyManagement()
  await wrapper.get('[data-testid="workspace-storage-ems"]').trigger('click')
  expect(wrapper.findComponent({ name: 'StorageEmsWorkspace' }).exists()).toBe(true)
  expect(wrapper.find('[data-testid="energy-overview-workspace"]').exists()).toBe(false)
})
```

Do not add or modify a router test: `/energy` remains the only route for this workspace.

- [ ] **Step 2: Run and verify failure**

Run:

```bash
cd frontend
npm run test:unit -- src/features/energy-management/storage-ems src/views/__tests__/EnergyManagement.test.ts
```

Expected: FAIL because `StorageEmsWorkspace`, the workspace selector, and the typed API do not exist.

- [ ] **Step 3: Add typed API and composable**

Define exact overview/comparison/request types in `storageEnergy.ts`. Implement `useStorageEms` as the only owner of loading, error, scenario, seed, initial SOC, refresh, plan generation, and comparison state:

```typescript
function toErrorMessage(reason: unknown): string {
  return reason instanceof Error && reason.message ? reason.message : '光储 EMS 数据加载失败'
}

export function useStorageEms() {
  const scenario = ref<StorageScenarioKey>('sunny_workday')
  const seed = ref(20260716)
  const initialSoc = ref(50)
  const overview = ref<StorageEnergyOverview | null>(null)
  const comparison = ref<StorageStrategyComparisonResult | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function refresh() {
    loading.value = true
    error.value = null
    try {
      overview.value = await getStorageEnergyOverview()
    } catch (reason) {
      error.value = toErrorMessage(reason)
    } finally {
      loading.value = false
    }
  }

  async function generatePlan(deviceId: number) {
    await generateStorageDispatchPlan(deviceId, { scenario_key: scenario.value, seed: seed.value, initial_soc: initialSoc.value })
    await refresh()
  }

  async function compareStrategies() {
    comparison.value = await getStorageStrategyComparison({ scenario_key: scenario.value, seed: seed.value, initial_soc: initialSoc.value })
  }

  return { scenario, seed, initialSoc, overview, comparison, loading, error, refresh, generatePlan, compareStrategies }
}
```

Define `getStorageEnergyOverview`, `generateStorageDispatchPlan`, and `getStorageStrategyComparison` in `storageEnergy.ts`; import those three API functions explicitly in the composable and keep `toErrorMessage` local to that focused file.

Components stay presentational and emit scenario, refresh, and generate actions. They must not call APIs directly.

- [ ] **Step 4: Add the existing-page workspace selector**

In `EnergyManagement.vue`, add `activeWorkspace = ref<'overview' | 'storage_ems'>('overview')` and two accessible selector buttons with `data-testid="workspace-overview"` and `data-testid="workspace-storage-ems"`. Keep the existing energy overview subtree unchanged under `v-if="activeWorkspace === 'overview'"`; mount `StorageEmsWorkspace` under the alternative branch. Do not modify `frontend/src/router/index.ts` or `frontend/src/layout/Layout.vue`.

- [ ] **Step 5: Compose the storage EMS workspace**

Use the energy-flow strip above one dominant power/SOC trend. Place dispatch, scenario, and strategy comparison below it. Render missing values as `--`; render `data_source=simulated` as a persistent `仿真数据` badge and `data_source=real` as `真实设备`. Display optimizer status and fallback reason without fabricating plan success.

- [ ] **Step 6: Run focused tests, typecheck, and build**

Run:

```bash
cd frontend
npm run test:unit -- src/features/energy-management/storage-ems src/views/__tests__/EnergyManagement.test.ts src/features/device-monitor/components/storage src/features/device-monitor/composables/__tests__/useStorageMonitor.test.ts
npm run typecheck
npm run build
```

Expected: focused tests, typecheck, and build PASS; no new route or menu item exists.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/api/storageEnergy.ts frontend/src/features/energy-management/storage-ems frontend/src/views/EnergyManagement.vue frontend/src/views/__tests__/EnergyManagement.test.ts
git commit -m "feat: add storage ems energy workspace"
```

## Task 15: Prove adapter replacement, safe cutover, and deterministic end-to-end behavior

**Files:**
- Create: `app/services/devices/storage/simulation_cutover_service.py`
- Create: `tests/test_storage_simulation_cutover.py`
- Create: `tests/test_storage_simulator_e2e.py`
- Create: `scripts/python/storage_cutover.py`
- Create: `scripts/python/run_storage_demo.py`
- Create: `docs/guides/storage-simulation-demo.md`
- Modify: `scripts/python/README.md`
- Modify: `README.md`
- Modify: `docs/plans/PLAN-20260716-campus-pv-storage-simulation.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Write failing exact-device cutover tests**

Create two storage devices with mixed `simulated` and `real` telemetry, plans, and control logs. Lock preview and execution behavior:

```python
preview = StorageSimulationCutoverService.preview(session, device_id=simulated_device.id)
assert preview.telemetry_count == 12
assert preview.plan_count == 96
assert preview.control_log_count == 3

result = StorageSimulationCutoverService.execute(
    session,
    device_id=simulated_device.id,
    expected=preview,
    operator="admin",
)
assert result.deleted == preview
assert remaining_real_rows(session, simulated_device.id) == original_real_rows
assert rows_for_device(session, other_device.id) == original_other_rows
```

Also assert execution is rejected when `ems_auto_enabled=true`, recent simulated telemetry indicates the simulator is still active, expected counts differ from current counts, the device category is not `storage`, or no explicit operator is supplied.

- [ ] **Step 2: Run cutover tests and verify failure**

Run: `python -m pytest -q tests/test_storage_simulation_cutover.py`

Expected: FAIL because the cutover service and script do not exist.

- [ ] **Step 3: Implement preview-first transactional cutover**

`StorageSimulationCutoverService.preview` must count only the exact device's `StorageTelemetry.data_source=simulated`, `StorageDispatchPlan.data_source=simulated`, and `DeviceControlLog` rows whose `command_source=storage-control-api` and structured reason contains `data_source=simulated`. `execute` must acquire device-scoped row locks, re-check all blockers and expected counts, delete the three allowlisted record groups in one transaction, and write one audit event containing device, operator, counts, and timestamp. It must never delete the device archive, asset profile, permissions, real telemetry, or another device's rows.

- [ ] **Step 4: Add an explicit CLI with no implicit deletion**

`storage_cutover.py` must require `--device-code` and exactly one mode. Preview is read-only:

```bash
python scripts/python/storage_cutover.py --device-code STO-001 --preview
```

Execution requires the operator and all three preview counts; count drift aborts without deletion:

```bash
python scripts/python/storage_cutover.py --device-code STO-001 --execute --operator admin --expected-telemetry 12 --expected-plans 96 --expected-control-logs 3
```

Do not add this low-frequency tool to `bin/` and do not invoke `--execute` in automated demo or release verification.

- [ ] **Step 5: Write failing deterministic adapter-replacement acceptance test**

Run a compressed sunny workday through baseline, rules, and day-ahead strategies. Assert midday charging, evening discharging, hard SOC bounds, safety rejection, terminal receipts, calculated comparisons, and persistent simulated labels. Then stop the simulator adapter, feed one contract-valid `data_source=real` payload through the same ingestion entry, and assert the same storage service/API response changes source without changing device id, route, or response shape.

- [ ] **Step 6: Run the end-to-end test and verify failure**

Run: `python -m pytest -q tests/test_storage_simulator_e2e.py`

Expected: FAIL until the demo orchestrator and adapter-replacement fixture exist.

- [ ] **Step 7: Implement one stable demo entrypoint**

`run_storage_demo.py` must accept scenario, speed, seed, and output directory; start or connect to the simulator; run the selected day; write raw JSON/CSV and summary JSON; exit nonzero when acceptance invariants fail. It must never perform simulated-data deletion and must not be added to `bin/`.

- [ ] **Step 8: Document demo and real-device handoff**

Document exact startup commands, the original storage device page, the existing energy-management `光储 EMS` workspace, five scenarios, metric definitions, sign convention, persistent source labels, cutover preview, troubleshooting, canonical MQTT fields, and the boundary between simulated BMS/PCS and the future vendor gateway. State that real automatic control remains disabled until field acceptance is complete.

- [ ] **Step 9: Run complete verification**

Run:

```bash
python -m pytest -q
bash ./scripts/shell/run_backend_coverage.sh
cd frontend && npm run typecheck
cd frontend && npm run build
cd frontend && npm run test:unit -- src/features/energy-management/storage-ems src/views/__tests__/EnergyManagement.test.ts src/features/device-monitor/components/storage src/features/device-monitor/composables/__tests__/useStorageMonitor.test.ts
docker compose -f docker-compose.prod.yml --env-file env.prod.example config
python scripts/python/run_storage_demo.py --scenario sunny_workday --seed 20260716 --output-dir artifacts/storage-demo
python scripts/python/storage_cutover.py --device-code STO-001 --preview
```

Expected: backend and frontend focused tests PASS; coverage remains at or above the accepted 73% gate; typecheck, build, Compose validation, demo, and read-only cutover preview exit `0`; no new frontend failures exist.

- [ ] **Step 10: Perform manual visual and interaction QA**

Verify the original storage device route shows source, component state, control lifecycle, and target/actual trends; the existing energy-management route switches to `光储 EMS` without navigation; energy-flow directions match the sign convention; simulated and real fixtures are labeled correctly; control states never claim early success; empty/error states show no fabricated values; laptop layout remains usable.

- [ ] **Step 11: Close the topic documents**

Record actual test counts, calculated scenario results, unresolved risks, cutover preview evidence, and future vendor-gateway handoff. Archive daily status/handoff snapshots and leave the main area serving only the next active topic.

- [ ] **Step 12: Commit Milestone C and closure**

```bash
git add app/services/devices/storage/simulation_cutover_service.py tests/test_storage_simulation_cutover.py tests/test_storage_simulator_e2e.py scripts/python/storage_cutover.py scripts/python/run_storage_demo.py docs/guides/storage-simulation-demo.md scripts/python/README.md README.md docs/plans/PLAN-20260716-campus-pv-storage-simulation.md docs/plans/current-status.md docs/plans/handoff.md docs/plans/daily/2026-07
git commit -m "feat: complete single storage ems simulation"
```

## Final acceptance boundary

The feature is complete only when all three milestones are independently demonstrated:

1. Simulator telemetry reaches MQTT, persistence, API, WebSocket, and the original storage device page with `data_source=simulated`; a contract-valid real fixture can replace the adapter without changing device identity, route, or response shape.
2. Manual and automatic commands have auditable `accepted/running/terminal` receipts, and safety conditions override economic goals.
3. The same deterministic scenario produces baseline, rule, and day-ahead comparisons from raw data inside the existing energy-management `光储 EMS` workspace, with no hard-coded improvement claims.
4. Cutover preview and transaction tests prove that only one exact device's simulated business rows are removable while real rows, other devices, the archive, and the asset profile remain intact.

Future real hardware work replaces only the simulator adapter with a vendor gateway implementing the same MQTT contract. It must confirm vendor-specific sign, scale, alarm, and protection semantics and validate commands against the actual BMS/PCS before `ems_auto_enabled` can be enabled.
