import os
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints.devices import storage
from app.api.endpoints.devices.storage_schemas import StorageDispatchGenerateRequest
from app.core.exceptions import PermissionDeniedException
from app.models.tables import UserRole


def _device():
    return SimpleNamespace(id=1, sn="STO-001", device_category="storage")


def _user(role=UserRole.ADMIN):
    return SimpleNamespace(role=role, username="tester", location_scope=None)


def test_dispatch_routes_extend_existing_storage_boundary():
    paths = {(route.path, next(iter(route.methods))) for route in storage.router.routes}

    assert ("/{device_id}/storage/dispatch/current", "GET") in paths
    assert ("/{device_id}/storage/dispatch/generate", "POST") in paths
    assert ("/{device_id}/storage/dispatch/status", "GET") in paths


def test_viewer_can_read_current_plan_but_cannot_generate():
    viewer = _user(UserRole.VIEWER)
    expected = [SimpleNamespace(slot_index=0)]
    with patch.object(storage, "ensure_device_access", return_value=_device()), patch.object(
        storage.StorageDispatchService,
        "get_current_plan",
        return_value=expected,
    ):
        assert storage.get_current_storage_dispatch(1, date(2026, 7, 18), object(), viewer) == expected

    with pytest.raises(PermissionDeniedException):
        storage.MAINTAINER_OPERATOR_OR_ADMIN(viewer)


def test_generate_dispatch_forwards_scenario_and_returns_failure_without_deleting_plan():
    body = StorageDispatchGenerateRequest(
        dispatch_date=date(2026, 7, 18),
        scenario_key="sunny_workday",
        seed=20260716,
        initial_soc=50.0,
    )
    failure = SimpleNamespace(status="failed", solver_status="Infeasible", failure_reason="Infeasible")
    with patch.object(storage, "ensure_device_access", return_value=_device()), patch.object(
        storage.StorageDispatchService,
        "generate_scenario_plan",
        return_value=failure,
    ) as generate:
        result = storage.generate_storage_dispatch(1, body, object(), _user(UserRole.OPERATOR))

    assert result is failure
    generate.assert_called_once()
    assert generate.call_args.kwargs["scenario_key"] == "sunny_workday"
    assert generate.call_args.kwargs["seed"] == 20260716


def test_solver_status_uses_device_scope_and_service():
    expected = {"status": "optimal", "solver_status": "Optimal"}
    session = object()
    user = _user(UserRole.VIEWER)
    with patch.object(storage, "ensure_device_access", return_value=_device()) as access, patch.object(
        storage.StorageDispatchService,
        "get_solver_status",
        return_value=expected,
    ) as get_status:
        result = storage.get_storage_dispatch_status(1, date(2026, 7, 18), session, user)

    assert result == expected
    access.assert_called_once_with(session, user, 1)
    get_status.assert_called_once_with(session, 1, date(2026, 7, 18))
