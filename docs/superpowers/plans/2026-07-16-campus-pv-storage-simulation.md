# Campus PV-Storage Simulation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repeatable 500 kWh/250 kW campus PV-storage simulation with MQTT telemetry, storage command receipts, safety-first rule control, 96-slot day-ahead dispatch, and measurable baseline comparisons.

**Architecture:** Extend the existing `storage` device path instead of creating a parallel platform. Pure battery, rule, and dispatch mathematics live in focused domain modules; services orchestrate persistence, MQTT, scheduling, and permissions; the simulator remains a reusable `scripts/python/` tool; Vue pages consume stable device and energy-domain APIs. Delivery proceeds as three vertical milestones: simulated telemetry, closed-loop control, then optimization and benefit analysis.

**Tech Stack:** Python 3.10+, FastAPI, SQLModel, Alembic, APScheduler, paho-mqtt, PuLP/CBC, PostgreSQL/TimescaleDB, Redis, Vue 3, TypeScript, Pinia, Element Plus, ECharts, pytest, Vitest.

---

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

### Backend orchestration

- Modify `app/integrations/mqtt/device_extensions.py`: persist new storage telemetry fields.
- Create `app/services/devices/storage/asset_profile_service.py`: storage profile reads and writes.
- Create `app/services/devices/storage/control_command_service.py`: storage command lifecycle.
- Create `app/services/devices/storage/ems_service.py`: safety-first rule execution and plan tracking.
- Create `app/services/devices/storage/dispatch_service.py`: optimizer invocation and plan persistence.
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
- Create `frontend/src/api/storageEnergy.ts`: system-level overview APIs.
- Create `frontend/src/features/storage-energy/`: energy-flow, trends, dispatch, scenario, and comparison components.
- Create `frontend/src/views/StorageEnergy.vue`: PV-storage page container.
- Modify `frontend/src/router/index.ts` and `frontend/src/layout/Layout.vue`: route and navigation.

### Tests and documentation

- Create focused backend tests named in each task.
- Create focused frontend tests beside each new component/composable.
- Create `tests/test_storage_simulator_e2e.py`: deterministic end-to-end simulation acceptance.
- Create `docs/guides/storage-simulation-demo.md`: five-minute demo and result interpretation.
- Update `README.md` only after the demo entrypoint is stable.

## Task 1: Establish theme governance and migration gate

**Files:**
- Create: `docs/plans/PLAN-20260716-campus-pv-storage-simulation.md`
- Modify only after rules-role approval: `docs/plans/current-status.md`
- Modify only after rules-role approval: `docs/plans/handoff.md`
- Read/Test: `docs/plans/backend-reliability-phase2-inventory.md`
- Test: `tests/test_backend_tooling_contracts.py`

- [ ] **Step 1: Write the formal topic plan**

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

- [ ] **Step 2: Verify the migration prerequisite**

Run:

```bash
python -m pytest -q tests/test_backend_tooling_contracts.py
alembic upgrade head --sql
```

Expected before feature implementation: both commands exit `0`; offline SQL contains the accepted root revision `20260716_0001` and does not perform online database reads. Also run the fresh PostgreSQL, offline, and roundtrip acceptance commands established by the approved phase 2A plan; all three must pass with schema comparison enabled. Phase 2A has now supplied and passed those fixtures, so Task 3 has persistence admission.

- [ ] **Step 3: Stop if the gate is not green**

If either command fails, do not edit models or migrations. Record the exact failing revision in the active backend reliability plan and return ownership to the rules/backend reliability role.

- [ ] **Step 4: Switch the active topic only after approval**

Archive the previous status/handoff snapshot under `docs/plans/daily/2026-07/`, then replace the main sections with the storage topic. Do not append a second topic to the existing main-area files.

- [ ] **Step 5: Commit governance changes**

```bash
git add docs/plans/PLAN-20260716-campus-pv-storage-simulation.md docs/plans/current-status.md docs/plans/handoff.md docs/plans/daily/2026-07
git commit -m "docs: start campus pv storage simulation"
```

## Task 2: Implement the pure battery state model

**Files:**
- Create: `app/domain/storage_simulation.py`
- Test: `tests/test_storage_simulation_domain.py`

- [ ] **Step 1: Write failing energy-balance tests**

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

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest -q tests/test_storage_simulation_domain.py`

Expected: FAIL with `ModuleNotFoundError: app.domain.storage_simulation`.

- [ ] **Step 3: Implement the minimal pure model**

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

- [ ] **Step 4: Add boundary tests**

Add tests for rated power clipping, ramping, direction change through zero, SOC ceiling, finite inputs, and `seconds > 0`. Reject invalid configuration with `ValueError` rather than returning NaN.

- [ ] **Step 5: Run focused tests**

Run: `python -m pytest -q tests/test_storage_simulation_domain.py`

Expected: all storage simulation domain tests PASS.

- [ ] **Step 6: Commit**

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

- [ ] **Step 1: Write failing CLI and payload tests**

```python
from scripts.python.storage_simulator import SimulatorConfig, build_telemetry_payload


def test_simulator_payload_is_explicitly_simulated():
    payload = build_telemetry_payload(SimulatorConfig(device_code="STO-001"), timestamp="2026-07-16T10:00:00+08:00")
    assert payload["device_category"] == "storage"
    assert payload["device_subtype"] == "battery_energy_storage_system"
    assert payload["data_source"] == "simulated"
    assert payload["active_power"] == 0.0
```

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest -q tests/test_storage_simulator_cli.py`

Expected: FAIL because the simulator module does not exist.

- [ ] **Step 3: Implement the simulator CLI**

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

- [ ] **Step 4: Verify deterministic output**

Run:

```bash
python scripts/python/storage_simulator.py --print-only --seed 20260716
python -m pytest -q tests/test_storage_simulator_cli.py tests/test_storage_settings.py
```

Expected: JSON contains `data_source=simulated`; tests PASS; repeated runs with the same seed match after excluding the generated timestamp.

- [ ] **Step 5: Document the entrypoint**

Add the exact command, MQTT topics, sign convention, supported scenarios, and a warning that the tool is a system-level simulator rather than real BMS/PCS firmware.

- [ ] **Step 6: Commit Milestone A**

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
- Test: `tests/test_storage_control_command_service.py`
- Test: `tests/test_storage_control_receipts.py`

- [ ] **Step 1: Write failing command lifecycle tests**

```python
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


def test_storage_receipt_dispatches_by_device_category(session, storage_device, pending_storage_log):
    log = process_device_control_receipt(
        session,
        {"message_type": "control_receipt", "command_id": str(pending_storage_log.id), "result": "success"},
        storage_device.id,
    )
    assert log.result == "success"
```

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest -q tests/test_storage_control_command_service.py tests/test_storage_control_receipts.py`

Expected: FAIL because the storage command service and dispatcher do not exist.

- [ ] **Step 3: Define fixed storage command specs**

Support only:

```python
SUPPORTED_STORAGE_COMMANDS = {"set_active_power", "set_control_mode", "stop"}
SUPPORTED_RESULTS = {"accepted", "running", "success", "failed", "timeout", "rejected"}
PENDING_RESULTS = {"accepted", "running"}
TERMINAL_RESULTS = {"success", "failed", "timeout", "rejected"}
```

Validate finite power, rated-power bounds from `StorageAssetProfile`, source in `manual/rule/day_ahead`, mode in `auto/manual`, and one pending storage command per device.

- [ ] **Step 4: Implement storage control service**

Reuse `DeviceControlLog`, `publish_control_payload_async`, row locking, pending-command timeout, idempotent terminal receipts, and realtime control-log events. Use `command_source="storage-control-api"`; encode target power and source into a structured JSON reason until a future generic control-detail table is separately approved.

- [ ] **Step 5: Add category-aware receipt dispatch**

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

- [ ] **Step 6: Add timeout job**

Create `expire_storage_control_timeouts()` in `scheduler_jobs.py` and register it at the same cadence as compensation timeout convergence. It must only update `storage-control-api` pending logs.

- [ ] **Step 7: Run focused tests**

Run:

```bash
python -m pytest -q tests/test_storage_control_command_service.py tests/test_storage_control_receipts.py tests/test_mqtt_processor.py tests/test_capacitor_bank_control_command_service_boundary.py
```

Expected: all PASS; compensation receipt tests remain green.

- [ ] **Step 8: Commit**

```bash
git add app/services/devices/storage/specs.py app/services/devices/storage/control_command_service.py app/integrations/mqtt/control_receipts.py app/integrations/mqtt/processor.py app/services/scheduler_jobs.py tests/test_storage_control_command_service.py tests/test_storage_control_receipts.py
git commit -m "feat: add storage control receipt lifecycle"
```

## Task 7: Expose storage asset and control APIs

**Files:**
- Create: `app/api/endpoints/devices/storage_schemas.py`
- Create: `app/services/devices/storage/asset_profile_service.py`
- Modify: `app/api/endpoints/devices/storage.py`
- Test: `tests/test_storage_device_nested_api.py`

- [ ] **Step 1: Write failing API boundary tests**

Test:

```text
GET  /devices/{id}/storage/profile
PUT  /devices/{id}/storage/profile
GET  /devices/{id}/storage/control/capabilities
POST /devices/{id}/storage/control
GET  /devices/{id}/storage/simulation/capabilities
POST /devices/{id}/storage/simulation/control
```

Assert viewers can read but cannot control; maintainer/operator/admin can control within location scope; invalid power returns 400; unknown device returns the existing access-control response; simulator endpoints return 404 while `STORAGE_SIMULATION_ENABLED=false`.

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest -q tests/test_storage_device_nested_api.py`

Expected: new endpoint tests FAIL with 404 or missing schema imports.

- [ ] **Step 3: Add explicit Pydantic/SQLModel schemas**

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

- [ ] **Step 4: Implement thin endpoints**

Endpoints perform dependency injection, permission checks, audit logging, service calls, and response conversion only. Keep validation and command lifecycle in services. Simulator endpoints publish only to `campus/simulation/{device_code}/control`, require the explicit simulation flag, and never share the production device-control topic.

- [ ] **Step 5: Run API tests**

Run: `python -m pytest -q tests/test_storage_device_nested_api.py tests/test_access_control.py`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/api/endpoints/devices/storage_schemas.py app/services/devices/storage/asset_profile_service.py app/api/endpoints/devices/storage.py tests/test_storage_device_nested_api.py
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

- [ ] **Step 1: Write failing rule-priority tests**

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

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest -q tests/test_storage_control_rules.py`

Expected: FAIL because the rule module does not exist.

- [ ] **Step 3: Implement pure rules**

Use immutable input/decision dataclasses. Fixed priority is safety, PV surplus, demand limit, tariff, idle. Add 5 kW deadband, SOC/temperature hysteresis, minimum run/stop durations, and direction-change standby. Return both target power and a stable reason code.

- [ ] **Step 4: Implement EMS orchestration**

`StorageEmsService.evaluate_device` loads latest telemetry/profile and current campus load/PV/tariff inputs, invokes the pure rule, and queues a command only when:

- device is auto mode;
- no pending command exists;
- target differs from current target outside deadband;
- minimum timing constraints permit a transition.

The service does not publish directly if the rule returns a safety stop already represented by a pending stop command.

- [ ] **Step 5: Register the 60-second rule job**

Register the job only when `STORAGE_EMS_ENABLED=true`, using the default-off typed setting introduced with the simulator. Adding the rule service must not change the default runtime behavior.

- [ ] **Step 6: Run focused tests**

Run: `python -m pytest -q tests/test_storage_control_rules.py tests/test_storage_ems_service.py tests/test_scheduler_registry.py`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add app/domain/storage_control_rules.py app/services/devices/storage/ems_service.py app/services/scheduler_jobs.py app/services/scheduler_registry.py tests/test_storage_control_rules.py tests/test_storage_ems_service.py
git commit -m "feat: add storage safety and realtime ems rules"
```

## Task 9: Complete simulator command execution and fault injection

**Files:**
- Modify: `scripts/python/storage_simulator.py`
- Test: `tests/test_storage_simulator_control.py`

- [ ] **Step 1: Write failing command execution tests**

Cover `accepted -> running -> success`, SOC rejection, overtemperature rejection, timeout injection, duplicate `command_id`, manual/auto mode, stop, actual-power tolerance, scenario switching, speed changes, and fault injection over the separate simulator-only topic.

Use this success criterion:

```python
assert abs(actual_power_kw - target_power_kw) <= max(2.5, abs(target_power_kw) * 0.02)
```

and require it to hold for three consecutive simulator steps before `success`.

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest -q tests/test_storage_simulator_control.py`

Expected: lifecycle assertions FAIL.

- [ ] **Step 3: Implement command state machine**

Use states `accepted`, `running`, and one terminal result. Cache terminal results by `command_id` so duplicate delivery republishes the same receipt without applying the action twice. Fault injection accepts only the fixed scenario keys from the design rather than arbitrary code execution. Reject simulator-only messages unless `STORAGE_SIMULATION_ENABLED=true`; never accept `set_scenario`, `set_speed`, or `inject_fault` on the real-device control topic.

- [ ] **Step 4: Run simulator control tests**

Run: `python -m pytest -q tests/test_storage_simulator_cli.py tests/test_storage_simulator_control.py`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/python/storage_simulator.py tests/test_storage_simulator_control.py
git commit -m "feat: simulate storage command execution"
```

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

- [ ] **Step 1: Write failing frontend tests**

Assert:

- simulated telemetry shows a visible `仿真数据` badge;
- positive target power is labeled charging and negative target power discharging;
- viewer controls are disabled;
- manual setpoint emits `set_active_power` with the unchanged sign;
- a pending command disables conflicting controls;
- rejected/timeout receipts show the backend reason.

- [ ] **Step 2: Run focused tests and verify failure**

Run:

```bash
cd frontend
npm run test:unit -- src/features/device-monitor/composables/__tests__/useStorageMonitor.test.ts src/features/device-monitor/components/storage/__tests__/StorageControlPanel.test.ts src/features/device-monitor/components/storage/__tests__/StorageCommandTimeline.test.ts
```

Expected: FAIL because components and APIs do not exist.

- [ ] **Step 3: Extend frontend contracts**

Add the eight telemetry fields, profile/capability types, simulator scenario types, and:

```typescript
export function sendStorageControl(deviceId: number, body: StorageControlRequest) {
  return request.post<never, StorageControlResponse>(`/devices/${deviceId}/storage/control`, body)
}
```

- [ ] **Step 4: Add composable state and actions**

Keep requests in `useStorageMonitor`; components receive props and emit actions. On accepted commands, show accepted state and refresh overview/control logs. WebSocket control-log events update the timeline without fabricating success.

- [ ] **Step 5: Compose the workbench**

Add target/actual power, available power, BMS/PCS/grid state, data source, manual/auto controls, stop, and command timeline. Keep existing SOC/trends/status panels; do not rewrite unrelated monitor components.

- [ ] **Step 6: Run focused tests, typecheck, and build**

Run:

```bash
cd frontend
npm run test:unit -- src/features/device-monitor
npm run typecheck
npm run build
```

Expected: all storage/device-monitor tests PASS; typecheck and build exit `0`. Record the four unrelated baseline unit failures separately if a full unit run is repeated.

- [ ] **Step 7: Commit Milestone B**

```bash
git add frontend/src/api/storage.ts frontend/src/features/device-monitor/composables/useStorageMonitor.ts frontend/src/features/device-monitor/components/storage frontend/src/features/device-monitor/views/StorageMonitorView.vue
git commit -m "feat: add storage control workbench"
```

## Task 11: Implement the day-ahead MILP optimizer

**Files:**
- Modify: `requirements.txt`
- Modify: `constraints-ci.txt`
- Create: `app/domain/storage_dispatch_optimizer.py`
- Test: `tests/test_storage_dispatch_optimizer.py`

- [ ] **Step 1: Pin PuLP**

Add one compatible pinned PuLP version to both dependency files and verify `pip check`. Do not add Gurobi or another commercial runtime.

- [ ] **Step 2: Write failing optimizer tests**

Create a deterministic 96-slot sunny-day input and assert:

- 96 results are returned;
- no slot charges and discharges simultaneously;
- SOC stays within 15%-85%;
- end SOC meets target;
- grid import is non-negative;
- maximum grid import is lower than the no-storage baseline;
- repeated solve returns identical rounded results.

- [ ] **Step 3: Run and verify failure**

Run: `python -m pytest -q tests/test_storage_dispatch_optimizer.py`

Expected: FAIL because the optimizer module does not exist.

- [ ] **Step 4: Implement the MILP**

Use PuLP variables `charge_kw[t]`, `discharge_kw[t]`, `grid_kw[t]`, `soc[t]`, binary `is_charging[t]`, `is_discharging[t]`, `curtail_kw[t]`, and `peak_grid_kw`. Objective terms are energy cost, demand charge, throughput degradation, and curtailment penalty. Return a frozen result object containing solver status, slot results, total cost, peak demand, curtailment, and terminal SOC.

Keep the repository-wide sign convention explicit at the optimizer boundary:

```text
target_active_power[t] = charge_kw[t] - discharge_kw[t]
grid_kw[t] = load_kw[t] - pv_kw[t] + curtail_kw[t] + charge_kw[t] - discharge_kw[t]
```

Update SOC with charge/discharge efficiency at 0.25 h per slot, enforce the 15%-85% soft operating range, enforce mutually exclusive charge/discharge binaries, and require the configured terminal SOC target. Baseline comparison uses zero storage power against the same load/PV/tariff series.

- [ ] **Step 5: Add infeasibility and validation tests**

Reject non-96-length inputs, non-finite values, invalid efficiency, and impossible initial SOC with `ValueError`. Convert non-optimal solver outcomes to `DispatchOptimizationError` with the solver status.

- [ ] **Step 6: Run optimizer tests and dependency check**

Run:

```bash
python -m pip install --constraint constraints-ci.txt -r requirements.txt
python -m pip check
python -m pytest -q tests/test_storage_dispatch_optimizer.py
```

Expected: dependency check and tests PASS.

- [ ] **Step 7: Commit**

```bash
git add requirements.txt constraints-ci.txt app/domain/storage_dispatch_optimizer.py tests/test_storage_dispatch_optimizer.py
git commit -m "feat: add storage day ahead optimizer"
```

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

Persist all 96 rows only after an optimal result exists. Mark the prior plan invalid in the same transaction. Use strategy `day_ahead`, a semantic version string, and a generated-at timestamp.

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

## Task 14: Build the PV-storage overview and dispatch UI

**Files:**
- Create: `frontend/src/api/storageEnergy.ts`
- Create: `frontend/src/views/StorageEnergy.vue`
- Create: `frontend/src/features/storage-energy/components/StorageEnergyFlow.vue`
- Create: `frontend/src/features/storage-energy/components/StoragePowerTrend.vue`
- Create: `frontend/src/features/storage-energy/components/StorageDispatchPanel.vue`
- Create: `frontend/src/features/storage-energy/components/StorageScenarioPanel.vue`
- Create: `frontend/src/features/storage-energy/components/StorageStrategyComparison.vue`
- Create: `frontend/src/features/storage-energy/composables/useStorageEnergy.ts`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/layout/Layout.vue`
- Test: `frontend/src/features/storage-energy/__tests__/StorageEnergy.test.ts`
- Test: `frontend/src/router/__tests__/storageEnergyRoute.test.ts`

- [ ] **Step 1: Write failing page tests**

Assert the page renders one dominant energy-flow/trend workspace, not a grid of equal-weight cards; displays load/PV/grid/storage values; distinguishes plan and actual power; labels simulated data; shows optimizer fallback; switches fixed scenarios; and compares baseline/rule/day-ahead results.

- [ ] **Step 2: Run and verify failure**

Run:

```bash
cd frontend
npm run test:unit -- src/features/storage-energy src/router/__tests__/storageEnergyRoute.test.ts
```

Expected: FAIL because route and components do not exist.

- [ ] **Step 3: Add typed API and composable**

The composable owns loading, error, scenario, refresh, generate-plan, and comparison state. Components remain presentational and emit actions.

- [ ] **Step 4: Compose the page and route**

Add `/storage-energy` with title `光储协同`; add one menu entry under the energy mainline. Use the main trend as the visual anchor, an energy-flow strip above, and dispatch/comparison/scenario sections below. Missing values render `--`; simulated values show a persistent badge.

- [ ] **Step 5: Run focused tests, typecheck, and build**

Run:

```bash
cd frontend
npm run test:unit -- src/features/storage-energy src/features/device-monitor/components/storage src/features/device-monitor/composables/__tests__/useStorageMonitor.test.ts
npm run typecheck
npm run build
```

Expected: focused tests, typecheck, and build PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api/storageEnergy.ts frontend/src/views/StorageEnergy.vue frontend/src/features/storage-energy frontend/src/router/index.ts frontend/src/layout/Layout.vue
git commit -m "feat: add campus pv storage workspace"
```

## Task 15: Add deterministic end-to-end demo and final verification

**Files:**
- Create: `tests/test_storage_simulator_e2e.py`
- Create: `scripts/python/run_storage_demo.py`
- Create: `docs/guides/storage-simulation-demo.md`
- Modify: `scripts/python/README.md`
- Modify: `README.md`
- Modify: `docs/plans/PLAN-20260716-campus-pv-storage-simulation.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Write failing deterministic acceptance test**

Run a compressed sunny workday through baseline, rules, and day-ahead strategies. Assert:

- midday surplus produces positive storage power;
- evening demand-limit event produces negative storage power;
- SOC remains inside hard bounds;
- low-SOC command returns `rejected`;
- overtemperature transitions from derating to stop;
- every command reaches one terminal state;
- day-ahead peak grid power is no worse than baseline;
- all reported improvements are calculated from raw series.

- [ ] **Step 2: Run and verify failure**

Run: `python -m pytest -q tests/test_storage_simulator_e2e.py`

Expected: FAIL until the demo orchestrator exists.

- [ ] **Step 3: Implement one stable demo entrypoint**

`run_storage_demo.py` must accept scenario, speed, seed, and output directory; start or connect to the simulator; run the selected day; write raw JSON/CSV and a summary JSON; exit nonzero when acceptance invariants fail. It must not be added to `bin/`.

- [ ] **Step 4: Document the five-minute demo**

Document exact startup commands, expected page, five scenarios, metric definitions, sign convention, simulator label, troubleshooting, and the boundary between simulated BMS/PCS and future real hardware.

- [ ] **Step 5: Run complete verification**

Run:

```bash
python -m pytest -q
bash ./scripts/shell/run_backend_coverage.sh
cd frontend && npm run typecheck
cd frontend && npm run build
cd frontend && npm run test:unit -- src/features/storage-energy src/features/device-monitor/components/storage src/features/device-monitor/composables/__tests__/useStorageMonitor.test.ts
docker compose -f docker-compose.prod.yml --env-file env.prod.example config
python scripts/python/run_storage_demo.py --scenario sunny_workday --seed 20260716 --output-dir artifacts/storage-demo
```

Expected:

- backend tests PASS with no regression from the accepted baseline;
- coverage does not drop below the current 73% gate;
- frontend storage-focused tests, typecheck, and build PASS;
- Compose validation exits `0`;
- demo exits `0` and writes raw series plus calculated summary;
- the four pre-existing unrelated frontend unit failures are either unchanged or separately resolved; no new failures exist.

- [ ] **Step 6: Perform manual visual and interaction QA**

Verify in the browser:

- energy-flow directions match the sign convention;
- plan and actual power are visually distinct;
- simulated badge is always visible;
- control states transition without claiming early success;
- error and empty states do not show fabricated values;
- responsive layout remains usable at laptop width.

- [ ] **Step 7: Close the topic documents**

Record actual test counts, calculated scenario results, unresolved risks, and future BMS/PCS handoff. Archive daily status/handoff snapshots and leave the main area serving only the next active topic.

- [ ] **Step 8: Commit Milestone C and closure**

```bash
git add tests/test_storage_simulator_e2e.py scripts/python/run_storage_demo.py docs/guides/storage-simulation-demo.md scripts/python/README.md README.md docs/plans/PLAN-20260716-campus-pv-storage-simulation.md docs/plans/current-status.md docs/plans/handoff.md docs/plans/daily/2026-07
git commit -m "feat: complete campus pv storage simulation"
```

## Final acceptance boundary

The feature is complete only when all three milestones are independently demonstrated:

1. Simulator telemetry reaches MQTT, persistence, API, WebSocket, and the storage page with `data_source=simulated`.
2. Manual and automatic commands have auditable `accepted/running/terminal` receipts, and safety conditions override economic goals.
3. The same deterministic scenario produces baseline, rule, and day-ahead comparisons from raw data, with no hard-coded improvement claims.

Future real hardware work is a separate plan. It must replace the simulator adapter, confirm vendor-specific sign/scale/protection semantics, add operational approval boundaries, and validate commands against the actual BMS/PCS before any real-device claim is made.
