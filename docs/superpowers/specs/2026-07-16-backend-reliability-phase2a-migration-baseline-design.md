# Backend Reliability Phase 2A Deterministic Migration Baseline Design

## Status

- Design date: 2026-07-16
- Product context: Campus Energy Management System
- Decision: approved section by section in conversation
- Scope: Alembic migration-chain trust only
- Data decision: the current development database contains no data that must be preserved and may be rebuilt

## Goal

Replace the non-deterministic historical Alembic chain with one static, reproducible Campus EMS baseline so an empty PostgreSQL/TimescaleDB instance can reach the expected schema through either online migrations or generated offline SQL. Make migration verification a blocking CI gate and remove application-startup schema mutation.

This phase exists to unblock the storage persistence task. It does not implement storage persistence itself.

## Current Evidence

The local Docker middleware is running. PostgreSQL 14 is healthy, Redis is healthy, and MQTT is running with an unhealthy health check. MQTT and Redis do not participate in Alembic validation and remain outside this phase.

The current development database is stamped at `20260515_0011` and exposes 26 public tables including `alembic_version`. Its data is disposable by user decision, so this design does not preserve upgrade compatibility with arbitrary historical database drift.

The active migration chain has these confirmed defects:

- `20260325_0001` calls `SQLModel.metadata.create_all()`, so the same revision changes whenever current ORM models change.
- Several revisions inspect or query a live database during `--sql` generation.
- Offline generation fails reproducibly in `20260412_0003` because `op.get_bind().execute()` returns no online result and `result.fetchone()` is called.
- Later revisions mix conditional runtime inspection with schema changes.
- Some current structures, including `storage_telemetry` and several alarm fields, came from ORM creation or runtime schema sync rather than a deterministic migration.
- Application startup can still create tables, add fields and indexes, and attempt TimescaleDB hypertable conversion.
- CI explicitly quarantines the known migration failure with `continue-on-error`.

## Design Decision

Create a new root baseline and retire the old chain from Alembic's active version directory.

The new active chain starts as:

```text
base
  -> 20260716_0001_campus_baseline
  -> 20260716_0002_storage_simulation_contracts
  -> future incremental revisions
```

`20260716_0002` belongs to the already approved storage implementation and is not implemented during phase 2A. The previous storage-plan placeholder `20260716_0012` must be updated to the new revision and down-revision before storage Task 3 begins.

## Alternatives Considered

### Preserve and Rewrite Every Historical Revision

Keep revision IDs `0001-0011`, replace dynamic behavior, add reconciliation, and validate historical database shapes.

This preserves upgrade compatibility, but it adds substantial conditional logic for data and schemas the user has confirmed are disposable. It also retains a long chain whose original states no longer provide product value.

Decision: rejected for this repository state.

### Repair Offline SQL Only

Add offline-mode branches to the failing revisions and leave the dynamic baseline in place.

This would make the immediate command run further, but the root revision would still derive its result from current ORM metadata. A future model edit could silently change a historical revision.

Decision: rejected because it does not establish a trustworthy baseline.

### New Deterministic Baseline and Database Reset

Archive the old revisions, create one static root revision, validate it in isolated databases, and rebuild the disposable development database.

This gives the smallest maintainable active chain, a clear future migration boundary, and strong CI evidence without legacy compatibility complexity.

Decision: selected.

## Scope

### Included

- Archive active revisions `20260325_0001` through `20260515_0011` outside `migrations/versions/`.
- Add one static root migration `20260716_0001_campus_baseline.py`.
- Include the complete current Campus EMS schema required before storage Task 3.
- Move TimescaleDB extension/hypertable ownership out of application startup and into the baseline.
- Remove automatic table creation, runtime column/index synchronization, and startup hypertable DDL.
- Add deterministic schema-fingerprint and PostgreSQL migration-path verification.
- Replace the non-blocking CI migration diagnostic with a blocking TimescaleDB-backed gate.
- Rebuild the disposable local `campus_energy` database only after isolated validation passes.
- Update phase 2A and storage governance documents to reflect the new baseline and storage down-revision.

### Excluded

- Storage asset, telemetry-extension, or dispatch-plan persistence.
- Redis behavior.
- MQTT health or broker configuration.
- Readiness HTTP status, rate-limit semantics, or production deployment sequencing.
- Frontend changes.
- Public API, MQTT topic, or payload changes.
- Preservation of existing development rows.

## Active Migration Layout

Historical migration sources move to:

```text
docs/archive/migrations/legacy-pre-20260716/
  README.md
  20260325_0001_industrial_baseline.py
  ...
  20260515_0011_add_capacitor_bank_harmonic_spectrum.py
```

The archive README records each revision, its former responsibility, known non-deterministic behavior, and the fact that `20260716_0001` supersedes it for rebuildable development environments. Archived Python files are evidence only and are not imported or executed by Alembic.

`migrations/versions/` contains only active revisions. At the end of phase 2A it contains the new baseline; storage Task 3 later adds `20260716_0002`.

## Baseline Schema Contract

The baseline is a hand-reviewed static schema snapshot. Generation from current ORM metadata may be used once as an authoring aid, but the checked-in migration must contain explicit Alembic/SQLAlchemy operations and must not import application models, `SQLModel.metadata`, settings, database engines, or runtime registries.

The baseline creates all 25 current business tables represented by the Campus EMS models before storage Task 3:

- campus/location/device and device-group structures;
- users and audit events;
- energy data, statistics, carbon and maintenance structures;
- alarms and ingestion-health records;
- MQTT ingestion and control logs;
- inspection structures;
- SVG and capacitor-bank profiles/telemetry;
- the existing base `storage_telemetry` table.

The static schema includes all current columns that were previously supplied by runtime sync, including alarm lifecycle fields, MQTT retry/replay fields, device subtype/archive state, compensation monitoring fields, harmonic JSON columns, and required indexes.

Every table definition must explicitly state:

- column type and nullability;
- primary key;
- foreign keys;
- unique constraints;
- server defaults where application startup depends on them;
- named indexes used by queries or startup assertions.

Schema ownership excludes `alembic_version`, which Alembic manages.

## TimescaleDB Ownership

The baseline explicitly executes:

1. `CREATE EXTENSION IF NOT EXISTS timescaledb`;
2. creation of `energydata` with a primary key containing the time partition column;
3. `create_hypertable('energydata', 'timestamp', if_not_exists => TRUE)` while the table is empty.

Application startup no longer calls `create_hypertable`. The baseline downgrade drops owned business tables in reverse dependency order but does not drop the TimescaleDB extension because an extension may be shared by other schemas or administrative processes.

CI and local integration verification use a TimescaleDB PostgreSQL 14 image, matching the development environment.

## Application Startup Contract

`init_db()` becomes validation-only:

```text
startup
  -> assert required tables exist
  -> assert required columns/indexes exist
  -> continue or fail with an actionable migration message
```

It must not:

- call `SQLModel.metadata.create_all()`;
- add or alter columns;
- create runtime indexes;
- execute `create_hypertable()`;
- silently swallow missing-schema errors.

The compatibility settings `DB_AUTO_CREATE_TABLES` and `DB_RUNTIME_SCHEMA_SYNC` remain parseable for one transition period, but all environment examples default them to false. If either is true, startup fails with a clear instruction to run Alembic rather than mutating schema. This retains configuration compatibility without retaining the unsafe behavior.

The old `_sync_runtime_schema`, `_ensure_runtime_indexes`, and `_try_enable_timescaledb_hypertable` implementation paths are removed after tests lock the validation-only behavior.

## Verification Architecture

### Static Contract Tests

`tests/test_migration_baseline_contract.py` verifies:

- exactly one active root revision exists after archival;
- the revision ID is `20260716_0001` with `down_revision = None`;
- no active migration imports application models or SQLModel metadata;
- no active migration calls inspectors, `op.get_bind()`, or online result methods;
- required tables, critical fields, indexes, and Timescale operations appear in the static baseline;
- old revisions remain present in the archive and absent from the active version directory.

### PostgreSQL Verification Tool

`scripts/python/verify_postgres_migrations.py` owns isolated database lifecycle. It accepts an administrative PostgreSQL URL and only creates or drops databases whose names begin with the fixed `ces_migration_` prefix. It never targets `campus_energy`.

The tool creates:

- `ces_migration_fresh`: apply online `alembic upgrade head`;
- `ces_migration_offline`: generate offline SQL, then execute it against an empty database;
- `ces_migration_roundtrip`: upgrade to head, downgrade to base, then upgrade to head again.

If a path fails, the tool preserves the failing database by default and prints its name and failed step. A separate explicit cleanup option removes only prefixed temporary databases.

### Schema Fingerprint

The verifier reads PostgreSQL catalogs and produces a normalized fingerprint containing:

- public table names excluding `alembic_version`;
- columns, normalized types, nullability and defaults;
- primary keys and unique constraints;
- foreign keys and delete behavior;
- application-owned indexes;
- TimescaleDB hypertable identity for `energydata`.

Internal TimescaleDB schemas and generated extension objects are excluded. The three final fingerprints must be identical. The verifier also checks that the baseline contains the tables and fields required by startup assertions.

### Unit Tests for the Verifier

`tests/test_postgres_migration_verifier.py` covers database-name safety, command construction, fingerprint normalization, failed-database preservation, and explicit cleanup without requiring Docker. PostgreSQL integration execution remains in the verification script and CI step.

## CI Contract

The backend workflow adds a TimescaleDB PostgreSQL 14 service with a dedicated CI database account. The existing migration diagnostic is replaced by a blocking step that runs:

```text
static baseline contract tests
-> offline SQL generation
-> three-path PostgreSQL verifier
-> schema fingerprint equality
```

The migration step has no `continue-on-error`. Failure stops the workflow. Existing pytest, coverage, Ruff, image, Compose and security gates remain unchanged.

CI credentials are test-only workflow values and are not reused outside the service container.

## Local Database Reset

The current `campus_energy` database is never used for destructive experimentation.

The execution order is:

1. confirm the Docker database is healthy;
2. run static tests;
3. run all three temporary-database paths;
4. compare fingerprints;
5. show a final reset notice identifying `campus_energy`;
6. drop and recreate `campus_energy` using the known development account;
7. run `alembic upgrade head` against the recreated database;
8. run startup schema assertions and focused backend tests;
9. verify `alembic current` is `20260716_0001`.

The user has approved clearing this database. The reset is still gated behind successful isolated validation so an implementation error cannot leave the development environment without a working database.

Redis volumes, MQTT data and other Docker services are not reset.

## Error Handling

- Offline SQL failure stops before any database reset.
- Temporary database creation refuses names outside the approved prefix.
- A failed test database is retained for diagnosis and named in output.
- Cleanup failures are reported but do not trigger broad or wildcard database deletion.
- A schema fingerprint mismatch reports the first differing table/object and preserves all three databases.
- Local reset failure stops before backend startup and prints the exact migration command to retry.
- Startup schema mismatch raises an actionable error rather than attempting repair.

## Documentation and Governance

Phase 2A temporarily becomes the active main topic while this work runs. The storage topic state is preserved in daily/plan documentation with Task 1 and Task 2 complete and Task 3 blocked.

Phase 2A completion evidence must include:

- static migration contract results;
- online, offline and roundtrip temporary-database results;
- matching schema fingerprints;
- development database rebuild result;
- startup validation result;
- full backend regression count;
- blocking CI migration configuration.

After phase 2A passes, the main topic returns to storage and Task 3 changes from blocked to ready. The storage implementation plan is updated from revision `20260716_0012`/down-revision `20260515_0011` to revision `20260716_0002`/down-revision `20260716_0001`.

## Risks and Mitigations

### Static Baseline Omits a Runtime-Created Object

Mitigation: compare the intended ORM/startup-required schema with all three migrated fingerprints before resetting the development database.

### Archive Accidentally Remains Active

Mitigation: active-directory contract test requires exactly one root and ensures old revision IDs are absent from `migrations/versions/`.

### Lazy Runtime Repair Hides a Baseline Gap

Mitigation: remove runtime mutation before final acceptance and run startup with both compatibility flags false.

### TimescaleDB Differs from Generic PostgreSQL

Mitigation: standardize local and CI migration verification on the TimescaleDB PostgreSQL 14 image.

### Reset Targets the Wrong Database

Mitigation: temporary tooling only accepts the `ces_migration_` prefix; the one-time `campus_energy` reset is a separate explicit step with the database name printed before execution.

### Future Models Drift Without Migration

Mitigation: CI schema contract and migration verification remain blocking; future schema changes must add incremental revisions.

## Acceptance Criteria

Phase 2A is complete only when:

1. old revisions are archived and inactive;
2. the active root baseline is static and offline-safe;
3. online, offline and roundtrip paths pass in isolated TimescaleDB databases;
4. normalized fingerprints match;
5. application startup performs no schema mutation;
6. the disposable development database is rebuilt at `20260716_0001`;
7. backend regression tests pass without new failures;
8. CI migration verification is blocking;
9. storage Task 3 is updated to use `20260716_0002` after the new baseline.

## Handoff

- Next role after written design approval: plan author.
- Next artifact: `docs/superpowers/plans/2026-07-16-backend-reliability-phase2a-migration-baseline.md`.
- Implementation mode after plan approval: Subagent-Driven Development with TDD, specification review and code-quality review for every task.
