from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_source(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_energy_endpoint_modules_do_not_import_shared_catch_all():
    for relative_path in [
        "app/api/endpoints/energy/data.py",
        "app/api/endpoints/energy/carbon.py",
    ]:
        source = read_source(relative_path)
        assert "from .shared import" not in source


def test_energy_explicit_layer_modules_exist():
    for relative_path in [
        "app/api/endpoints/energy/schemas.py",
        "app/api/endpoints/energy/constants.py",
        "app/api/endpoints/energy/serializers.py",
    ]:
        assert (ROOT / relative_path).exists()
