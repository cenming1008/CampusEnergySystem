# Requirements Document

## Introduction

This specification defines the requirements for refactoring the backend Service layer to resolve the "fat service" problem. The current Service classes (especially AlarmService and EnergyService) mix business rule logic, data access, and orchestration into single monolithic classes. The refactoring extracts pure domain logic into `app/domain/`, keeps data access in `app/repositories/`, and reduces Service classes to thin orchestration layers. The refactoring is incremental, starting with AlarmService as the pilot, then applying the pattern to other services.

## Glossary

- **Domain_Layer**: The `app/domain/` package containing pure functions and domain objects that encode business rules without database or I/O dependencies
- **Service_Layer**: The `app/services/` package containing orchestration classes that coordinate between Domain_Layer and Repository_Layer
- **Repository_Layer**: The `app/repositories/` package containing classes responsible for all database queries and persistence operations
- **Alarm_Domain**: The domain module (`app/domain/alarm_rules.py`) containing pure alarm fault detection rules, severity inference, and alarm lifecycle state machine logic
- **Alarm_Repository**: The repository module (`app/repositories/alarm_repository.py`) containing all alarm-related database queries and persistence operations
- **Alarm_Service**: The refactored service class that orchestrates calls between Alarm_Domain and Alarm_Repository
- **Fault_Rule**: A pure function that accepts telemetry data and threshold configuration, and returns a list of fault detection results without performing any I/O
- **Instance_Key**: A stable string identifier for an alarm instance, composed of device_id, source, and category
- **Active_Alarm**: An alarm record where `recovered_at` is None, indicating the fault condition is still present
- **Orchestration**: The pattern where a Service method calls Domain_Layer for business decisions, then calls Repository_Layer for persistence, then emits events or notifications

## Requirements

### Requirement 1: Extract Alarm Fault Detection Rules to Domain Layer

**User Story:** As a developer, I want alarm fault detection rules extracted into pure functions in the Domain_Layer, so that I can unit test business logic without database dependencies.

#### Acceptance Criteria

1. WHEN telemetry data for an SVG device is provided, THE Alarm_Domain SHALL evaluate SVG fault rules and return a list of detected faults with category, severity, and message for each fault
2. WHEN telemetry data for a capacitor bank device is provided, THE Alarm_Domain SHALL evaluate capacitor bank fault rules and return a list of detected faults with category, severity, and message for each fault
3. WHEN telemetry data with voltage and current readings is provided, THE Alarm_Domain SHALL evaluate threshold-based rules against configured limits and return a list of threshold violations
4. THE Alarm_Domain fault detection functions SHALL accept telemetry data and threshold configuration as input parameters and SHALL NOT import or reference any database session, ORM model, or I/O module
5. FOR ALL valid telemetry data inputs, evaluating fault rules then formatting the results back to telemetry-equivalent form SHALL produce consistent fault detection outcomes (idempotence property)

### Requirement 2: Extract Alarm Lifecycle State Machine to Domain Layer

**User Story:** As a developer, I want alarm lifecycle transitions (create, refresh, recover) encoded as pure domain logic, so that state machine correctness can be verified independently of persistence.

#### Acceptance Criteria

1. WHEN a new fault is detected and no Active_Alarm exists for the same Instance_Key, THE Alarm_Domain SHALL produce a "create" transition containing the alarm fields to persist
2. WHEN a fault is detected and an Active_Alarm already exists for the same Instance_Key, THE Alarm_Domain SHALL produce a "refresh" transition containing the updated last_seen_at timestamp and message
3. WHEN a previously active fault is no longer detected in the current telemetry cycle, THE Alarm_Domain SHALL produce a "recover" transition containing the recovered_at timestamp
4. WHEN a resolve action is requested for an active alarm, THE Alarm_Domain SHALL produce a "resolve" transition containing resolved_at, resolved_by, and handling_note fields
5. THE Alarm_Domain lifecycle functions SHALL accept the current alarm state and the triggering event as inputs and SHALL NOT perform any database operations

### Requirement 3: Create Alarm Repository for Data Access

**User Story:** As a developer, I want all alarm-related database queries consolidated in a dedicated Alarm_Repository, so that data access is decoupled from business logic and orchestration.

#### Acceptance Criteria

1. THE Alarm_Repository SHALL provide a method to query Active_Alarm records by device_id, category, and source
2. THE Alarm_Repository SHALL provide a method to persist new alarm records
3. THE Alarm_Repository SHALL provide a method to update existing alarm records with transition fields (refresh, recover, resolve)
4. THE Alarm_Repository SHALL provide a method to list alarms with filtering by device_id, resolved status, time range, and access-control device set
5. THE Alarm_Repository SHALL provide a method to batch-query active alarms for a device filtered by source and category set
6. THE Alarm_Repository SHALL extend BaseRepository and follow the existing repository conventions established in `app/repositories/base.py`

### Requirement 4: Refactor AlarmService to Orchestration-Only

**User Story:** As a developer, I want AlarmService reduced to a thin orchestration layer, so that each method follows the pattern: call domain rules, call repository for persistence, emit events.

#### Acceptance Criteria

1. WHEN `check_svg_faults` is called, THE Alarm_Service SHALL call Alarm_Domain to evaluate faults, then call Alarm_Repository to persist transitions, then return the list of newly created alarms
2. WHEN `check_capacitor_bank_faults` is called, THE Alarm_Service SHALL call Alarm_Domain to evaluate faults, then call Alarm_Repository to persist transitions, then return the list of newly created alarms
3. WHEN `check_and_create_alarm` is called, THE Alarm_Service SHALL call Alarm_Domain to evaluate threshold rules, then call Alarm_Repository to persist transitions, then return the list of newly created alarms
4. WHEN `resolve_alarm` or `resolve_all_alarms` is called, THE Alarm_Service SHALL call Alarm_Domain to produce resolve transitions, then call Alarm_Repository to persist the transitions
5. THE Alarm_Service SHALL NOT contain any SQLModel `select`, `where`, or `exec` statements after refactoring
6. THE Alarm_Service SHALL NOT contain any inline business rule logic (threshold comparisons, fault bit evaluation, severity inference) after refactoring

### Requirement 5: Maintain Backward Compatibility with API Endpoints

**User Story:** As a developer, I want the refactoring to preserve all existing API endpoint behavior, so that no breaking changes are introduced to consumers.

#### Acceptance Criteria

1. THE Alarm_Service public method signatures (parameter names, types, and return types) SHALL remain unchanged after refactoring
2. WHEN any existing API endpoint calls AlarmService, THE endpoint SHALL receive the same response structure and data as before the refactoring
3. THE refactored Alarm_Service SHALL continue to use `@staticmethod` methods accepting a Session parameter to maintain compatibility with existing callers
4. IF an existing test calls AlarmService methods directly, THEN THE test SHALL continue to pass without modification to the test code

### Requirement 6: Establish Domain Layer Conventions for Future Extractions

**User Story:** As a developer, I want clear conventions established by the AlarmService pilot, so that subsequent service refactorings (EnergyService, FDDService) follow the same pattern consistently.

#### Acceptance Criteria

1. THE Domain_Layer modules SHALL follow the naming convention `app/domain/{concern}_rules.py` for pure rule functions
2. THE Domain_Layer functions SHALL use Python dataclasses or TypedDict for structured input and output types rather than raw dictionaries
3. THE Domain_Layer functions SHALL be stateless and deterministic: given the same inputs, the function SHALL always produce the same outputs
4. THE Repository_Layer modules SHALL follow the naming convention `app/repositories/{concern}_repository.py`
5. THE Service_Layer refactored classes SHALL follow the three-step orchestration pattern: domain call, repository call, side-effect emission

### Requirement 7: Support Incremental Migration Path

**User Story:** As a developer, I want the refactoring to support incremental migration, so that other services can be refactored one at a time without requiring a big-bang rewrite.

#### Acceptance Criteria

1. WHILE the migration is in progress, THE Service_Layer SHALL support both refactored services (using domain + repository) and legacy services (with inline logic) coexisting in the same codebase
2. THE refactored Alarm_Domain module SHALL be importable and usable independently of AlarmService, enabling other services or tests to call domain rules directly
3. WHEN a new domain rule is added to Alarm_Domain, THE rule SHALL be testable with a unit test that does not require a database session or any mocking of I/O
4. THE refactoring SHALL NOT require changes to `app/application/` use-case modules that currently call AlarmService, beyond updating import paths if necessary
