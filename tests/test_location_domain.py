from types import SimpleNamespace

from app.domain.location_rules import (
    build_location_tree,
    build_location_statistics_payload,
    build_location_tree_node,
    calculate_location_path_fields,
)


def test_calculate_location_path_fields_uses_parent_path_and_level():
    parent = SimpleNamespace(level=2, full_path="/园区/北区/一号楼")

    fields = calculate_location_path_fields("三层", parent)

    assert fields == {"level": 3, "full_path": "/园区/北区/一号楼/三层"}


def test_calculate_location_path_fields_defaults_to_root_when_parent_missing():
    fields = calculate_location_path_fields("北区", None)

    assert fields == {"level": 0, "full_path": "/北区"}


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


def test_build_location_tree_recurses_until_max_depth_with_service_callbacks():
    campus = SimpleNamespace(
        id=1,
        name="园区",
        location_type="campus",
        code="CAMPUS",
        full_path="/园区",
        level=0,
        area_sqm=5000.0,
        manager="alice",
    )
    area = SimpleNamespace(
        id=2,
        name="北区",
        location_type="area",
        code="NORTH",
        full_path="/园区/北区",
        level=1,
        area_sqm=2000.0,
        manager="bob",
    )
    building = SimpleNamespace(
        id=3,
        name="一号楼",
        location_type="building",
        code="B001",
        full_path="/园区/北区/一号楼",
        level=2,
        area_sqm=1000.0,
        manager="carol",
    )
    child_map = {1: [area], 2: [building], 3: []}
    device_counts = {1: 1, 2: 2, 3: 3}

    tree = build_location_tree(
        [campus],
        max_depth=1,
        get_device_count=lambda location: device_counts[location.id],
        get_child_locations=lambda location: child_map[location.id],
    )

    assert tree == [
        {
            "id": 1,
            "name": "园区",
            "type": "campus",
            "code": "CAMPUS",
            "full_path": "/园区",
            "level": 0,
            "device_count": 1,
            "area_sqm": 5000.0,
            "manager": "alice",
            "children": [
                {
                    "id": 2,
                    "name": "北区",
                    "type": "area",
                    "code": "NORTH",
                    "full_path": "/园区/北区",
                    "level": 1,
                    "device_count": 2,
                    "area_sqm": 2000.0,
                    "manager": "bob",
                    "children": [],
                }
            ],
        }
    ]


def test_build_location_statistics_payload_counts_devices_and_children():
    location = SimpleNamespace(
        id=3,
        name="北区",
        location_type="area",
        full_path="/园区/北区",
        level=1,
        area_sqm=3000.0,
        manager="alice",
    )
    devices = [
        SimpleNamespace(energy_type="electricity", device_category="load", is_active=True),
        SimpleNamespace(energy_type="electricity", device_category="load", is_active=False),
        SimpleNamespace(energy_type="water", device_category="water_meter", is_active=True),
        SimpleNamespace(energy_type=None, device_category=None, is_active=True),
    ]
    child_locations = [SimpleNamespace(id=10), SimpleNamespace(id=11)]

    payload = build_location_statistics_payload(location, devices, child_locations)

    assert payload == {
        "location": {
            "id": 3,
            "name": "北区",
            "type": "area",
            "full_path": "/园区/北区",
            "level": 1,
        },
        "device_count": {
            "total": 4,
            "active": 3,
            "by_energy_type": {"electricity": 2, "water": 1, None: 1},
            "by_category": {"load": 2, "water_meter": 1, None: 1},
        },
        "child_locations_count": 2,
        "area_sqm": 3000.0,
        "manager": "alice",
    }
