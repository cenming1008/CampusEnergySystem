from types import SimpleNamespace

from app.domain.location_rules import calculate_location_path_fields, build_location_tree_node


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
