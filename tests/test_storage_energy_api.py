import os
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints.energy import storage


def _user():
    return SimpleNamespace(username="viewer", role="viewer", location_scope=None)


def test_storage_energy_routes_extend_existing_energy_boundary():
    paths = {(route.path, next(iter(route.methods))) for route in storage.router.routes}
    response_models = {route.path: route.response_model.__name__ for route in storage.router.routes}

    assert ("/storage/overview", "GET") in paths
    assert ("/storage/comparison", "GET") in paths
    assert response_models == {
        "/storage/overview": "StorageEnergyOverviewResponse",
        "/storage/comparison": "StorageStrategyComparisonResponse",
    }


def test_overview_forwards_existing_device_scope_to_service():
    expected = {"current": {"load_kw": 420.0}}
    session = object()
    user = _user()
    with patch.object(storage, "get_allowed_device_ids", return_value={1, 2, 3}) as allowed, patch.object(
        storage.StorageEnergyService,
        "get_overview",
        return_value=expected,
    ) as overview:
        result = storage.get_storage_overview(None, session, user)

    assert result == expected
    allowed.assert_called_once_with(session, user)
    overview.assert_called_once_with(session, allowed_device_ids={1, 2, 3}, device_id=None)


def test_explicit_device_uses_existing_access_control_before_overview():
    session = object()
    user = _user()
    device = SimpleNamespace(id=3, device_category="storage")
    with patch.object(storage, "ensure_device_access", return_value=device) as ensure, patch.object(
        storage,
        "get_allowed_device_ids",
        return_value={3},
    ), patch.object(storage.StorageEnergyService, "get_overview", return_value={"current": {}}):
        storage.get_storage_overview(3, session, user)

    ensure.assert_called_once_with(session, user, 3)


def test_comparison_forwards_replay_parameters_and_scope():
    expected = {"strategies": {"baseline": {}, "rule": {}, "day_ahead": {}}}
    session = object()
    user = _user()
    with patch.object(storage, "ensure_device_access", return_value=SimpleNamespace(id=7)), patch.object(
        storage,
        "get_allowed_device_ids",
        return_value={7},
    ) as allowed, patch.object(
        storage.StorageEnergyService,
        "compare_strategies",
        return_value=expected,
    ) as compare:
        result = storage.get_storage_comparison(
            scenario_key="pv_surplus",
            seed=20260718,
            initial_soc=55.0,
            device_id=7,
            session=session,
            current_user=user,
        )

    assert result == expected
    allowed.assert_called_once_with(session, user)
    compare.assert_called_once_with(
        session,
        scenario_key="pv_surplus",
        seed=20260718,
        initial_soc=55.0,
        allowed_device_ids={7},
        device_id=7,
    )
