from pathlib import Path

from packaging.requirements import Requirement


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def parse_requirements(content: str) -> dict[str, Requirement]:
    requirements = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        requirement = Requirement(line.split(" #", 1)[0].strip())
        canonicalized_name = requirement.name.lower().replace("_", "-")
        requirements[canonicalized_name] = requirement
    return requirements


def workflow_step(content: str, name: str) -> str:
    start_marker = f"      - name: {name}"
    assert start_marker in content, f"workflow step not found: {name}"
    start = content.index(start_marker)
    next_step = content.find("\n      - ", start + len(start_marker))
    return content[start:] if next_step == -1 else content[start:next_step]


def test_parse_requirements_skips_comments_and_parses_pep_508_requirements():
    requirements = parse_requirements(
        """
        # pytest==999
        ruff~=0.6.0  # quality gate
        Example_Pkg[cli]>=1; python_version >= "3.9"
        """
    )

    assert set(requirements) == {"ruff", "example-pkg"}
    assert str(requirements["ruff"].specifier) == "~=0.6.0"
    assert requirements["example-pkg"].extras == {"cli"}
    assert requirements["example-pkg"].marker is not None


def test_workflow_step_stops_before_the_next_unnamed_step():
    content = """
      - name: Unrelated allowed failure
        continue-on-error: true
        run: false
      - name: Migration diagnostic pending phase 2
        run: alembic upgrade head --sql
      - uses: actions/upload-artifact@v4
        continue-on-error: true
    """

    migration_step = workflow_step(
        content, "Migration diagnostic pending phase 2"
    )

    assert "alembic upgrade head --sql" in migration_step
    assert "continue-on-error: true" not in migration_step
    assert "actions/upload-artifact@v4" not in migration_step


def test_backend_coverage_uses_pytest_discovery():
    content = read_text("scripts/shell/run_backend_coverage.sh")

    assert '-m coverage run -m pytest -q' in content
    assert "unittest discover" not in content


def test_test_and_quality_tools_live_in_development_requirements():
    runtime = parse_requirements(read_text("requirements.txt"))
    development = parse_requirements(read_text("requirements-dev.txt"))

    for package in ["pytest", "coverage", "ruff", "mypy"]:
        assert package in development
        assert any(
            specifier.operator == "=="
            for specifier in development[package].specifier
        )

    for package in ["coverage", "ruff", "mypy", "pytest"]:
        assert package not in runtime


def test_runtime_and_ci_constraints_exclude_unused_python_multipart():
    runtime = parse_requirements(read_text("requirements.txt"))
    constraints = parse_requirements(read_text("constraints-ci.txt"))

    assert "python-multipart" not in runtime
    assert "python-multipart" not in constraints


def test_ci_constraints_pin_secure_packaging_tools():
    constraints = parse_requirements(read_text("constraints-ci.txt"))

    assert str(constraints["setuptools"].specifier) == "==82.0.1"
    assert str(constraints["wheel"].specifier) == "==0.47.0"


def test_backend_image_uses_ci_constraints_and_bundles_packaging_tools():
    content = read_text("Dockerfile")
    builder, runtime = content.split("# ---- Runtime stage ----", 1)
    normalized_builder = " ".join(builder.split())
    normalized_runtime = " ".join(runtime.split())

    assert any(
        line.startswith("COPY ") and "constraints-ci.txt" in line
        for line in builder.splitlines()
    )
    assert "--prefix=/install" in normalized_builder
    assert "--constraint constraints-ci.txt" in normalized_builder
    assert "-r requirements.txt" in normalized_builder
    assert "setuptools==82.0.1" in normalized_builder
    assert "wheel==0.47.0" in normalized_builder
    assert "COPY --from=builder /install /usr/local" in normalized_runtime


def test_root_readme_uses_ci_constraints_for_local_backend_development():
    content = " ".join(read_text("README.md").split())

    assert (
        "pip install --constraint constraints-ci.txt "
        "-r requirements.txt -r requirements-dev.txt"
    ) in content


def test_backend_ci_runs_automatic_pytest_and_ruff_regression_gates():
    content = read_text(".github/workflows/backend-ci.yml")
    normalized_content = " ".join(content.split())

    assert "\n  push:" in content
    assert "\n  pull_request:" in content
    assert "\n  workflow_dispatch:" in content
    assert "          cache: pip" in content
    assert "          cache-dependency-path: |" in content
    for dependency_path in [
        "constraints-ci.txt",
        "requirements.txt",
        "requirements-dev.txt",
    ]:
        assert f"            {dependency_path}" in content
    assert (
        "pip install --constraint constraints-ci.txt "
        "-r requirements.txt -r requirements-dev.txt"
    ) in normalized_content
    assert "python scripts/python/check_ruff_regressions.py" in content
    assert "bash ./scripts/shell/run_backend_coverage.sh" in content


def test_backend_ci_quarantines_known_migration_failure_until_phase2():
    content = read_text(".github/workflows/backend-ci.yml")
    migration_step = workflow_step(
        content, "Migration diagnostic pending phase 2"
    )

    assert "continue-on-error: true" in migration_step
    assert "alembic upgrade head --sql" in migration_step


def test_backend_ci_uses_read_only_permissions_and_blocking_image_scan():
    content = read_text(".github/workflows/backend-ci.yml")
    image_scan_step = workflow_step(content, "Scan backend image")

    assert "\npermissions:\n  contents: read\n" in content
    assert "uses: aquasecurity/trivy-action@" in image_scan_step
    assert "exit-code: 1" in image_scan_step
    assert "severity: CRITICAL,HIGH" in image_scan_step
    assert "ignore-unfixed: true" in image_scan_step
    assert "continue-on-error" not in image_scan_step
