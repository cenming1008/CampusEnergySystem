# Backend Architecture Audit Design

## Goal

Create a backend architecture audit and phased cleanup plan for the Campus Energy Management System without starting a broad code refactor in the audit round.

This design turns the current backend layering rules into an executable governance path. It should help later backend work decide where code belongs, which files are cleanup candidates, which changes are allowed in each phase, and how to verify that API behavior remains compatible.

## Context

The project is now positioned as a campus EMS. Backend work should serve multi-energy ingestion, hierarchical metering, itemized analysis, alarm linkage, realtime monitoring, and dashboard aggregation.

The current main topic is `设备监控统一模板 V4 后续结构收敛`. Recent backend work has already introduced several useful layering patterns:

- `app/application/` contains use case orchestration for device management, monitoring, reporting, campus aggregation, locations, users, maintenance, inspection, analysis, energy management, authentication, and telemetry ingestion.
- `app/api/endpoints/devices/` has been split into domain router files such as `management.py`, `data.py`, `monitoring.py`, `ingestion_health.py`, `compensation_capacitor_bank.py`, `compensation_svg.py`, and `storage.py`.
- Device monitoring has a plugin registry and monitor context, which reduces central branching inside `DeviceMonitorService`.
- Alarm rules have started moving into `app/domain/alarm_rule_profiles.py`, keeping profile resolution away from frontend code and endpoint files.

The current audit should preserve those improvements and avoid reopening completed architecture topics unless a later implementation plan explicitly scopes them.

## Non-Goals

- Do not rename the repository, database, runtime identifiers, MQTT topics, environment variables, or compatibility labels.
- Do not perform a full service-layer rewrite.
- Do not change public API paths, request parameters, response models, or status-code contracts.
- Do not merge backend architecture cleanup with frontend work.
- Do not expand coal-mine-specific modeling or terminology.
- Do not move code only for visual symmetry. Every later code movement must reduce a concrete responsibility leak, file-growth risk, or testability problem.

## Target Layering Model

### API Endpoints

`app/api/endpoints/` should remain the HTTP boundary.

Allowed responsibilities:

- Parse path, query, and body parameters.
- Use `Depends` for session and current-user injection.
- Apply route metadata, response models, and HTTP status codes.
- Translate a small number of expected exceptions into HTTP errors.
- Call a use case or stable service method.

Disallowed responsibilities:

- Multi-service workflow orchestration.
- Audit/event side effects spread across router functions.
- Device type dispatch tables that belong in a registry, profile, or use case.
- Large serializer blocks duplicated across endpoints.
- Business rule evaluation, threshold decisions, or alarm lifecycle decisions.

### Application Use Cases

`app/application/` should own user-intent and system-workflow orchestration.

Allowed responsibilities:

- Access prechecks and user-visible scope filtering.
- Multi-service calls for one business action.
- Default value decisions that belong to a workflow.
- Audit side-effect placement for the workflow.
- Stable response DTO assembly when the DTO represents an interface workflow rather than a pure domain object.
- Internal workflows such as telemetry ingestion and replay preparation.

Disallowed responsibilities:

- HTTP `Depends`, response status codes, and router-specific exception formatting.
- ORM query details or SQL-level data access.
- Pure mathematical or rules logic that can live in `domain`.
- Empty pass-through wrappers that only forward one call without adding workflow value.

### Services

`app/services/` should provide stable business capabilities and persistence-oriented operations.

Allowed responsibilities:

- Resource CRUD and state transition operations.
- Query composition and aggregation that is not tied to HTTP.
- Coordination with repositories or models.
- Device-specific service packages for capabilities that are too large for a single root service.
- Compatibility wrappers that keep older callers stable while the main path moves to use cases.

Disallowed responsibilities:

- HTTP response concerns.
- Frontend display branching.
- Global "god service" growth for unrelated subdomains.
- Protocol parsing that belongs in `integrations`.
- Pure rule profile evaluation that belongs in `domain`.

### Domain

`app/domain/` should contain pure business rules and deterministic transformations.

Allowed responsibilities:

- Alarm rule profile resolution.
- Energy and analysis rule calculation.
- Device payload normalization and validation that does not require DB or HTTP.
- Stable constants, categories, and rule helpers for campus EMS business concepts.

Disallowed responsibilities:

- Database session usage.
- HTTP exception handling.
- MQTT publishing or external I/O.
- User-interface DTO assembly.

### Integrations

`app/integrations/` should contain external protocol and vendor adapter concerns.

Allowed responsibilities:

- MQTT payload transport adapters.
- Vendor protocol decoding.
- Field alias mapping at the protocol boundary.
- External-client concerns that are not core business logic.

Disallowed responsibilities:

- Campus EMS business rule decisions.
- Alarm lifecycle decisions.
- Frontend-facing response shaping.

## Current Audit Findings

The initial scan found several cleanup candidates. These are candidates, not approval to refactor all of them at once.

### Endpoint Layer

- `app/api/endpoints/energy/shared.py` conflicts with the backend guideline that discourages broad `shared.py` growth. Its current role should be audited and split into clearer `schemas.py`, `serializers.py`, or local helpers only if there is actual reuse pressure.
- `app/api/endpoints/inspection.py`, `app/api/endpoints/maintenance.py`, `app/api/endpoints/locations.py`, and `app/api/endpoints/campus.py` remain large enough to deserve responsibility review, but previous use case convergence already improved parts of this layer. Later work should audit before moving code.
- `app/api/endpoints/devices/` is already aligned with the target pattern and should be used as the reference for complex endpoint domains.

### Application Layer

- `app/application/README.md` is already a useful source of truth and should be kept in sync with any new use case modules.
- Existing use cases should not be expanded into pass-through wrappers. New use cases must show workflow value.
- Device monitoring's application entry should remain the preferred HTTP overview path; compatibility wrappers can stay in services where needed.

### Service Layer

Large service files deserve staged review rather than bulk splitting:

- `app/services/inspection_service.py`
- `app/services/device_service.py`
- `app/services/alarm_service.py`
- `app/services/campus_service.py`
- `app/services/maintenance_service.py`
- `app/services/location_service.py`
- `app/services/devices/compensation/capacitor_bank/control_command_service.py`
- `app/services/devices/compensation/monitor_service.py`

Likely cleanup directions include extracting pure rules to `domain`, workflow orchestration to `application`, protocol boundaries to `integrations`, or device-family-specific capabilities into focused service packages.

### Domain Layer

- `app/domain/alarm_rule_profiles.py` is a good example of moving profile resolution out of service and endpoint code.
- `app/domain/alarm_rules.py`, `energy_rules.py`, and `analysis_rules.py` are sizable and should be treated as domain packages if they continue to grow.

### Tests

The repository already has useful boundary tests, including application use case tests, endpoint semantic tests, device monitor tests, alarm rule tests, and device-family boundary tests. Any later cleanup must add or preserve tests that prove compatibility before and after movement.

## Recommended Approach

Use a staged audit-to-plan workflow.

### Phase 1: Architecture Audit Inventory

Create a backend audit document that maps current files to the target layering model and classifies each finding as:

- `keep`: already aligned or intentionally compatible.
- `watch`: not urgent but should not grow further.
- `split_candidate`: clear responsibility leak or file-growth risk.
- `plan_required`: too risky for direct cleanup and needs its own PLAN.

This phase should not move code.

### Phase 2: Boundary Guardrails

Add or update lightweight tests and docs that prevent regression:

- Endpoint files should not gain obvious large workflow blocks where use cases already exist.
- Device monitor and alarm contracts must remain compatible.
- `shared.py` files should not become dumping grounds for unrelated schemas, serializers, and business helpers.

This phase may modify tests and documentation, but should avoid broad production-code restructuring.

### Phase 3: Low-Risk Endpoint Cleanup

Handle narrow endpoint-layer cleanup first, starting with files that have clear non-business helper extraction opportunities. Candidate order:

1. `app/api/endpoints/energy/shared.py`
2. Small duplicate serializers or schemas in endpoint files
3. Endpoint-only helper functions that can move into local `serializers.py`

No public API contract changes are allowed.

### Phase 4: Service Responsibility Cleanup

Pick one service family per round. Each round must state one exact responsibility leak and fix only that leak.

Suggested order:

1. `alarm_service.py`: move remaining pure rule/profile decisions to `domain` only if tests can lock lifecycle behavior.
2. `device_service.py`: separate device profile/default normalization from persistence if the code currently mixes them.
3. `campus_service.py`: separate aggregation calculation helpers from data access if they are independently testable.
4. `inspection_service.py` and `maintenance_service.py`: only revisit after confirming the existing application convergence did not already solve the main issue.

### Phase 5: Package-Level Domain Splits

Only after concrete growth pressure, convert large domain files into packages. For example:

- `app/domain/alarm_rules/`
- `app/domain/energy_rules/`
- `app/domain/analysis_rules/`

This phase should keep import compatibility where practical.

## Acceptance Criteria

The audit and plan are acceptable when:

- They identify concrete backend cleanup candidates with file paths.
- They classify each candidate by risk and expected layer destination.
- They preserve the campus EMS product direction.
- They do not propose API-breaking changes.
- They avoid expanding the current device monitoring main topic beyond its boundary.
- They define verification commands for each later implementation phase.
- They make clear which changes require a formal `PLAN-*.md` before code movement.

## Verification Strategy

For the audit/spec round:

- Review the created design document for placeholders, contradictions, and scope creep.
- Check that it does not instruct immediate broad refactoring.
- Confirm it aligns with `AGENTS.md`, `docs/guides/backend-guidelines.md`, `docs/plans/current-status.md`, and `docs/plans/handoff.md`.

For later implementation rounds, use focused tests based on touched areas:

- Device monitoring: `./venv/bin/python -m pytest tests/test_device_monitor_plugin_registry.py tests/test_device_monitor_service.py -q`
- Alarm rules: `./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py tests/test_alarm_service.py tests/test_alarm_endpoints.py -q`
- Energy endpoints: `./venv/bin/python -m pytest tests/test_energy_endpoint_semantics.py tests/test_energy_service_round2.py -q`
- Application boundaries: `./venv/bin/python -m pytest tests/test_application_use_cases.py tests/test_endpoint_application_convergence.py -q`
- Full backend smoke when a phase touches shared layers: `./venv/bin/python -m pytest -q`

## Open Decisions For Implementation Planning

The next plan should decide:

1. Whether the first executable phase should be documentation-only audit inventory or audit inventory plus boundary tests.
2. Whether the architecture audit should live under `docs/plans/` as a project plan or under `docs/guides/` as a durable backend guide extension.
3. Whether the current main topic should remain `设备监控统一模板 V4 后续结构收敛`, or whether backend architecture cleanup should become a separate current main topic before code movement begins.
