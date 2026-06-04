import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def iter_python_files(relative_dir: str):
    return sorted((ROOT / relative_dir).glob("*.py"))


def imported_module_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_domain_layer_does_not_import_outer_layers():
    forbidden_prefixes = (
        "app.api",
        "app.application",
        "app.services",
        "app.integrations",
    )
    violations: list[str] = []

    for path in iter_python_files("app/domain"):
        for module in imported_module_names(path):
            if module.startswith(forbidden_prefixes):
                violations.append(f"{path.relative_to(ROOT)} imports {module}")

    assert violations == []
