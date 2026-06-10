# Backend Reliability and Progressive Decoupling Design

## Status

- Design date: 2026-06-10
- Decision: approved in conversation
- Product context: Campus Energy Management System
- Proposed theme: `后端可靠性基线与渐进式解耦治理`
- Execution mode: staged governance with independent acceptance and rollback boundaries

## Goal

Restore a trustworthy backend engineering baseline first, then progressively remove the highest-risk coupling in migrations, MQTT ingestion, transaction ownership, application persistence, and oversized services.

The final architecture target is a thoroughly governed backend, but implementation must remain incremental. Every phase must produce independently verifiable software, preserve public API compatibility unless an explicitly approved correctness correction is recorded, and leave a clear rollback point.

## Why This Becomes a New Theme

The previous theme, `后端架构分层审计与规范整理`, successfully established an audit inventory, import guardrails, endpoint cleanup patterns, and several small domain-rule extractions. The latest full-system review exposed problems that are broader than another isolated `split_candidate`:

- The full pytest suite has four failures caused by a stale `CampusService._find_ancestor_location` call.
- The backend CI workflow is manual-only and its `unittest discover` path omits pytest-style tests, including architecture guardrails.
- The Alembic chain cannot complete the configured offline validation, while the baseline migration derives schema from current models.
- The deployment script does not explicitly apply migrations before application startup.
- MQTT ingestion has an actual `application <-> integrations.mqtt` cycle hidden by delayed imports.
- Transaction ownership is distributed across repositories, services, application code, and MQTT processing.
- Several application modules still query ORM models directly.
- Domain modules still depend on ORM models, global settings, or registries.
- Static quality configuration exists but does not provide a meaningful merge gate.

These findings affect tests, deployment, database state, telemetry ingestion, alarm behavior, and transaction consistency. According to the repository collaboration rules, they require a new heavyweight plan rather than continued uncoordinated cleanup under the audit theme.

## Design Decision

Use the final architecture intent of a comprehensive restructuring, but deliver it through five gated phases:

1. Restore a trustworthy test and CI baseline.
2. Repair migration, deployment, and runtime failure semantics.
3. Reverse the MQTT dependency and separate protocol adaptation from business workflow.
4. Establish explicit transaction ownership and a Unit of Work boundary.
5. Continue responsibility cleanup one bounded business slice at a time.

This path is preferred over a one-shot rewrite because the current test, CI, and migration baselines cannot yet reliably distinguish existing defects from new regressions.

## Alternatives Considered

### Alternative A: Only Repair Immediate Failures

Repair the four tests, migration error, readiness status, and CI trigger, then stop.

Advantages:

- Lowest short-term implementation cost.
- Minimal production-code movement.
- Fastest route back to a green test suite.

Disadvantages:

- Leaves the MQTT cycle and fragmented transaction ownership intact.
- Future device protocol and telemetry work continues to cross multiple layers.
- Large services and direct ORM access remain difficult to modify safely.

Decision: rejected as the final path, but its reliability repairs become phases 1 and 2.

### Alternative B: One-Shot Architecture Rewrite

Rewrite application, services, repositories, MQTT processing, transactions, and domain boundaries in one coordinated branch.

Advantages:

- Reaches the target structure faster on paper.
- Avoids carrying temporary compatibility wrappers for several phases.

Disadvantages:

- Current test and migration baselines are not trustworthy enough to validate a rewrite.
- Device ingestion, alarms, control receipts, permissions, and database state would change simultaneously.
- Failure attribution and rollback would be difficult.
- The repository already contains useful structures that should be retained rather than replaced.

Decision: rejected as an execution strategy. Its target architecture remains the long-term destination.

### Alternative C: Progressive Reliability and Decoupling

Repair the safety net first, then eliminate coupling in dependency order.

Advantages:

- Each phase can be verified, released, and reverted independently.
- Existing API and device behavior can be protected with characterization tests.
- The highest-risk infrastructure issues are fixed before moving business code.
- Existing good patterns remain usable throughout the transition.

Disadvantages:

- Temporary compatibility wrappers remain for a limited period.
- The complete cleanup takes multiple implementation rounds.
- Architecture inventory and allowlists must be maintained during transition.

Decision: selected.

## Non-Goals

- Do not rename repository paths, database identifiers, MQTT topics, environment variable keys, containers, or historical compatibility labels.
- Do not change frontend behavior or frontend code.
- Do not redesign public API paths, request schemas, or response schemas as part of architecture cleanup.
- Do not rewrite all repositories or services in one phase.
- Do not introduce a generic event bus, CQRS framework, dependency injection framework, or separate microservices.
- Do not dual-write telemetry or alarm data through old and new paths.
- Do not expand coal-mine-specific product concepts.
- Do not delete compatibility wrappers until all known callers have migrated and acceptance tests protect the replacement.

## Guiding Principles

### Reliability Before Movement

No broad code movement starts while the canonical full test command fails or the migration verification path is broken.

### One Transaction Owner

One business use case owns one transaction. Lower layers may mutate and flush through the supplied session, but they do not decide when the business action is committed.

### Outer Layers Depend Inward

HTTP, MQTT consumers, schedulers, and external adapters may call application use cases. Application code must not import concrete HTTP or MQTT processors.

### Compatibility Through Adapters

When an old import or service entry point has active callers, retain a narrow adapter that delegates to the new owner. Do not maintain two independent implementations.

### Guardrails Shrink Debt

Where immediate global cleanup is impractical, use a checked-in baseline or explicit allowlist. New violations fail CI, and each implementation phase must shrink the baseline.

### Single-Slice Delivery

After the infrastructure phases, each cleanup round addresses one responsibility leak, one transaction boundary, or one dependency violation. File size alone is not sufficient justification.

## Target Architecture

```text
HTTP Endpoint       MQTT Consumer       Scheduler / Replay Entry
      \                   |                     /
       \                  |                    /
        +---------- Application Use Case ------+
                           |
                  Domain and Service APIs
                           |
                 Repository Ports / UoW
                           |
                SQLModel / Database Adapter

MQTT Decoder / Vendor Adapter --------> Application Command DTO
External Publisher Adapter <----------- Application Port
```

The important rule is not the physical directory alone. The rule is the dependency direction:

```text
api or integration entrypoint -> application -> service/domain/ports
infrastructure implementation -> application port
application -X-> concrete api or mqtt processor
domain -X-> database, settings, mqtt, redis, or HTTP
```

## Layer Responsibilities

### API

Allowed:

- Parse HTTP path, query, and body values.
- Resolve authentication and request-scoped dependencies.
- Declare response models and status codes.
- Translate a small set of expected boundary errors.
- Call one application use case or stable service entry point.

Forbidden:

- Direct transaction ownership.
- Multi-service workflow orchestration.
- Catching every `Exception` and forcing a generic 500.
- Direct protocol decoding or business alarm decisions.

### Application

Allowed:

- Represent a user or system intent as a use case.
- Apply authorization scope and workflow preconditions.
- Coordinate services, repositories, audit effects, and external ports.
- Own commit and rollback through a Unit of Work.
- Return stable application result objects.

Forbidden:

- Import concrete FastAPI endpoints or MQTT processors.
- Encode SQL queries directly in newly governed code.
- Contain pure calculations that belong in domain rules.
- Exist only as an empty forwarding wrapper.

### Services

Allowed:

- Expose stable business capabilities.
- Perform state transitions using repositories or a supplied session.
- Coordinate domain rules for one cohesive capability.

Forbidden:

- Import API or application layers.
- Decide HTTP status codes.
- Commit a transaction when called within a governed use case.
- Grow into unrelated resource, statistics, permission, and protocol responsibilities.

### Repositories

Allowed:

- Execute resource-specific queries.
- Add, update, delete, refresh, and flush entities.
- Return domain-usable records or persistence models during transition.

Forbidden:

- Default to `commit=True` in new APIs.
- Send audit notifications or MQTT messages.
- Own business workflow decisions.

### Domain

Allowed:

- Deterministic calculations, normalization, validation, and decisions.
- Plain value objects, enums, and immutable rule inputs.
- Functions that are testable without application startup.

Forbidden:

- Database sessions and SQL queries.
- ORM mutation as a required execution mechanism.
- Global settings reads inside rule evaluation.
- MQTT, Redis, HTTP, filesystem, or notification I/O.

### Integrations

Allowed:

- Decode topics and payloads.
- Map vendor fields to application command DTOs.
- Implement outbound ports such as MQTT publication.
- Host entrypoints that call application use cases.

Forbidden:

- Commit database transactions.
- Decide alarm lifecycle, authorization, or campus EMS business rules.
- Become an import dependency of an application use case.

## Core Contracts

The design uses small Python protocols instead of a new framework.

```python
from types import TracebackType
from typing import Optional, Protocol, Type


class UnitOfWork(Protocol):
    devices: "DeviceRepository"
    alarms: "AlarmRepository"

    def __enter__(self) -> "UnitOfWork": ...
    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
```

Application command DTOs are protocol-independent:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass(frozen=True)
class TelemetryCommand:
    device_identity: str
    observed_at: datetime
    measurements: dict[str, Any]
    source: str
    message_id: Optional[str] = None
```

The application use case owns the business transaction:

```python
def ingest_telemetry(command: TelemetryCommand, uow: UnitOfWork):
    try:
        device = uow.devices.get_by_identity(command.device_identity)
        result = telemetry_service.process(device, command)
        alarm_service.apply_candidates(result.alarm_candidates, uow)
        uow.commit()
        return result
    except Exception:
        uow.rollback()
        raise
```

The MQTT entrypoint performs adaptation and delegates:

```python
def handle_mqtt_message(topic: str, raw_payload: bytes):
    command = mqtt_decoder.decode(topic, raw_payload)
    with uow_factory() as uow:
        return ingest_telemetry(command, uow)
```

Concrete names may be adjusted to existing repository conventions in the implementation plan, but ownership and dependency direction are fixed by this design.

## Phase 1: Trustworthy Test and CI Baseline

### Objectives

- Restore a green canonical backend test command.
- Ensure CI runs the same test population used locally.
- Make architecture tests part of the normal merge gate.
- Prevent new lint debt without requiring an unrelated full cleanup.

### Required Changes

- Replace stale `CampusService._find_ancestor_location` calls in `AnalysisService` with the current domain helper or supported service interface.
- Add a regression test that fails if analysis aggregation uses the removed compatibility method.
- Make `python -m pytest -q` the canonical backend test command.
- Replace the CI `unittest discover` execution path with pytest.
- Add `push` and `pull_request` triggers while retaining manual dispatch.
- Keep `requirements.txt` as the runtime declaration, add `requirements-dev.txt` for pytest and quality tools, and install both through an exact CI constraints file.
- Run architecture guardrails through the canonical pytest command.
- Record the current Ruff findings as a normalized baseline and fail CI only when new findings appear.
- Run a non-blocking full Ruff report so historical debt remains visible.
- Keep the existing narrow mypy scope initially, but report its scope explicitly in CI output.

### Ruff Baseline Rules

The baseline must be machine-generated from Ruff JSON output and checked into a quality configuration directory. Comparison must normalize findings by:

- rule code,
- repository-relative path,
- line-independent message identity where practical.

Changed line numbers alone must not create false regressions. Removing an old violation shrinks the baseline; adding a violation fails CI.

### Exit Criteria

- Full pytest returns zero failures.
- CI and local pytest collect the same test set under the same dependency set.
- Architecture guardrails run on every pull request.
- A new Ruff violation causes CI failure.
- Existing Ruff debt does not require unrelated mass edits in this phase.

### Rollback

CI configuration and quality scripts can be reverted independently. The analysis regression fix remains because it restores supported behavior rather than introducing a new architecture.

## Phase 2: Migration, Deployment, and Runtime Reliability

### Objectives

- Make database schema evolution deterministic.
- Verify fresh and existing database upgrade paths.
- Ensure deployment cannot start new application code against an unapplied schema.
- Return operationally correct HTTP failure status codes.

### Migration Strategy

The dynamic baseline migration must be converted into a deterministic schema snapshot representing the schema at that revision. It must not import current application models or call `SQLModel.metadata.create_all`.

Because existing databases may already have the baseline revision recorded:

- Existing installations continue from their recorded Alembic revision.
- Fresh installations execute the deterministic baseline followed by every later migration.
- A representative existing-schema fixture is upgraded from its recorded revision to `head`.
- Editing the historical baseline is treated as a fresh-install correctness repair, not as a migration that reruns on existing databases.

The migration that queries database state during offline SQL generation must be rewritten so offline generation does not depend on a live query result. PostgreSQL-specific idempotent DDL may be used because PostgreSQL is the deployment target.

### Deployment Sequence

```text
production readiness checks
        ->
container/image build
        ->
database availability check
        ->
alembic upgrade head
        ->
application start
        ->
readiness verification
```

Migration failure stops deployment before the new application process becomes ready.

Application startup must not create tables or perform general schema synchronization in production. TimescaleDB extension or hypertable setup must move to a migration or an explicit administrative command.

### Runtime Semantics

- Readiness returns HTTP 503 when required dependencies are not ready.
- Liveness remains independent and returns success while the process itself is alive.
- Rate-limit rejection returns HTTP 429 and is covered by an HTTP integration test.
- Deployment success checks readiness, not only liveness.

### Exit Criteria

- A fresh PostgreSQL database upgrades from base to head.
- A representative existing database upgrades from its recorded revision to head.
- Offline SQL generation completes for the supported chain.
- A failed migration prevents application readiness.
- Readiness failure returns 503.
- Rate limiting returns 429.

### Rollback

Database migrations use forward repair. Once a production data migration has executed, rollback means deploying a compatible application and, when required, applying a compensating migration. Deployment scripts must not use code rollback as an implicit database downgrade.

## Phase 3: MQTT Dependency Reversal

### Objectives

- Remove the hidden circular import.
- Separate protocol adaptation from telemetry business workflow.
- Keep realtime ingestion, replay, idempotency, alarms, and control receipts behaviorally compatible.

### Target Components

- MQTT decoder: topic and payload parsing only.
- MQTT consumer: composition entrypoint that creates dependencies and calls application use cases.
- Telemetry ingestion use case: device lookup, idempotency decision, persistence orchestration, alarm coordination, and transaction ownership.
- Replay use case: obtains stored payloads and delegates through the same protocol-neutral command path.
- Control receipt use case: applies receipt state transitions without embedding them in the decoder.
- MQTT publisher port: application-facing interface implemented by the MQTT integration.

### Transition Strategy

- Introduce `TelemetryCommand` and characterize current normalized outputs with fixture tests.
- Extract decoder behavior before moving persistence.
- Keep the old `processor` public entry point as a narrow compatibility adapter.
- Redirect replay to the protocol-neutral decoder or command factory, not to the processor.
- Move one workflow responsibility at a time: main telemetry ingestion, replay, then control receipts.
- Remove eager package imports that initialize processor and service barrels.
- Delete the delayed import only after all callers use the new direction.

No old/new dual write is allowed. Compatibility adapters call the single new implementation.

### Dependency Guardrail

CI must reject:

- `app/application/**` importing `app.integrations.mqtt.processor`,
- MQTT decoder modules importing service or repository modules,
- MQTT integration modules calling `commit()` directly after the governed path is active.

### Exit Criteria

- The import graph has no strongly connected component containing application and MQTT integration modules.
- Realtime ingestion and replay share one application workflow.
- Existing MQTT topic and payload contracts remain unchanged.
- Existing idempotency, alarm, and control receipt behavior is protected by tests.
- MQTT protocol tests run without application startup or a database.

### Rollback

The compatibility processor can be redirected to the previous implementation while the phase is unreleased. After release, rollback uses the same public processor entry point and swaps only its delegated implementation.

## Phase 4: Transaction Ownership and Unit of Work

### Objectives

- Give every governed business action one transaction owner.
- Prevent repository and integration layers from committing independently.
- Eliminate silent partial success in selected batch workflows.

### Unit of Work Design

- The application layer owns the Unit of Work protocol.
- The SQLModel implementation owns one Session for the use case lifetime.
- Repositories receive that Session and use add/delete/flush/refresh as required.
- The use case calls commit once after all business steps succeed.
- Exceptions trigger rollback and preserve the original typed error.

### First Pilots

#### Device Group Batch Membership

- Validate group access, device access, duplicates, and all requested device identities before mutation.
- Preserve the existing API path and response shape.
- If validation fails, perform no membership writes and return the existing error representation where compatible.
- If persistence fails after mutation starts, roll back all membership changes.

#### Telemetry Ingestion

- Device state, telemetry data, ingestion health, alarm candidates, and receipt state changes participate in one explicitly owned transaction where business semantics require atomicity.
- External publication occurs after commit or through an explicit post-commit action; it must not create an untracked database commit.

### Transitional Compatibility

- Existing repository methods with `commit=True` remain temporarily callable only where not yet governed.
- New repository methods default to no commit.
- An explicit allowlist records remaining internal commit sites.
- Every migrated workflow removes its commit sites from the allowlist.

### Exit Criteria

- Device group batch failure leaves no partial membership changes.
- Telemetry ingestion has one documented commit point.
- Governed repositories do not default to commit.
- MQTT integration contains no direct commit.
- Transaction rollback tests cover validation failure, persistence failure, and alarm workflow failure.

### Rollback

Each pilot retains its existing service entry point as an adapter. If a new use case must be reverted before release, callers can be redirected without reverting unrelated transaction work.

## Phase 5: Continuous Responsibility Convergence

This phase is a sequence of small plans, not one refactor.

### Slice Order

1. Device group authorization, workflow, repository, and statistics boundaries.
2. Application modules that execute direct ORM queries.
3. Inspection and maintenance service responsibility splits.
4. Domain dependencies on ORM models, settings, and global registries.
5. Endpoint-wide exception catches that shadow typed global handlers.
6. Remaining oversized service or model modules, only when a concrete responsibility leak is demonstrated.

### Slice Requirements

Every slice must:

- Name one concrete responsibility leak.
- Add characterization or failing tests first.
- Preserve API contracts unless the plan records an approved correctness change.
- Remove or shrink one allowlist entry.
- Avoid moving unrelated helpers for visual symmetry.
- Update the architecture inventory and current handoff evidence.

### Exit Criteria

The phase is considered continuously healthy when:

- New application code does not directly query ORM models.
- New domain code has no infrastructure dependency.
- New endpoints rely on typed global exception handling.
- Service packages can be tested around cohesive business capabilities.
- Architecture baselines trend downward and never grow silently.

## Error Handling

Typed application and domain errors remain the source of HTTP and operational semantics.

Expected error flow:

```text
domain/application error
        ->
global HTTP error handler or MQTT outcome mapper
        ->
stable status code / error code / log context
```

Endpoints may translate parsing-specific errors but must not catch all exceptions and overwrite known status semantics.

Application use cases must:

- roll back transactions,
- retain typed error identity,
- avoid logging secrets or raw credential material,
- add workflow identifiers such as device identity, message ID, or request ID.

Unexpected errors are logged once at the boundary. Synchronous external notification must not block the async HTTP request path.

## Observability

The governance work adds or standardizes the following signals:

- canonical test count and result in CI,
- migration revision before and after deployment,
- migration duration and failure status,
- readiness dependency outcomes,
- telemetry ingestion success, duplicate, rejected, and rollback counts,
- transaction rollback count by use case,
- MQTT decode failures separated from business rejections,
- normalized route templates for HTTP metrics.

Metrics must not use raw URLs containing resource IDs as labels.

## Testing Strategy

### Unit Tests

- Domain calculations and command normalization.
- MQTT topic and payload decoding.
- Repository query behavior with a supplied session.
- Application use cases with fake repositories or a test Unit of Work where appropriate.

### Integration Tests

- FastAPI status semantics for readiness, rate limiting, and typed errors.
- PostgreSQL migration from fresh and representative existing states.
- SQLModel transaction rollback using a real test database.
- MQTT application entrypoint with fake broker transport and real workflow dependencies.

### Architecture Tests

- Layer import direction.
- No application import of concrete MQTT processor.
- No new repository default commit.
- No governed integration commit.
- No new domain infrastructure dependency.
- Quality baseline does not grow.

### Contract Tests

- Existing HTTP paths, request models, response models, and documented status codes.
- MQTT topics and accepted payload aliases.
- Telemetry normalization and replay equivalence.
- Alarm creation and recovery behavior.
- Device group response shape.

## CI Pipeline Target

The target pull-request pipeline is:

```text
dependency integrity
    ->
compile/import smoke
    ->
ruff regression gate
    ->
architecture tests
    ->
full pytest
    ->
temporary PostgreSQL migration test
```

The migration job may run in parallel with non-database unit tests after dependency installation, but merging requires all jobs to pass.

## Compatibility Matrix

| Surface | Policy |
| --- | --- |
| HTTP paths and methods | unchanged |
| Request and response schemas | unchanged unless separately approved |
| MQTT topics | unchanged |
| MQTT payload aliases | retained through adapter tests |
| Database revision history | preserved; fresh baseline made deterministic |
| Existing imports | narrow compatibility exports retained temporarily |
| Batch membership behavior | corrected to atomic execution while preserving API shape |
| Runtime error status | corrected where current status contradicts endpoint semantics |

Correcting readiness from 200 to 503 and rate limiting from 500 to 429 is an intentional operational correctness change, not an API redesign.

## Rollout Strategy

Each phase follows:

1. Characterize current behavior.
2. Add the failing guardrail or regression test.
3. Implement the smallest ownership change.
4. Run focused tests.
5. Run the canonical full backend gate.
6. Update plan status and handoff.
7. Release or stop before beginning the next phase.

Phases 3 and 4 may use internal compatibility adapters, but not duplicate persistence paths. Feature flags are only justified when the same public entry point can safely select one implementation without double processing.

## Risks and Mitigations

### Migration History Repair

Risk: fresh database schema diverges from databases that already applied the dynamic baseline.

Mitigation: compare fresh-to-head and representative-existing-to-head schemas in PostgreSQL before deployment.

### Telemetry Behavioral Drift

Risk: moving workflow code changes idempotency, alarm ordering, or health-state updates.

Mitigation: characterize representative payloads, duplicate messages, missing devices, malformed payloads, alarm triggers, replay, and control receipts before movement.

### Transaction Scope Expansion

Risk: longer transactions increase lock duration.

Mitigation: perform parsing and pure validation before opening the transaction; keep external I/O outside the active database transaction.

### Compatibility Wrappers Becoming Permanent

Risk: adapters accumulate and obscure the new ownership model.

Mitigation: every adapter has a caller inventory, removal criterion, and architecture allowlist entry that must shrink.

### Quality Baseline Normalization

Risk: line movement creates false Ruff regressions or hides real ones.

Mitigation: normalize stable finding identity and separately report the complete Ruff output.

## Phase Gates

| Gate | Required Evidence |
| --- | --- |
| Enter phase 2 | canonical pytest green; CI test population aligned |
| Enter phase 3 | migration and runtime reliability acceptance green |
| Enter phase 4 | MQTT cycle removed; ingestion/replay contract tests green |
| Enter phase 5 | Unit of Work pilots green; commit ownership documented |
| Close theme | all phase acceptance evidence recorded; remaining debt moved to bounded inventory entries |

## Completion Criteria

The theme is complete when:

- Full backend tests and architecture guardrails run automatically and pass.
- Fresh and representative existing PostgreSQL databases reach Alembic head.
- Deployment applies migrations before readiness.
- Application and MQTT integration have no circular dependency.
- Governed workflows have one explicit transaction owner.
- Device group batch writes are atomic.
- New code cannot increase identified layer violations without an explicit plan change.
- Remaining large modules are recorded as bounded candidates rather than treated as an unplanned global rewrite.

## Role Handoff

### Rules Role

- Establish the new heavyweight PLAN.
- Lock compatibility exceptions and phase gates.
- Maintain allowlist and architecture terminology.

### Prediction Role

- Produce caller inventories and dependency graphs before phases 3 through 5.
- Identify the smallest executable slice and verify assumptions.

### Backend Role

- Implement one phase or bounded slice using TDD.
- Preserve contracts and record transaction ownership.

### Acceptance Role

- Verify focused tests, canonical full tests, migration evidence, import direction, and rollback readiness.
- Prevent progression when a phase gate is not satisfied.

No frontend handoff is required unless a separately approved correctness change affects a consumed HTTP status.
