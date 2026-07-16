# Backend Reliability Phase 2A Deterministic Migration Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the disposable legacy Alembic chain with one static Campus EMS baseline, prove online/offline/roundtrip TimescaleDB migrations, remove startup schema mutation, and restore a blocking CI migration gate so storage persistence can safely begin.

**Architecture:** Archive revisions `20260325_0001` through `20260515_0011`, generate and hand-review a static root revision `20260716_0001`, and validate it through a reusable safety-checked PostgreSQL verifier. Application startup becomes validation-only; the current disposable development database is rebuilt only after three isolated migration paths produce identical schema fingerprints.

**Tech Stack:** Python 3.10+, Alembic, SQLAlchemy, SQLModel, psycopg2, PostgreSQL 14, TimescaleDB 2.17.2, Docker Compose, pytest, GitHub Actions.

---

## Execution prerequisites

1. Work only in `/Users/todo/CampusEnergySystem/.worktrees/campus-pv-storage-plan` on `codex/campus-pv-storage-plan`.
2. Read `AGENTS.md`, `docs/plans/current-status.md`, `docs/plans/handoff.md`, `docs/guides/product-positioning.md`, `docs/guides/five-role-vibe-coding-framework.md`, `docs/guides/backend-guidelines.md`, and `docs/guides/script-guidelines.md` before implementation.
3. Use the approved design at `docs/superpowers/specs/2026-07-16-backend-reliability-phase2a-migration-baseline-design.md` as the source of truth.
4. The user explicitly approved clearing `campus_energy`, but destructive reset remains Task 8 and must not occur until Tasks 1-7 pass.
5. Never drop or modify a database whose name is not exactly `campus_energy` for the one-time reset or prefixed with `ces_migration_` for temporary verification.
6. Redis and MQTT are out of scope. MQTT being unhealthy does not block this plan.
7. Follow TDD for every production behavior: write the test, observe the intended failure, implement the minimum, rerun focused and related tests.
8. Preserve the original main-worktree user modification to `app/api/README.md`; do not stage or edit it.

## File structure map

### Governance

- Create `docs/plans/PLAN-20260716-backend-reliability-phase2a.md`: formal phase 2A scope, gates and acceptance.
- Modify `docs/plans/current-status.md` and `docs/plans/handoff.md`: temporarily make phase 2A the only active main topic.
- Modify `docs/plans/daily/2026-07/2026-07-16-status.md` and `docs/plans/daily/2026-07/2026-07-16-handoff.md`: append, never overwrite, the paused storage snapshot.
- Create `docs/plans/backend-reliability-phase2a-acceptance.md`: final evidence after the local rebuild.

### Migration verification

- Create `scripts/python/migration_schema.py`: temporary-database name safety, PostgreSQL catalog reads, normalized fingerprints and comparison.
- Create `scripts/python/verify_postgres_migrations.py`: online/offline/roundtrip database orchestration CLI.
- Create `tests/test_postgres_migration_verifier.py`: verifier unit tests without Docker.
- Create `tests/test_postgres_migration_paths.py`: opt-in real PostgreSQL integration acceptance.
- Modify `scripts/python/README.md` and `scripts/SCRIPT_LIST.md`: document the formal migration verifier.

### Alembic baseline

- Move eleven legacy migration files from `migrations/versions/` to `docs/archive/migrations/legacy-pre-20260716/`.
- Create `docs/archive/migrations/legacy-pre-20260716/README.md`: revision inventory and supersession note.
- Create `migrations/versions/20260716_0001_campus_baseline.py`: static root schema and TimescaleDB hypertable creation.
- Create `tests/test_migration_baseline_contract.py`: active-chain and static-content guardrails.

### Runtime and CI

- Modify `app/core/database.py`: validation-only startup.
- Modify `app/core/settings.py`, `app/core/startup_checks.py`, `env.example`, `env.local.example`, and `env.prod.example`: default-off and reject mutation flags.
- Modify `tests/test_database_core.py` and `tests/test_startup_checks.py`: new runtime contract.
- Modify `.github/workflows/backend-ci.yml` and `tests/test_backend_tooling_contracts.py`: blocking TimescaleDB migration job.

### Storage handback

- Modify `docs/superpowers/plans/2026-07-16-campus-pv-storage-simulation.md`: change storage revision to `20260716_0002` and down-revision to `20260716_0001`.
- Modify `docs/plans/PLAN-20260716-campus-pv-storage-simulation.md`, `docs/plans/current-status.md`, and `docs/plans/handoff.md`: release Task 3 only after phase 2A acceptance.

## Task 1: Switch governance to phase 2A without losing storage progress

**Files:**
- Create: `docs/plans/PLAN-20260716-backend-reliability-phase2a.md`
- Create: `tests/test_backend_reliability_phase2a_docs.py`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`
- Modify: `docs/plans/daily/2026-07/2026-07-16-status.md`
- Modify: `docs/plans/daily/2026-07/2026-07-16-handoff.md`

- [ ] **Step 1: Write failing governance tests**

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase2a_is_the_only_active_main_topic():
    status = read("docs/plans/current-status.md")
    handoff = read("docs/plans/handoff.md")
    assert "当前主主题：`后端可靠性阶段 2A：确定性迁移基线`" in status
    assert "当前主题：`后端可靠性阶段 2A：确定性迁移基线`" in handoff
    assert "园区光储协同仿真与 EMS 控制`。" not in status


def test_storage_task2_completion_is_preserved_in_daily_snapshot():
    status = read("docs/plans/daily/2026-07/2026-07-16-status.md")
    handoff = read("docs/plans/daily/2026-07/2026-07-16-handoff.md")
    assert "园区光储主题暂停快照" in status
    assert "Task 2" in status and "正式完成" in status
    assert "Task 3" in handoff and "阶段 2A" in handoff
```

- [ ] **Step 2: Run the tests and confirm the intended failure**

Run:

```bash
python -m pytest -q tests/test_backend_reliability_phase2a_docs.py
```

Expected: FAIL because the main status still names storage and no new phase 2A PLAN exists.

- [ ] **Step 3: Create the formal phase 2A PLAN**

Use these fixed headings and decisions:

```markdown
# PLAN-20260716 后端可靠性阶段 2A：确定性迁移基线

## 目标
- 用静态根迁移替代动态旧链。
- online、offline、roundtrip 三条路径得到相同 schema。
- 启动只校验 schema，不修改 schema。
- CI migration 恢复为阻塞门禁。

## 数据边界
- 当前 campus_energy 数据经用户确认可清除。
- 破坏性实验只允许 ces_migration_ 前缀临时库。
- 临时验证全部通过后才重建 campus_energy。

## 非目标
- 不处理 Redis、MQTT、readiness、rate limit、部署顺序或储能持久化。

## 固定版本
- 新根 revision：20260716_0001。
- 后续储能 revision：20260716_0002。

## 验收
- 静态迁移契约通过。
- 三路径指纹一致。
- 开发库重建成功。
- 启动无 schema mutation。
- CI migration 无 continue-on-error。
```

- [ ] **Step 4: Append the storage pause snapshot**

Append a separate `## 园区光储主题暂停快照` section to both existing daily files. Do not rewrite the earlier phase 2A snapshot. Record commits through `efbbe808`, Task 1/2 completion, Task 3 blocker, and the exact resume condition `20260716_0001` accepted.

- [ ] **Step 5: Replace the main status and handoff bodies**

Make phase 2A the only active topic. The next role is backend for migration verification tooling; storage remains a paused dependent topic, not a second main section.

- [ ] **Step 6: Run governance tests and diff checks**

Run:

```bash
python -m pytest -q tests/test_backend_reliability_phase2a_docs.py
git diff --check
```

Expected: governance tests PASS; diff check exits `0`.

- [ ] **Step 7: Commit**

```bash
git add docs/plans/PLAN-20260716-backend-reliability-phase2a.md docs/plans/current-status.md docs/plans/handoff.md docs/plans/daily/2026-07/2026-07-16-status.md docs/plans/daily/2026-07/2026-07-16-handoff.md tests/test_backend_reliability_phase2a_docs.py
git commit -m "docs: start deterministic migration baseline"
```

## Task 2: Build the pure schema-fingerprint and database-safety core

**Files:**
- Create: `scripts/python/migration_schema.py`
- Create: `tests/test_postgres_migration_verifier.py`

- [ ] **Step 1: Write failing name-safety and normalization tests**

```python
import pytest

from scripts.python.migration_schema import (
    MigrationVerificationError,
    compare_fingerprints,
    normalize_fingerprint,
    validate_temporary_database_name,
)


@pytest.mark.parametrize("name", [
    "ces_migration_fresh",
    "ces_migration_offline",
    "ces_migration_roundtrip",
])
def test_accepts_only_fixed_temporary_database_names(name):
    assert validate_temporary_database_name(name) == name


@pytest.mark.parametrize("name", ["campus_energy", "postgres", "ces_migration_", "ces_migration_bad-name"])
def test_rejects_unsafe_database_names(name):
    with pytest.raises(MigrationVerificationError):
        validate_temporary_database_name(name)


def test_fingerprint_normalization_is_order_independent():
    left = {"tables": [{"name": "device", "columns": [{"name": "id", "type": "integer"}]}]}
    right = {"tables": [{"columns": [{"type": "INTEGER", "name": "id"}], "name": "device"}]}
    assert normalize_fingerprint(left) == normalize_fingerprint(right)


def test_comparison_reports_first_differing_object():
    with pytest.raises(MigrationVerificationError, match="device.archive_status"):
        compare_fingerprints(
            {"objects": {"device.archive_status": {"type": "varchar"}}},
            {"objects": {"device.archive_status": {"type": "text"}}},
        )
```

- [ ] **Step 2: Run and confirm module-missing failure**

Run:

```bash
python -m pytest -q tests/test_postgres_migration_verifier.py
```

Expected: collection FAILS with `ModuleNotFoundError: scripts.python.migration_schema`.

- [ ] **Step 3: Implement the safety contract**

```python
TEMP_DATABASE_NAMES = frozenset({
    "ces_migration_fresh",
    "ces_migration_offline",
    "ces_migration_roundtrip",
})


class MigrationVerificationError(RuntimeError):
    pass


def validate_temporary_database_name(name: str) -> str:
    if name not in TEMP_DATABASE_NAMES:
        raise MigrationVerificationError(
            f"refusing database outside fixed migration set: {name!r}"
        )
    return name
```

Implement recursive normalization that lowercases PostgreSQL type spellings, sorts dictionary keys, sorts lists by canonical JSON, and excludes only `alembic_version` plus Timescale internal schemas.

- [ ] **Step 4: Define catalog query responsibilities**

Add constants and `collect_schema_fingerprint(connection)` for:

```python
PUBLIC_COLUMNS_SQL = """
SELECT table_name, column_name, data_type, udt_name, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name <> 'alembic_version'
ORDER BY table_name, ordinal_position
"""

CONSTRAINTS_SQL = """
SELECT tc.table_name, tc.constraint_name, tc.constraint_type,
       kcu.column_name, ccu.table_name AS foreign_table,
       ccu.column_name AS foreign_column,
       rc.update_rule, rc.delete_rule
FROM information_schema.table_constraints tc
LEFT JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
LEFT JOIN information_schema.constraint_column_usage ccu
  ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
LEFT JOIN information_schema.referential_constraints rc
  ON tc.constraint_name = rc.constraint_name AND tc.constraint_schema = rc.constraint_schema
WHERE tc.table_schema = 'public'
ORDER BY tc.table_name, tc.constraint_name, kcu.ordinal_position
"""

INDEXES_SQL = """
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname
"""

HYPERTABLE_SQL = """
SELECT hypertable_name, num_dimensions
FROM timescaledb_information.hypertables
WHERE hypertable_schema = 'public'
ORDER BY hypertable_name
"""
```

Return one JSON-serializable dictionary under `objects`; use stable object keys such as `table.device.column.archive_status`, `table.device.index.ix_device_archive_status`, and `hypertable.energydata`.

- [ ] **Step 5: Add fake-connection tests**

Use a small fake cursor/connection to assert catalog rows become stable object keys and `alembic_version` is excluded. Do not mock the normalization functions themselves.

- [ ] **Step 6: Run tests and Ruff**

```bash
python -m pytest -q tests/test_postgres_migration_verifier.py
ruff check scripts/python/migration_schema.py tests/test_postgres_migration_verifier.py
```

Expected: all tests PASS; Ruff exits `0`.

- [ ] **Step 7: Commit**

```bash
git add scripts/python/migration_schema.py tests/test_postgres_migration_verifier.py
git commit -m "test: add migration schema verification core"
```

## Task 3: Build the isolated PostgreSQL migration verifier CLI

**Files:**
- Create: `scripts/python/verify_postgres_migrations.py`
- Modify: `tests/test_postgres_migration_verifier.py`

- [ ] **Step 1: Write failing orchestration tests**

```python
from scripts.python.verify_postgres_migrations import (
    MigrationPath,
    build_database_url,
    execute_verification,
)


def test_build_database_url_replaces_only_database_name():
    url = build_database_url(
        "postgresql://admin:secret@localhost:5432/postgres",
        "ces_migration_fresh",
    )
    assert url.endswith("/ces_migration_fresh")
    assert "admin:secret@localhost:5432" in url


def test_execute_verification_uses_three_fixed_paths(fake_backend):
    result = execute_verification(fake_backend)
    assert [item.path for item in result.paths] == [
        MigrationPath.FRESH,
        MigrationPath.OFFLINE,
        MigrationPath.ROUNDTRIP,
    ]
    assert all(item.success for item in result.paths)
```

Add failure tests proving a failed database is preserved and cleanup calls only the three validated names.

- [ ] **Step 2: Run and confirm missing-symbol failures**

```bash
python -m pytest -q tests/test_postgres_migration_verifier.py
```

Expected: FAIL because the CLI module and orchestration types do not exist.

- [ ] **Step 3: Implement typed path results**

```python
class MigrationPath(str, Enum):
    FRESH = "fresh"
    OFFLINE = "offline"
    ROUNDTRIP = "roundtrip"


@dataclass(frozen=True)
class PathResult:
    path: MigrationPath
    database_name: str
    success: bool
    fingerprint: dict[str, object] | None
    failed_step: str | None = None


@dataclass(frozen=True)
class VerificationResult:
    paths: tuple[PathResult, ...]

    @property
    def success(self) -> bool:
        return all(item.success for item in self.paths)
```

- [ ] **Step 4: Implement the PostgreSQL backend**

Use `sqlalchemy.engine.make_url` to replace only the database component. Use `psycopg2.connect(admin_url)` with `ISOLATION_LEVEL_AUTOCOMMIT` for `CREATE DATABASE`, forced connection termination, and `DROP DATABASE`. Every method validates the target name first.

`PostgresBackend` exposes these focused methods used by `execute_verification`: `create_database(name)`, `drop_database(name)`, `upgrade(name)`, `downgrade_to_base(name)`, `generate_offline_sql()`, `apply_offline_sql(name, sql)`, and `fingerprint(name)`. Unit tests provide a fake object with the same methods; production orchestration must not branch on the fake type.

When converting the replaced SQLAlchemy URL back to text, call `render_as_string(hide_password=False)` so the subprocess receives the real test-only password; never log that rendered URL.

Use `subprocess.run` with argument arrays, `check=True`, `capture_output=True`, and an environment containing the target `DATABASE_URL`:

```python
[sys.executable, "-m", "alembic", "upgrade", "head"]
[sys.executable, "-m", "alembic", "downgrade", "base"]
[sys.executable, "-m", "alembic", "upgrade", "head", "--sql"]
```

Apply captured offline SQL with a psycopg2 cursor against `ces_migration_offline`. Do not invoke shell parsing or interpolate credentials into command strings.

- [ ] **Step 5: Implement path order and preservation**

```text
fresh: create -> online upgrade -> fingerprint
offline: create -> generate SQL -> execute SQL -> fingerprint
roundtrip: create -> online upgrade -> downgrade base -> online upgrade -> fingerprint
compare: fresh == offline == roundtrip
success cleanup: drop all three unless --keep-success
failure: preserve failing and unverified databases, print exact failed step
```

- [ ] **Step 6: Implement CLI arguments**

```text
--admin-url ADMIN_URL       required unless MIGRATION_ADMIN_URL is set
--keep-success              preserve successful temporary databases
--cleanup                   drop the three fixed temporary databases and exit
--json-output PATH          write the normalized result JSON
```

Never add this low-frequency tool to `bin/`.

- [ ] **Step 7: Run unit tests and help smoke test**

```bash
python -m pytest -q tests/test_postgres_migration_verifier.py
python scripts/python/verify_postgres_migrations.py --help
ruff check scripts/python/migration_schema.py scripts/python/verify_postgres_migrations.py tests/test_postgres_migration_verifier.py
```

Expected: tests PASS; help lists all four arguments; Ruff exits `0`.

- [ ] **Step 8: Commit**

```bash
git add scripts/python/verify_postgres_migrations.py tests/test_postgres_migration_verifier.py
git commit -m "feat: add isolated postgres migration verifier"
```

## Task 4: Archive the legacy chain and create the static root baseline

**Files:**
- Create: `docs/archive/migrations/legacy-pre-20260716/README.md`
- Move: `migrations/versions/20260325_0001_industrial_baseline.py`
- Move: `migrations/versions/20260325_0002_mqtt_retry_dead_letter.py`
- Move: `migrations/versions/20260412_0003_add_reactive_power.py`
- Move: `migrations/versions/20260412_0004_add_svg_tables.py`
- Move: `migrations/versions/20260412_0005_merge_svg_operations_profile.py`
- Move: `migrations/versions/20260414_0006_unify_compensation_type_to_svg.py`
- Move: `migrations/versions/20260414_0007_add_device_subtype.py`
- Move: `migrations/versions/20260423_0008_drop_prediction.py`
- Move: `migrations/versions/20260424_0009_add_capacitor_bank_monitor_fields.py`
- Move: `migrations/versions/20260424_0010_add_device_archive_status.py`
- Move: `migrations/versions/20260515_0011_add_capacitor_bank_harmonic_spectrum.py`
- Create: `migrations/versions/20260716_0001_campus_baseline.py`
- Create: `tests/test_migration_baseline_contract.py`

- [ ] **Step 1: Write the active-chain contract test first**

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / "migrations" / "versions"
ARCHIVE = ROOT / "docs" / "archive" / "migrations" / "legacy-pre-20260716"

REQUIRED_TABLES = {
    "alarm", "audit_event", "capacitor_bank_control_profile",
    "capacitor_bank_telemetry", "carbon_emission", "device",
    "device_control_log", "device_group", "device_group_membership",
    "device_ingestion_health", "device_maintenance", "energy_statistics",
    "energydata", "inspection_plan", "inspection_point", "inspection_record",
    "inspection_route", "inspection_task", "location", "mqtt_ingestion_record",
    "storage_telemetry", "svg_asset_profile", "svg_config", "svg_telemetry", "user",
}


def test_only_static_root_is_active():
    files = sorted(path.name for path in ACTIVE.glob("*.py") if path.name != "__init__.py")
    assert files == ["20260716_0001_campus_baseline.py"]


def test_baseline_is_offline_safe_and_static():
    text = (ACTIVE / "20260716_0001_campus_baseline.py").read_text(encoding="utf-8")
    for forbidden in ["SQLModel", ".metadata", "op.get_bind", "inspect(", "fetchone", "information_schema", "from app"]:
        assert forbidden not in text
    assert 'revision = "20260716_0001"' in text
    assert "down_revision = None" in text
    for table in REQUIRED_TABLES:
        assert f'"{table}"' in text
    assert "CREATE EXTENSION IF NOT EXISTS timescaledb" in text
    assert "create_hypertable" in text
```

Add an archive test requiring exactly eleven legacy Python files and a README that lists all former revision IDs.

- [ ] **Step 2: Run and observe failure against the legacy active directory**

```bash
python -m pytest -q tests/test_migration_baseline_contract.py
```

Expected: FAIL because eleven legacy revisions remain active and the new baseline is absent.

- [ ] **Step 3: Archive legacy revisions with history-preserving moves**

```bash
mkdir -p docs/archive/migrations/legacy-pre-20260716
git mv migrations/versions/20260325_0001_industrial_baseline.py docs/archive/migrations/legacy-pre-20260716/
git mv migrations/versions/20260325_0002_mqtt_retry_dead_letter.py docs/archive/migrations/legacy-pre-20260716/
git mv migrations/versions/20260412_0003_add_reactive_power.py docs/archive/migrations/legacy-pre-20260716/
git mv migrations/versions/20260412_0004_add_svg_tables.py docs/archive/migrations/legacy-pre-20260716/
git mv migrations/versions/20260412_0005_merge_svg_operations_profile.py docs/archive/migrations/legacy-pre-20260716/
git mv migrations/versions/20260414_0006_unify_compensation_type_to_svg.py docs/archive/migrations/legacy-pre-20260716/
git mv migrations/versions/20260414_0007_add_device_subtype.py docs/archive/migrations/legacy-pre-20260716/
git mv migrations/versions/20260423_0008_drop_prediction.py docs/archive/migrations/legacy-pre-20260716/
git mv migrations/versions/20260424_0009_add_capacitor_bank_monitor_fields.py docs/archive/migrations/legacy-pre-20260716/
git mv migrations/versions/20260424_0010_add_device_archive_status.py docs/archive/migrations/legacy-pre-20260716/
git mv migrations/versions/20260515_0011_add_capacitor_bank_harmonic_spectrum.py docs/archive/migrations/legacy-pre-20260716/
```

The README table must include revision, filename, former purpose, known issue, and `superseded by 20260716_0001`.

- [ ] **Step 4: Create an empty authoring database**

```bash
docker exec campusenergysystem-db-1 dropdb -U admin --if-exists ces_migration_fresh
docker exec campusenergysystem-db-1 createdb -U admin ces_migration_fresh
```

This pre-acceptance authoring use of the fixed fresh-path name is temporary. Task 5 recreates it from empty before collecting the acceptance fingerprint.

- [ ] **Step 5: Generate the one-time authoring draft**

```bash
DATABASE_URL=postgresql://admin:password123@localhost:5432/ces_migration_fresh \
python -m alembic revision --autogenerate \
  --rev-id 20260716_0001 \
  -m "campus deterministic baseline"
```

Rename the generated file to `20260716_0001_campus_baseline.py` if Alembic includes a different suffix. Generation is an authoring aid only; the checked-in revision must remain static.

- [ ] **Step 6: Hand-review and complete the baseline**

Ensure the generated header is exactly:

```python
revision = "20260716_0001"
down_revision = None
branch_labels = None
depends_on = None
```

Insert this as the first operation inside `upgrade()`:

```python
op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
```

Insert this immediately after the generated `energydata` table, primary key and indexes exist:

```python
op.execute(
    "SELECT create_hypertable('energydata', 'timestamp', "
    "if_not_exists => TRUE, migrate_data => FALSE)"
)
```

Keep every generated `op.create_table` and `op.create_index` operation needed by the 25-table contract. Keep explicit downgrade operations in reverse dependency order. Do not drop the TimescaleDB extension in downgrade.

Audit all 25 required tables against current model definitions. Do not keep generated type changes, table drops, or objects outside the required set.

- [ ] **Step 7: Remove the authoring database**

```bash
docker exec campusenergysystem-db-1 dropdb -U admin --if-exists ces_migration_fresh
```

- [ ] **Step 8: Run static and offline tests**

```bash
python -m pytest -q tests/test_migration_baseline_contract.py
DATABASE_URL=postgresql://admin:password123@localhost:5432/postgres \
python -m alembic upgrade head --sql > /tmp/phase2a-baseline.sql
test -s /tmp/phase2a-baseline.sql
rg "CREATE TABLE energydata|create_hypertable|CREATE TABLE storage_telemetry" /tmp/phase2a-baseline.sql
```

Expected: tests PASS; offline generation exits `0`; all three statements are found.

- [ ] **Step 9: Commit**

```bash
git add migrations/versions/20260716_0001_campus_baseline.py docs/archive/migrations/legacy-pre-20260716 tests/test_migration_baseline_contract.py
git commit -m "feat: establish deterministic campus schema baseline"
```

## Task 5: Prove online, offline and roundtrip paths against TimescaleDB

**Files:**
- Create: `tests/test_postgres_migration_paths.py`
- Modify: `scripts/python/verify_postgres_migrations.py`
- Modify: `scripts/python/README.md`
- Modify: `scripts/SCRIPT_LIST.md`

- [ ] **Step 1: Write the opt-in integration test**

```python
import os
import pytest

from scripts.python.verify_postgres_migrations import PostgresBackend, execute_verification


ADMIN_URL = os.getenv("MIGRATION_ADMIN_URL")


@pytest.mark.skipif(not ADMIN_URL, reason="MIGRATION_ADMIN_URL is required")
def test_online_offline_and_roundtrip_fingerprints_match():
    result = execute_verification(PostgresBackend(ADMIN_URL))
    assert result.success
    fingerprints = [item.fingerprint for item in result.paths]
    assert fingerprints[0] == fingerprints[1] == fingerprints[2]
    assert fingerprints[0]["objects"]["hypertable.energydata"]["num_dimensions"] == 1
```

- [ ] **Step 2: Run without the environment and verify the intentional skip**

```bash
python -m pytest -q tests/test_postgres_migration_paths.py
```

Expected: `1 skipped` because the administrative URL is intentionally absent.

- [ ] **Step 3: Run the real three-path verifier**

```bash
MIGRATION_ADMIN_URL=postgresql://admin:password123@localhost:5432/postgres \
python scripts/python/verify_postgres_migrations.py \
  --json-output /tmp/phase2a-migration-result.json
```

Expected: fresh, offline, and roundtrip all report success; fingerprints match; successful temporary databases are removed.

- [ ] **Step 4: Run the integration test with Docker PostgreSQL**

```bash
MIGRATION_ADMIN_URL=postgresql://admin:password123@localhost:5432/postgres \
python -m pytest -q tests/test_postgres_migration_paths.py
```

Expected: PASS.

- [ ] **Step 5: Document the formal script**

Add exact local commands, fixed database names, preservation-on-failure behavior, cleanup command, TimescaleDB requirement, and a warning that `campus_energy` is never a verifier target.

- [ ] **Step 6: Verify script documentation and tests**

```bash
python -m pytest -q tests/test_postgres_migration_verifier.py tests/test_postgres_migration_paths.py
python scripts/python/verify_postgres_migrations.py --help
git diff --check
```

Expected: unit and integration tests PASS with `MIGRATION_ADMIN_URL`; help and diff checks succeed.

- [ ] **Step 7: Commit**

```bash
git add tests/test_postgres_migration_paths.py scripts/python/verify_postgres_migrations.py scripts/python/README.md scripts/SCRIPT_LIST.md
git commit -m "test: verify deterministic postgres migration paths"
```

## Task 6: Make application startup validation-only

**Files:**
- Modify: `app/core/database.py`
- Modify: `app/core/settings.py`
- Modify: `app/core/startup_checks.py`
- Modify: `env.example`
- Modify: `env.local.example`
- Modify: `env.prod.example`
- Modify: `tests/test_database_core.py`
- Modify: `tests/test_startup_checks.py`

- [ ] **Step 1: Replace mutation expectations with failing validation tests**

```python
def test_init_db_rejects_legacy_schema_mutation_flags():
    with patch.object(database.settings, "db_auto_create_tables", True):
        with patch.object(database.settings, "db_runtime_schema_sync", False):
            with self.assertRaisesRegex(RuntimeError, "alembic upgrade head"):
                database.init_db()


def test_init_db_only_runs_schema_assertions():
    with patch.object(database.settings, "db_auto_create_tables", False):
        with patch.object(database.settings, "db_runtime_schema_sync", False):
            with patch.object(database, "_assert_required_tables_exist") as tables:
                with patch.object(database, "_assert_required_columns_present") as columns:
                    with patch.object(database, "_assert_required_indexes_present") as indexes:
                        with patch.object(database, "_assert_energydata_hypertable") as hypertable:
                            database.init_db()
    tables.assert_called_once()
    columns.assert_called_once()
    indexes.assert_called_once()
    hypertable.assert_called_once()
```

Update startup-check tests so development and production both reject either mutation flag when strict startup checks are enabled.

- [ ] **Step 2: Run focused tests and confirm old behavior fails**

```bash
python -m pytest -q tests/test_database_core.py tests/test_startup_checks.py
```

Expected: FAIL because `init_db()` still mutates schema and development still permits risky flags.

- [ ] **Step 3: Implement validation-only init_db**

```python
def init_db() -> None:
    if settings.db_auto_create_tables or settings.db_runtime_schema_sync:
        raise RuntimeError(
            "启动时 schema mutation 已禁用；请设置 "
            "DB_AUTO_CREATE_TABLES=False、DB_RUNTIME_SCHEMA_SYNC=False，"
            "然后执行 alembic upgrade head"
        )
    _assert_required_tables_exist()
    _assert_required_columns_present()
    _assert_required_indexes_present()
    _assert_energydata_hypertable()
```

Remove `_sync_runtime_schema`, `_ensure_runtime_indexes`, `_try_enable_timescaledb_hypertable`, and imports used only by those mutation paths.

- [ ] **Step 4: Expand table and index assertions**

Set `REQUIRED_TABLES` to the same 25-table set in Task 4. Add a focused `REQUIRED_INDEXES` map containing at least:

```python
REQUIRED_INDEXES = {
    "alarm": {"ix_alarm_device_id", "idx_alarm_device_resolved_timestamp"},
    "device": {"ix_device_sn", "ix_device_device_category", "ix_device_archive_status"},
    "energydata": {"idx_energydata_device_timestamp", "idx_energydata_energy_type_timestamp"},
    "mqtt_ingestion_record": {"ix_mqtt_ingestion_record_fingerprint", "idx_mqtt_ingestion_record_next_retry_at"},
}
```

Use SQLAlchemy inspector reads only. `_assert_energydata_hypertable()` performs one read-only query against `timescaledb_information.hypertables` and raises `RuntimeError("energydata 尚未通过 migration 转换为 TimescaleDB hypertable")` when absent.

- [ ] **Step 5: Set all environment defaults false**

Change Python defaults and all three environment examples:

```text
DB_AUTO_CREATE_TABLES=False
DB_RUNTIME_SCHEMA_SYNC=False
```

Keep both settings parseable for compatibility; change descriptions to state that `True` is rejected and Alembic owns schema.

- [ ] **Step 6: Run focused and startup regression tests**

```bash
python -m pytest -q tests/test_database_core.py tests/test_startup_checks.py
python scripts/python/check_config.py
python scripts/python/check_production_readiness.py --env-file env.prod.example
ruff check app/core/database.py app/core/settings.py app/core/startup_checks.py tests/test_database_core.py tests/test_startup_checks.py
```

Expected: tests and checks PASS; no schema-mutating function remains in `app/core/database.py`.

- [ ] **Step 7: Run the real startup assertion against a verifier database**

Preserve a successful fresh database:

```bash
MIGRATION_ADMIN_URL=postgresql://admin:password123@localhost:5432/postgres \
python scripts/python/verify_postgres_migrations.py --keep-success
```

Then run:

```bash
DATABASE_URL=postgresql://admin:password123@localhost:5432/ces_migration_fresh \
DB_AUTO_CREATE_TABLES=False DB_RUNTIME_SCHEMA_SYNC=False \
python -c "from app.core.database import init_db; init_db()"
```

Expected: exit `0` with no DDL. Clean the temporary databases afterward:

```bash
MIGRATION_ADMIN_URL=postgresql://admin:password123@localhost:5432/postgres \
python scripts/python/verify_postgres_migrations.py --cleanup
```

- [ ] **Step 8: Commit**

```bash
git add app/core/database.py app/core/settings.py app/core/startup_checks.py env.example env.local.example env.prod.example tests/test_database_core.py tests/test_startup_checks.py
git commit -m "refactor: make database startup validation only"
```

## Task 7: Restore a blocking TimescaleDB migration CI gate

**Files:**
- Modify: `.github/workflows/backend-ci.yml`
- Modify: `tests/test_backend_tooling_contracts.py`

- [ ] **Step 1: Write the new workflow contract first**

Replace the quarantine test with:

```python
def test_backend_ci_blocks_on_timescaledb_migration_verification():
    content = read_text(".github/workflows/backend-ci.yml")
    migration_step = workflow_step(content, "Verify deterministic migrations")
    assert "continue-on-error" not in migration_step
    assert "test_migration_baseline_contract.py" in migration_step
    assert "verify_postgres_migrations.py" in migration_step
    assert "MIGRATION_ADMIN_URL" in content
    assert "timescale/timescaledb:2.17.2-pg14" in content
    assert "Migration diagnostic pending phase 2" not in content
```

- [ ] **Step 2: Run and confirm failure against the quarantined workflow**

```bash
python -m pytest -q tests/test_backend_tooling_contracts.py
```

Expected: FAIL because the old diagnostic name and `continue-on-error` remain.

- [ ] **Step 3: Add the TimescaleDB service**

Under job `verify`, add:

```yaml
    services:
      postgres:
        image: timescale/timescaledb:2.17.2-pg14
        env:
          POSTGRES_USER: migration_ci
          POSTGRES_PASSWORD: migration_ci_password
          POSTGRES_DB: postgres
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U migration_ci -d postgres"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 12
```

Add job environment values:

```yaml
    env:
      DATABASE_URL: postgresql://migration_ci:migration_ci_password@localhost:5432/postgres
      MIGRATION_ADMIN_URL: postgresql://migration_ci:migration_ci_password@localhost:5432/postgres
```

- [ ] **Step 4: Replace the migration diagnostic**

```yaml
      - name: Verify deterministic migrations
        run: |
          python -m pytest -q tests/test_migration_baseline_contract.py tests/test_postgres_migration_verifier.py
          python scripts/python/verify_postgres_migrations.py --admin-url "$MIGRATION_ADMIN_URL"
```

Do not use `continue-on-error` and do not upload a failure artifact as a substitute for blocking.

- [ ] **Step 5: Run workflow contract and compose validation**

```bash
python -m pytest -q tests/test_backend_tooling_contracts.py
docker compose -f docker-compose.prod.yml --env-file env.prod.example config > /tmp/phase2a-compose.yml
test -s /tmp/phase2a-compose.yml
```

Expected: tests PASS; Compose configuration remains valid.

- [ ] **Step 6: Run the complete migration gate locally**

```bash
python -m pytest -q tests/test_migration_baseline_contract.py tests/test_postgres_migration_verifier.py
MIGRATION_ADMIN_URL=postgresql://admin:password123@localhost:5432/postgres \
python scripts/python/verify_postgres_migrations.py
```

Expected: all commands PASS.

- [ ] **Step 7: Commit**

```bash
git add .github/workflows/backend-ci.yml tests/test_backend_tooling_contracts.py
git commit -m "ci: block on deterministic migration verification"
```

## Task 8: Rebuild the disposable development database and record acceptance

**Files:**
- Create: `docs/plans/backend-reliability-phase2a-acceptance.md`
- Modify: `docs/plans/PLAN-20260716-backend-reliability-phase2a.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Run the final pre-reset gate**

```bash
python -m pytest -q tests/test_migration_baseline_contract.py tests/test_postgres_migration_verifier.py tests/test_postgres_migration_paths.py tests/test_database_core.py tests/test_startup_checks.py tests/test_backend_tooling_contracts.py
MIGRATION_ADMIN_URL=postgresql://admin:password123@localhost:5432/postgres \
python scripts/python/verify_postgres_migrations.py --json-output /tmp/phase2a-final.json
```

Expected: all focused tests PASS; three-path verification succeeds. If any command fails, stop and do not execute Step 2.

- [ ] **Step 2: Print and execute the approved reset**

The implementation report must state: `即将重建已获用户批准清除的数据库 campus_energy；Redis/MQTT volumes 不变。`

Then run:

```bash
docker exec campusenergysystem-db-1 dropdb -U admin --if-exists --force campus_energy
docker exec campusenergysystem-db-1 createdb -U admin campus_energy
```

- [ ] **Step 3: Apply the new baseline**

```bash
DATABASE_URL=postgresql://admin:password123@localhost:5432/campus_energy \
python -m alembic upgrade head
```

Expected: exit `0` at revision `20260716_0001`.

- [ ] **Step 4: Verify version, table count and hypertable**

```bash
docker exec campusenergysystem-db-1 psql -U admin -d campus_energy -Atc "SELECT version_num FROM alembic_version"
docker exec campusenergysystem-db-1 psql -U admin -d campus_energy -Atc "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"
docker exec campusenergysystem-db-1 psql -U admin -d campus_energy -Atc "SELECT hypertable_name FROM timescaledb_information.hypertables WHERE hypertable_schema='public'"
```

Expected: revision `20260716_0001`; 26 public tables including `alembic_version`; hypertable `energydata`.

- [ ] **Step 5: Run validation-only startup**

```bash
DATABASE_URL=postgresql://admin:password123@localhost:5432/campus_energy \
DB_AUTO_CREATE_TABLES=False DB_RUNTIME_SCHEMA_SYNC=False \
python -c "from app.core.database import init_db; init_db()"
```

Expected: exit `0` and no schema changes.

- [ ] **Step 6: Run full backend regression and quality checks**

```bash
export DATABASE_URL=postgresql://admin:password123@localhost:5432/campus_energy
export DB_AUTO_CREATE_TABLES=False
export DB_RUNTIME_SCHEMA_SYNC=False
python -m pytest -q
bash ./scripts/shell/run_backend_coverage.sh
python scripts/python/check_ruff_regressions.py
python -m compileall -q app tests scripts/python migrations
git diff --check
```

Expected: no backend regression; coverage remains above the existing 57% gate; Ruff debt does not grow; compile and diff checks pass.

- [ ] **Step 7: Write the acceptance record**

Record exact command results, test counts, three fingerprints or their common hash, rebuilt revision/table count, startup result, warnings, MQTT out-of-scope status, and the decision that phase 2A passes or is blocked. Do not mark pass if CI configuration or any local gate is unverified.

- [ ] **Step 8: Commit acceptance evidence**

```bash
git add docs/plans/backend-reliability-phase2a-acceptance.md docs/plans/PLAN-20260716-backend-reliability-phase2a.md docs/plans/current-status.md docs/plans/handoff.md
git commit -m "docs: accept deterministic migration baseline"
```

## Task 9: Return the main topic to storage and release Task 3

**Files:**
- Modify: `docs/superpowers/plans/2026-07-16-campus-pv-storage-simulation.md`
- Modify: `docs/plans/PLAN-20260716-campus-pv-storage-simulation.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`
- Modify: `docs/plans/daily/2026-07/2026-07-16-status.md`
- Modify: `docs/plans/daily/2026-07/2026-07-16-handoff.md`
- Test: `tests/test_backend_reliability_phase2a_docs.py`

- [ ] **Step 1: Write the resume-state assertions**

Add tests asserting:

```python
def test_storage_resumes_only_after_phase2a_acceptance():
    status = read("docs/plans/current-status.md")
    storage_plan = read("docs/superpowers/plans/2026-07-16-campus-pv-storage-simulation.md")
    assert "当前主主题：`园区光储协同仿真与 EMS 控制`" in status
    assert "Task 3" in status and "具备准入条件" in status
    assert 'revision = "20260716_0002"' in storage_plan
    assert 'down_revision = "20260716_0001"' in storage_plan
```

- [ ] **Step 2: Run and verify failure before handback**

```bash
python -m pytest -q tests/test_backend_reliability_phase2a_docs.py
```

Expected: new resume assertions FAIL while phase 2A remains the active topic and the storage plan still uses the old revision placeholder.

- [ ] **Step 3: Update the storage migration contract**

Replace every storage-plan occurrence of:

```text
revision 20260716_0012 -> 20260716_0002
down_revision 20260515_0011 -> 20260716_0001
```

State that the new baseline already owns the base `storage_telemetry` table; storage Task 3 only adds profile, dispatch and the approved telemetry extensions.

- [ ] **Step 4: Append phase 2A completion snapshots**

Append separate completion sections to the existing daily files. Record acceptance commit, new revision, fingerprint result, rebuilt database, and the exact Task 3 handoff. Do not overwrite earlier snapshots.

- [ ] **Step 5: Replace main status and handoff with storage**

Make storage the only active main topic. Preserve Task 1/2 completion, mark Task 3 ready rather than complete, and hand off to the backend storage role.

- [ ] **Step 6: Run governance and migration contracts**

```bash
python -m pytest -q tests/test_backend_reliability_phase2a_docs.py tests/test_migration_baseline_contract.py tests/test_postgres_migration_verifier.py
git diff --check
```

Expected: tests PASS; no old storage revision/down-revision remains.

- [ ] **Step 7: Commit phase handback**

```bash
git add docs/superpowers/plans/2026-07-16-campus-pv-storage-simulation.md docs/plans/PLAN-20260716-campus-pv-storage-simulation.md docs/plans/current-status.md docs/plans/handoff.md docs/plans/daily/2026-07/2026-07-16-status.md docs/plans/daily/2026-07/2026-07-16-handoff.md tests/test_backend_reliability_phase2a_docs.py
git commit -m "docs: resume campus storage persistence"
```

## Final acceptance boundary

Phase 2A is complete only when all statements are true:

1. `migrations/versions/` has one static root revision `20260716_0001` before storage Task 3.
2. No active migration imports application models/metadata or performs online inspection during offline generation.
3. Fresh online, offline SQL, and upgrade-downgrade-upgrade paths produce identical normalized fingerprints.
4. `energydata` is a TimescaleDB hypertable created by migration.
5. Application startup rejects mutation flags and performs read-only schema assertions.
6. CI migration verification uses TimescaleDB and has no `continue-on-error`.
7. The approved disposable `campus_energy` database is rebuilt at `20260716_0001`.
8. Full backend regression, coverage, Ruff baseline and compile checks pass.
9. Storage Task 3 is handed back with revision `20260716_0002` and down-revision `20260716_0001`.

Do not start storage Task 3 before all nine statements have evidence.
