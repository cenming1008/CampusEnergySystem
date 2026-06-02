# Location Tree Node Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move single-node location tree payload construction out of `LocationService` into `app/domain/location_rules.py` without changing tree query behavior.

**Architecture:** `LocationService.get_location_tree` remains responsible for loading roots, counting devices, fetching children, recursion, and max-depth handling. The domain helper only creates the stable response dictionary for one location node. This slice does not move recursive tree traversal or database access.

**Tech Stack:** Python, pytest/unittest, existing SQLModel service layer.

---

### Task 1: RED Domain Test

**Files:**
- Modify: `tests/test_location_domain.py`

- [ ] **Step 1: Write the failing test**

Update `tests/test_location_domain.py`:

```python
from app.domain.location_rules import calculate_location_path_fields, build_location_tree_node


def test_build_location_tree_node_preserves_response_shape():
    location = SimpleNamespace(
        id=7,
        name="一号楼",
        location_type="building",
        code="B001",
        full_path="/园区/一号楼",
        level=1,
        area_sqm=1200.5,
        manager="alice",
    )

    node = build_location_tree_node(location, device_count=3)

    assert node == {
        "id": 7,
        "name": "一号楼",
        "type": "building",
        "code": "B001",
        "full_path": "/园区/一号楼",
        "level": 1,
        "device_count": 3,
        "area_sqm": 1200.5,
        "manager": "alice",
        "children": [],
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./venv/bin/python -m pytest tests/test_location_domain.py::test_build_location_tree_node_preserves_response_shape -q`

Expected: FAIL with `ImportError` because `build_location_tree_node` is not exported by `app.domain.location_rules`.

- [ ] **Step 3: Commit RED test**

Run:

```bash
git add tests/test_location_domain.py
git commit -m "test: capture location tree node payload"
```

### Task 2: GREEN Domain Helper and Service Delegation

**Files:**
- Modify: `app/domain/location_rules.py`
- Modify: `app/services/location_service.py`

- [ ] **Step 1: Add pure domain helper**

Add this function to `app/domain/location_rules.py`:

```python
def build_location_tree_node(location: Any, device_count: int) -> dict[str, Any]:
    """Build the public tree payload for one location node."""
    return {
        "id": getattr(location, "id"),
        "name": getattr(location, "name"),
        "type": getattr(location, "location_type"),
        "code": getattr(location, "code"),
        "full_path": getattr(location, "full_path"),
        "level": getattr(location, "level"),
        "device_count": device_count,
        "area_sqm": getattr(location, "area_sqm"),
        "manager": getattr(location, "manager"),
        "children": [],
    }
```

- [ ] **Step 2: Delegate tree node construction**

In `app/services/location_service.py`, import:

```python
from app.domain.location_rules import calculate_location_path_fields, build_location_tree_node
```

Inside `get_location_tree.build_tree`, replace the inline `node = {...}` dictionary with:

```python
node = build_location_tree_node(location, device_count=len(devices))
```

Leave recursion, device queries, child queries, and max-depth handling unchanged.

- [ ] **Step 3: Run tests to verify GREEN**

Run: `./venv/bin/python -m pytest tests/test_location_domain.py::test_build_location_tree_node_preserves_response_shape -q`

Expected: PASS.

- [ ] **Step 4: Run location regression tests**

Run: `./venv/bin/python -m pytest tests/test_location_domain.py tests/test_location_application_use_cases.py tests/test_endpoint_application_convergence.py -q`

Expected: PASS.

- [ ] **Step 5: Commit implementation**

Run:

```bash
git add app/domain/location_rules.py app/services/location_service.py tests/test_location_domain.py
git commit -m "refactor: move location tree node payload to domain"
```

### Task 3: Documentation Sync

**Files:**
- Modify: `docs/plans/backend-architecture-audit-inventory.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Record the completed slice**

Update docs to record that the location tree node payload moved to `domain/location_rules.py`, while recursive tree traversal remains in `LocationService`.

- [ ] **Step 2: Update status and handoff**

Record test evidence and note that `LocationService` remains a `split_candidate` for tree traversal or statistics cleanup.

- [ ] **Step 3: Commit docs**

Run:

```bash
git add docs/plans/backend-architecture-audit-inventory.md docs/plans/current-status.md docs/plans/handoff.md docs/superpowers/plans/2026-06-02-location-tree-node.md
git commit -m "docs: record location tree node domain cleanup"
```

### Task 4: Final Verification

**Files:**
- Verify only.

- [ ] **Step 1: Run focused verification**

Run: `./venv/bin/python -m pytest tests/test_location_domain.py tests/test_location_application_use_cases.py tests/test_endpoint_application_convergence.py tests/test_backend_architecture_audit_docs.py -q`

Expected: PASS.

- [ ] **Step 2: Inspect references**

Run: `rg -n "build_location_tree_node|get_location_tree|location_rules" app/services/location_service.py app/domain/location_rules.py tests/test_location_domain.py`

Expected: service imports and uses the domain helper; recursion remains in `get_location_tree`.

- [ ] **Step 3: Inspect git status**

Run: `git status --short`

Expected: no tracked changes; `.understand-anything/` may remain untracked and unrelated.
