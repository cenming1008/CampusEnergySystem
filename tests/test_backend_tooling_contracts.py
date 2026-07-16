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


def test_runtime_and_ci_constraints_pin_secure_python_multipart():
    runtime = parse_requirements(read_text("requirements.txt"))
    constraints = parse_requirements(read_text("constraints-ci.txt"))

    assert str(runtime["python-multipart"].specifier) == "==0.0.32"
    assert str(constraints["python-multipart"].specifier) == "==0.0.32"


def test_backend_tooling_targets_python_310():
    pyproject = read_text("pyproject.toml")
    workflow = read_text(".github/workflows/backend-ci.yml")
    dockerfile = read_text("Dockerfile")
    install_script = read_text("scripts/shell/install_dependencies.sh")
    readme = read_text("README.md")

    assert 'target-version = "py310"' in pyproject
    assert 'python_version = "3.10"' in pyproject
    assert 'python-version: "3.10"' in workflow
    assert dockerfile.count("FROM python:3.10-slim") == 2
    assert "sys.version_info < (3, 10)" in install_script
    assert "Python 3.10+" in readme


def test_ci_constraints_pin_secure_packaging_tools():
    constraints = parse_requirements(read_text("constraints-ci.txt"))

    assert str(constraints["setuptools"].specifier) == "==82.0.1"
    assert str(constraints["wheel"].specifier) == "==0.47.0"


def test_ci_constraints_pin_secure_transitive_runtime_dependencies():
    constraints = parse_requirements(read_text("constraints-ci.txt"))

    assert str(constraints["mako"].specifier) == "==1.3.12"
    assert str(constraints["urllib3"].specifier) == "==2.7.0"


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
    uninstall_packaging_tools = (
        "python -m pip uninstall --yes setuptools wheel"
    )
    copy_builder_install = "COPY --from=builder /install /usr/local"
    assert uninstall_packaging_tools in normalized_runtime
    assert copy_builder_install in normalized_runtime
    assert normalized_runtime.index(uninstall_packaging_tools) < (
        normalized_runtime.index(copy_builder_install)
    )


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


def test_backend_ci_blocks_on_timescaledb_migration_verification():
    content = read_text(".github/workflows/backend-ci.yml")
    migration_step = workflow_step(
        content, "Verify deterministic migrations"
    )

    assert "continue-on-error" not in migration_step
    assert "test_migration_baseline_contract.py" in migration_step
    assert "test_postgres_migration_verifier.py" in migration_step
    assert "verify_postgres_migrations.py" in migration_step
    assert '"$MIGRATION_ADMIN_URL"' in migration_step
    assert "timescale/timescaledb:2.17.2-pg14" in content
    assert "POSTGRES_USER: migration_ci" in content
    assert "POSTGRES_PASSWORD: migration_ci_password" in content
    assert "POSTGRES_DB: postgres" in content
    assert "- 5432:5432" in content
    assert 'pg_isready -U migration_ci -d postgres' in content
    assert "--health-interval 5s" in content
    assert "--health-timeout 5s" in content
    assert "--health-retries 12" in content
    migration_url = (
        "postgresql://migration_ci:migration_ci_password@localhost:5432/postgres"
    )
    assert f"DATABASE_URL: {migration_url}" in content
    assert f"MIGRATION_ADMIN_URL: {migration_url}" in content
    assert "Migration diagnostic pending phase 2" not in content


def test_backend_ci_uses_read_only_permissions_and_blocking_image_scan():
    content = read_text(".github/workflows/backend-ci.yml")
    image_scan_step = workflow_step(content, "Scan backend image")

    assert "\npermissions:\n  contents: read\n" in content
    assert "uses: aquasecurity/trivy-action@" in image_scan_step
    assert "exit-code: 1" in image_scan_step
    assert "severity: CRITICAL,HIGH" in image_scan_step
    assert "ignore-unfixed: true" in image_scan_step
    assert "continue-on-error" not in image_scan_step
