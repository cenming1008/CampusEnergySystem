from types import SimpleNamespace

from app.domain.location_rules import calculate_location_path_fields


def test_calculate_location_path_fields_uses_parent_path_and_level():
    parent = SimpleNamespace(level=2, full_path="/园区/北区/一号楼")

    fields = calculate_location_path_fields("三层", parent)

    assert fields == {"level": 3, "full_path": "/园区/北区/一号楼/三层"}


def test_calculate_location_path_fields_defaults_to_root_when_parent_missing():
    fields = calculate_location_path_fields("北区", None)

    assert fields == {"level": 0, "full_path": "/北区"}
