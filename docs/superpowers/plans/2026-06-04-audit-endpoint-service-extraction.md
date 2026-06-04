# Audit Endpoint Service Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move audit endpoint query logic into `AuditService` while preserving API response shape.

**Architecture:** Add `app/services/audit_service.py` for query/filter/summary behavior. Keep `AuditEventResponse` and `_to_response(...)` in `app/api/endpoints/audit.py` for HTTP response serialization and compatibility.

**Tech Stack:** Python, FastAPI endpoint functions, SQLModel, pytest/unittest mocks.

---

### Task 1: Write Failing Endpoint Delegation Tests

**Files:**
- Modify: `tests/test_endpoint_application_convergence.py`

- [ ] **Step 1: Import audit endpoint module**

Change:

```python
from app.api.endpoints import analysis, auth, inspection, locations, maintenance, users
```

to:

```python
from app.api.endpoints import analysis, audit, auth, inspection, locations, maintenance, users
```

- [ ] **Step 2: Add audit events delegation test**

Add to `TestEndpointApplicationConvergence`:

```python
    @patch("app.api.endpoints.audit.AuditService.list_events")
    def test_audit_events_endpoint_delegates_to_service(self, mock_list_events):
        session = object()
        current_user = SimpleNamespace(username="admin", role="admin")
        event = SimpleNamespace(
            id=7,
            action="device.toggle",
            actor="admin",
            target="device:1",
            outcome="success",
            actor_role="admin",
            details='{"request_id":"req-1"}',
            created_at=datetime(2026, 6, 4, 10, 0, 0),
        )
        mock_list_events.return_value = [event]

        result = audit.get_audit_events(
            action="device.toggle",
            actor="admin",
            outcome="success",
            start_time=None,
            end_time=None,
            limit=50,
            offset=10,
            session=session,
            current_user=current_user,
        )

        self.assertEqual(result[0].id, 7)
        mock_list_events.assert_called_once_with(
            session,
            action="device.toggle",
            actor="admin",
            outcome="success",
            start_time=None,
            end_time=None,
            limit=50,
            offset=10,
        )
```

- [ ] **Step 3: Add audit search and summary delegation tests**

Add:

```python
    @patch("app.api.endpoints.audit.AuditService.search_events")
    def test_audit_search_endpoint_delegates_to_service(self, mock_search_events):
        session = object()
        current_user = SimpleNamespace(username="admin", role="admin")
        mock_search_events.return_value = {
            "items": [],
            "total": 0,
            "offset": 0,
            "limit": 100,
            "has_more": False,
            "filters": {"action": None},
        }

        result = audit.search_audit_events(
            action=None,
            actor=None,
            outcome=None,
            failed_only=True,
            denied_only=False,
            start_time=None,
            end_time=None,
            limit=100,
            offset=0,
            session=session,
            current_user=current_user,
        )

        self.assertEqual(result["data"]["total"], 0)
        mock_search_events.assert_called_once_with(
            session,
            action=None,
            actor=None,
            outcome=None,
            failed_only=True,
            denied_only=False,
            start_time=None,
            end_time=None,
            limit=100,
            offset=0,
            serialize_event=audit._to_response,
        )

    @patch("app.api.endpoints.audit.AuditService.get_summary")
    def test_audit_summary_endpoint_delegates_to_service(self, mock_get_summary):
        session = object()
        current_user = SimpleNamespace(username="admin", role="admin")
        mock_get_summary.return_value = {
            "window_hours": 24,
            "total": 0,
            "outcomes": {},
            "top_actions": [],
        }

        result = audit.get_audit_summary(hours=24, session=session, current_user=current_user)

        self.assertEqual(result["data"]["window_hours"], 24)
        mock_get_summary.assert_called_once_with(session, hours=24)
```

- [ ] **Step 4: Run first delegation test and verify RED**

Run:

```bash
./venv/bin/python -m pytest tests/test_endpoint_application_convergence.py::TestEndpointApplicationConvergence::test_audit_events_endpoint_delegates_to_service -q
```

Expected: FAIL because `app.api.endpoints.audit.AuditService` does not exist.

### Task 2: Add Audit Service

**Files:**
- Create: `app/services/audit_service.py`
- Modify: `app/api/endpoints/audit.py`

- [ ] **Step 1: Create service with query methods**

Create `AuditService` with:

- `_build_statement(...)`
- `list_events(...)`
- `search_events(..., serialize_event)`
- `get_summary(...)`

- [ ] **Step 2: Update endpoint imports and method bodies**

In `audit.py`, remove direct `select`, `func`, `or_` imports and import:

```python
from app.services.audit_service import AuditService
```

Use `AuditService.list_events`, `AuditService.search_events`, and `AuditService.get_summary`.

- [ ] **Step 3: Run endpoint delegation tests**

Run:

```bash
./venv/bin/python -m pytest tests/test_endpoint_application_convergence.py::TestEndpointApplicationConvergence::test_audit_events_endpoint_delegates_to_service tests/test_endpoint_application_convergence.py::TestEndpointApplicationConvergence::test_audit_search_endpoint_delegates_to_service tests/test_endpoint_application_convergence.py::TestEndpointApplicationConvergence::test_audit_summary_endpoint_delegates_to_service -q
```

Expected: PASS.

### Task 3: Verify Audit Behavior

**Files:**
- Verify only.

- [ ] **Step 1: Run audit tests**

Run:

```bash
./venv/bin/python -m pytest tests/test_audit.py tests/test_endpoint_application_convergence.py::TestEndpointApplicationConvergence::test_audit_events_endpoint_delegates_to_service tests/test_endpoint_application_convergence.py::TestEndpointApplicationConvergence::test_audit_search_endpoint_delegates_to_service tests/test_endpoint_application_convergence.py::TestEndpointApplicationConvergence::test_audit_summary_endpoint_delegates_to_service -q
```

Expected: PASS.

### Task 4: Update Handoff Docs

**Files:**
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`
- Modify: `docs/plans/daily/2026-06/2026-06-04-status.md`
- Modify: `docs/plans/daily/2026-06/2026-06-04-handoff.md`

- [ ] **Step 1: Record completion and verification**

Document that `audit.py` SQL query logic moved into `AuditService` and audit endpoint now delegates to service.
