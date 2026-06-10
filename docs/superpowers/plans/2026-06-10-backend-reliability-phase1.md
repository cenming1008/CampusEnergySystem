# Backend Reliability Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore a green canonical pytest baseline and make the same complete test population plus a no-new-Ruff-debt gate run automatically in backend CI.

**Architecture:** Keep this phase limited to test reliability and engineering tooling. Repair the stale analysis dependency, make pytest the single discovery path, split runtime and development dependencies, add a normalized Ruff debt baseline, and automate those checks on push and pull requests. Keep the known Alembic failure visible but non-blocking until phase 2.

**Tech Stack:** Python 3.9/3.10, pytest, Coverage.py, Ruff, Mypy, GitHub Actions, Bash.

---

## File Map

### Create

- `requirements-dev.txt`: exact top-level development and test tools.
- `constraints-ci.txt`: fully pinned CI dependency resolution.
- `config/quality/ruff-baseline.json`: normalized historical Ruff findings.
- `scripts/python/check_ruff_regressions.py`: Ruff baseline writer and regression gate.
- `tests/test_backend_tooling_contracts.py`: executable contracts for test discovery, CI triggers, dependency split, and temporary migration quarantine.
- `tests/test_ruff_regression_gate.py`: unit tests for finding normalization and diff behavior.

### Modify

- `app/services/analysis_service.py`: use the domain-owned ancestor lookup.
- `requirements.txt`: retain runtime dependencies only.
- `scripts/shell/run_backend_coverage.sh`: execute pytest under coverage.
- `.github/workflows/backend-ci.yml`: automatic triggers, exact dependency install, Ruff regression gate, pytest coverage, and explicit migration diagnostic.
- `tests/README.md`: document pytest as the canonical discovery path.
- `README.md`: document the canonical backend verification command.
- `scripts/SCRIPT_LIST.md`: describe the Ruff regression checker.
- `scripts/python/README.md`: document the new quality script.
- `docs/plans/PLAN-20260610-backend-reliability-progressive-decoupling.md`: record phase 1 completion evidence.
- `docs/plans/current-status.md`: record current phase result.
- `docs/plans/handoff.md`: hand off phase 1 acceptance or phase 2 planning.
- `docs/plans/daily/2026-06/2026-06-10-status.md`: daily status snapshot.
- `docs/plans/daily/2026-06/2026-06-10-handoff.md`: daily handoff snapshot.

## Task 1: Repair the Analysis Regression

**Files:**
- Modify: `app/services/analysis_service.py:15-27`
- Test: `tests/test_analysis_service.py`

- [ ] **Step 1: Run the focused existing test and verify RED**

Run:

```bash
./venv/bin/python -m pytest tests/test_analysis_service.py::TestAnalysisService::test_get_energy_analysis_overview_returns_first_batch_operational_aggregates -q
```

Expected: FAIL with:

```text
AttributeError: type object 'CampusService' has no attribute '_find_ancestor_location'
```

- [ ] **Step 2: Import the domain-owned lookup**

Change the campus rules import to:

```python
from app.domain.campus_rules import (
    ENERGY_CATEGORY_LABELS,
    SUB_ITEM_LABELS,
    find_ancestor_location,
)
```

- [ ] **Step 3: Replace both stale callbacks**

Change both ranking calls from:

```python
find_ancestor=CampusService._find_ancestor_location,
```

to:

```python
find_ancestor=find_ancestor_location,
```

Keep `CampusService` imported because `build_context(...)` remains its responsibility.

- [ ] **Step 4: Run the analysis tests and verify GREEN**

Run:

```bash
./venv/bin/python -m pytest tests/test_analysis_service.py tests/test_campus_domain.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit the regression repair**

```bash
git add app/services/analysis_service.py
git commit -m "fix: use domain ancestor lookup in analysis"
```

## Task 2: Add Failing Tooling Contracts

**Files:**
- Create: `tests/test_backend_tooling_contracts.py`

- [ ] **Step 1: Add repository text helpers and coverage contract**

Create:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_backend_coverage_uses_pytest_discovery():
    content = read_text("scripts/shell/run_backend_coverage.sh")

    assert '-m coverage run -m pytest -q' in content
    assert "unittest discover" not in content
```

- [ ] **Step 2: Add dependency split contract**

Append:

```python
def test_test_and_quality_tools_live_in_development_requirements():
    runtime = read_text("requirements.txt")
    development = read_text("requirements-dev.txt")

    for package in ["pytest==", "coverage==", "ruff==", "mypy=="]:
        assert package in development

    for package in ["coverage", "ruff", "mypy", "pytest"]:
        assert package not in {
            line.split("==", 1)[0].split(">=", 1)[0].strip()
            for line in runtime.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
```

- [ ] **Step 3: Add CI trigger and gate contract**

Append:

```python
def test_backend_ci_runs_automatic_pytest_and_ruff_regression_gates():
    content = read_text(".github/workflows/backend-ci.yml")

    assert "\n  push:" in content
    assert "\n  pull_request:" in content
    assert "\n  workflow_dispatch:" in content
    assert (
        "pip install --constraint constraints-ci.txt "
        "-r requirements.txt -r requirements-dev.txt"
    ) in content
    assert "python scripts/python/check_ruff_regressions.py" in content
    assert "bash ./scripts/shell/run_backend_coverage.sh" in content


def test_backend_ci_quarantines_known_migration_failure_until_phase2():
    content = read_text(".github/workflows/backend-ci.yml")

    assert "Migration diagnostic pending phase 2" in content
    assert "continue-on-error: true" in content
    assert "alembic upgrade head --sql" in content
```

- [ ] **Step 4: Run the new contracts and verify RED**

Run:

```bash
./venv/bin/python -m pytest tests/test_backend_tooling_contracts.py -q
```

Expected: FAIL because `requirements-dev.txt` does not exist and the coverage/CI paths still use the old configuration.

- [ ] **Step 5: Commit the failing contracts**

```bash
git add tests/test_backend_tooling_contracts.py
git commit -m "test: define backend reliability tooling contracts"
```

## Task 3: Split Development Dependencies and Pin CI Resolution

**Files:**
- Create: `requirements-dev.txt`
- Create: `constraints-ci.txt`
- Modify: `requirements.txt:25-36`

- [ ] **Step 1: Create exact development requirements**

Create `requirements-dev.txt`:

```text
pytest==8.4.2
coverage==7.10.7
ruff==0.6.9
mypy==1.11.2
```

- [ ] **Step 2: Remove quality tools from runtime requirements**

Remove these lines from `requirements.txt`:

```text
coverage>=7.6.0

# Python 静态质量工具（轻量启用，后续可逐步收紧）
ruff==0.6.9
mypy==1.11.2
```

Keep application runtime dependencies unchanged.

- [ ] **Step 3: Create the exact CI constraints file**

Create `constraints-ci.txt` with:

```text
alembic==1.16.5
annotated-doc==0.0.4
annotated-types==0.7.0
anyio==4.12.1
APScheduler==3.11.2
async-timeout==5.0.1
bcrypt==4.3.0
certifi==2026.4.22
cffi==2.0.0
charset-normalizer==3.4.7
click==8.1.8
coverage==7.10.7
cryptography==46.0.7
ecdsa==0.19.2
exceptiongroup==1.3.1
fastapi==0.128.8
h11==0.16.0
httpcore==1.0.9
httptools==0.7.1
httpx==0.28.1
idna==3.13
iniconfig==2.1.0
loguru==0.7.3
Mako==1.3.11
MarkupSafe==3.0.3
mypy==1.11.2
mypy_extensions==1.1.0
packaging==26.1
paho-mqtt==2.1.0
passlib==1.7.4
pluggy==1.6.0
prometheus_client==0.25.0
psycopg2-binary==2.9.9
pyasn1==0.6.3
pycparser==2.23
pydantic==2.13.3
pydantic_core==2.46.3
Pygments==2.20.0
pytest==8.4.2
python-dotenv==1.2.1
python-jose==3.5.0
python-multipart==0.0.6
PyYAML==6.0.3
redis==7.0.1
requests==2.32.5
rsa==4.9.1
ruff==0.6.9
six==1.17.0
SQLAlchemy==2.0.49
sqlmodel==0.0.14
starlette==0.49.3
tomli==2.4.1
typing-inspection==0.4.2
typing_extensions==4.15.0
tzlocal==5.3.1
urllib3==2.6.3
uvicorn==0.39.0
uvloop==0.22.1
watchfiles==1.1.1
websockets==15.0.1
```

This file is the accepted phase 1 lock snapshot. Dependency upgrades require regenerating and reviewing the diff rather than loosening CI installation.

- [ ] **Step 4: Verify a clean dependency resolution**

Run in a temporary virtual environment:

```bash
python3 -m venv /tmp/campus-backend-phase1-venv
/tmp/campus-backend-phase1-venv/bin/pip install --upgrade pip
/tmp/campus-backend-phase1-venv/bin/pip install \
  --constraint constraints-ci.txt \
  -r requirements.txt \
  -r requirements-dev.txt
/tmp/campus-backend-phase1-venv/bin/pip check
```

Expected: installation succeeds and `pip check` reports no broken requirements.

- [ ] **Step 5: Run the dependency contract**

Run:

```bash
./venv/bin/python -m pytest tests/test_backend_tooling_contracts.py::test_test_and_quality_tools_live_in_development_requirements -q
```

Expected: PASS.

- [ ] **Step 6: Commit dependency declarations**

```bash
git add requirements.txt requirements-dev.txt constraints-ci.txt
git commit -m "build: separate backend development dependencies"
```

## Task 4: Make Pytest the Canonical Coverage Entry

**Files:**
- Modify: `scripts/shell/run_backend_coverage.sh:18-25`
- Modify: `tests/README.md:1-10`
- Modify: `README.md:215-230`

- [ ] **Step 1: Replace unittest discovery in coverage**

Change:

```bash
"$PYTHON_BIN" -m coverage erase
"$PYTHON_BIN" -m coverage run -m unittest discover -s tests -p 'test_*.py'
"$PYTHON_BIN" -m coverage report --fail-under="$BACKEND_COVERAGE_FAIL_UNDER"
```

to:

```bash
"$PYTHON_BIN" -m coverage erase
"$PYTHON_BIN" -m coverage run -m pytest -q
"$PYTHON_BIN" -m coverage report --fail-under="$BACKEND_COVERAGE_FAIL_UNDER"
```

- [ ] **Step 2: Update the tests README canonical command**

Replace the opening discovery section with:

```markdown
# tests

`tests/` 当前保持单层目录，统一通过 pytest 发现和执行：

```bash
./venv/bin/python -m pytest -q
```

覆盖率、CI 和本地验收必须复用 pytest；不得再新增 `unittest discover` 独立入口。现有 `unittest.TestCase` 测试继续由 pytest 兼容收集。
```

Keep the existing test grouping below this section.

- [ ] **Step 3: Update the root README verification command**

In the backend command block, replace bare `pytest` with:

```bash
./venv/bin/python -m pytest -q
```

Add:

```markdown
后端覆盖率入口使用同一 pytest 测试人口：

```bash
bash ./scripts/shell/run_backend_coverage.sh
```
```

- [ ] **Step 4: Run the coverage discovery contract**

Run:

```bash
./venv/bin/python -m pytest tests/test_backend_tooling_contracts.py::test_backend_coverage_uses_pytest_discovery -q
```

Expected: PASS.

- [ ] **Step 5: Run the coverage entrypoint**

Run:

```bash
BACKEND_COVERAGE_FAIL_UNDER=57 BACKEND_COVERAGE_XML=false \
  bash ./scripts/shell/run_backend_coverage.sh
```

Expected: all pytest tests pass and total statement coverage is at least 57%.

- [ ] **Step 6: Commit canonical pytest discovery**

```bash
git add scripts/shell/run_backend_coverage.sh tests/README.md README.md
git commit -m "test: use pytest as canonical backend test entry"
```

## Task 5: Add the Ruff No-New-Debt Gate

**Files:**
- Create: `scripts/python/check_ruff_regressions.py`
- Create: `tests/test_ruff_regression_gate.py`
- Create: `config/quality/ruff-baseline.json`

- [ ] **Step 1: Add failing normalization tests**

Create `tests/test_ruff_regression_gate.py`:

```python
from collections import Counter

from scripts.python.check_ruff_regressions import diff_findings, normalize_diagnostics


def test_normalize_diagnostics_ignores_line_numbers_and_counts_duplicates():
    diagnostics = [
        {
            "filename": "app/example.py",
            "code": "F401",
            "message": "`unused` imported but unused",
            "location": {"row": 2, "column": 1},
        },
        {
            "filename": "app/example.py",
            "code": "F401",
            "message": "`unused` imported but unused",
            "location": {"row": 20, "column": 1},
        },
    ]

    assert normalize_diagnostics(diagnostics) == Counter(
        {
            (
                "app/example.py",
                "F401",
                "`unused` imported but unused",
            ): 2
        }
    )


def test_diff_findings_reports_new_and_resolved_counts():
    baseline = Counter({("app/a.py", "F401", "unused import"): 2})
    current = Counter(
        {
            ("app/a.py", "F401", "unused import"): 1,
            ("app/b.py", "F821", "undefined name"): 1,
        }
    )

    new, resolved = diff_findings(baseline, current)

    assert new == Counter({("app/b.py", "F821", "undefined name"): 1})
    assert resolved == Counter({("app/a.py", "F401", "unused import"): 1})
```

- [ ] **Step 2: Run the tests and verify RED**

Run:

```bash
./venv/bin/python -m pytest tests/test_ruff_regression_gate.py -q
```

Expected: FAIL because `scripts.python.check_ruff_regressions` does not exist.

- [ ] **Step 3: Implement the Ruff regression checker**

Create `scripts/python/check_ruff_regressions.py`:

```python
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASELINE = ROOT / "config/quality/ruff-baseline.json"
Finding = tuple[str, str, str]


def normalize_diagnostics(diagnostics: Iterable[dict[str, Any]]) -> Counter[Finding]:
    findings: Counter[Finding] = Counter()
    for diagnostic in diagnostics:
        filename = Path(diagnostic["filename"])
        if filename.is_absolute():
            filename = filename.relative_to(ROOT)
        finding = (
            filename.as_posix(),
            str(diagnostic["code"]),
            str(diagnostic["message"]),
        )
        findings[finding] += 1
    return findings


def serialize_findings(findings: Counter[Finding]) -> list[dict[str, Any]]:
    return [
        {
            "path": path,
            "code": code,
            "message": message,
            "count": count,
        }
        for (path, code, message), count in sorted(findings.items())
    ]


def deserialize_findings(records: Iterable[dict[str, Any]]) -> Counter[Finding]:
    return Counter(
        {
            (
                str(record["path"]),
                str(record["code"]),
                str(record["message"]),
            ): int(record["count"])
            for record in records
        }
    )


def collect_ruff_findings() -> Counter[Finding]:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "app",
            "tests",
            "--output-format=json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr.strip() or "ruff execution failed")
    return normalize_diagnostics(json.loads(result.stdout or "[]"))


def load_baseline(path: Path) -> Counter[Finding]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != 1:
        raise ValueError("unsupported Ruff baseline version")
    return deserialize_findings(payload["findings"])


def write_baseline(path: Path, findings: Counter[Finding]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "findings": serialize_findings(findings),
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def diff_findings(
    baseline: Counter[Finding],
    current: Counter[Finding],
) -> tuple[Counter[Finding], Counter[Finding]]:
    return current - baseline, baseline - current


def print_findings(label: str, findings: Counter[Finding]) -> None:
    if not findings:
        return
    print(label)
    for (path, code, message), count in sorted(findings.items()):
        print(f"  {count}x {path}: {code} {message}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Ruff findings against baseline")
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help="Ruff baseline JSON path",
    )
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Replace the baseline with current Ruff findings",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    current = collect_ruff_findings()
    if args.write_baseline:
        write_baseline(args.baseline, current)
        print(f"Wrote Ruff baseline with {sum(current.values())} findings")
        return 0

    baseline = load_baseline(args.baseline)
    new, resolved = diff_findings(baseline, current)
    print_findings("New Ruff findings:", new)
    print_findings("Resolved Ruff findings; regenerate the baseline:", resolved)
    if new or resolved:
        return 1

    print(f"Ruff baseline unchanged: {sum(current.values())} findings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run unit tests and verify GREEN**

Run:

```bash
./venv/bin/python -m pytest tests/test_ruff_regression_gate.py -q
```

Expected: PASS.

- [ ] **Step 5: Generate the checked-in baseline**

Run:

```bash
./venv/bin/python scripts/python/check_ruff_regressions.py --write-baseline
```

Expected: `config/quality/ruff-baseline.json` is created and reports the current finding count.

- [ ] **Step 6: Verify the no-new-debt gate**

Run:

```bash
./venv/bin/python scripts/python/check_ruff_regressions.py
```

Expected: PASS with `Ruff baseline unchanged`.

- [ ] **Step 7: Commit the Ruff gate**

```bash
git add \
  scripts/python/check_ruff_regressions.py \
  tests/test_ruff_regression_gate.py \
  config/quality/ruff-baseline.json
git commit -m "test: prevent new backend Ruff debt"
```

## Task 6: Automate the Backend CI Gate

**Files:**
- Modify: `.github/workflows/backend-ci.yml`
- Modify: `scripts/SCRIPT_LIST.md`
- Modify: `scripts/python/README.md`

- [ ] **Step 1: Enable automatic triggers**

Change the workflow trigger to:

```yaml
on:
  push:
  pull_request:
  workflow_dispatch:
```

- [ ] **Step 2: Install exact runtime and development dependencies**

Replace the install command with:

```yaml
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install --constraint constraints-ci.txt -r requirements.txt -r requirements-dev.txt
          pip check
```

- [ ] **Step 3: Add the Ruff regression and Mypy scope checks**

After compile, add:

```yaml
      - name: Ruff regression gate
        run: |
          python scripts/python/check_ruff_regressions.py

      - name: Report complete Ruff debt
        continue-on-error: true
        run: |
          ruff check app tests

      - name: Mypy configured scope
        run: |
          mypy
```

- [ ] **Step 4: Quarantine the known migration failure explicitly**

Replace the blocking migration step with:

```yaml
      - name: Migration diagnostic pending phase 2
        continue-on-error: true
        run: |
          alembic upgrade head --sql >/tmp/alembic_upgrade.sql
          test -s /tmp/alembic_upgrade.sql
```

Add this comment immediately above the step:

```yaml
      # PLAN-20260610 phase 2 must restore this as a blocking migration gate.
```

- [ ] **Step 5: Keep pytest coverage as the single test execution**

Keep:

```yaml
      - name: Run backend tests with coverage
        run: |
          BACKEND_COVERAGE_FAIL_UNDER=57 BACKEND_COVERAGE_XML=true bash ./scripts/shell/run_backend_coverage.sh
```

Do not add a second standalone unittest or pytest invocation to the workflow.

- [ ] **Step 6: Document the quality script**

Add to the Python scripts section of `scripts/SCRIPT_LIST.md`:

```markdown
| `check_ruff_regressions.py` | 对比 Ruff 历史基线，阻止新增或未同步移除的静态质量债务。 |
```

Add to `scripts/python/README.md`:

```markdown
- [check_ruff_regressions.py](/Users/todo/CampusEnergySystem/scripts/python/check_ruff_regressions.py)：维护并校验 Ruff 历史债务基线
```

Add usage:

```bash
./venv/bin/python scripts/python/check_ruff_regressions.py
./venv/bin/python scripts/python/check_ruff_regressions.py --write-baseline
```

- [ ] **Step 7: Run CI contract tests**

Run:

```bash
./venv/bin/python -m pytest tests/test_backend_tooling_contracts.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit the CI gate**

```bash
git add \
  .github/workflows/backend-ci.yml \
  scripts/SCRIPT_LIST.md \
  scripts/python/README.md
git commit -m "ci: automate complete backend quality gate"
```

## Task 7: Run Phase 1 Acceptance

**Files:**
- Verify only.

- [ ] **Step 1: Verify compile and installed dependencies**

Run:

```bash
PYTHONPYCACHEPREFIX=/tmp ./venv/bin/python -m compileall -q app tests scripts/python migrations
./venv/bin/pip check
```

Expected: both commands succeed.

- [ ] **Step 2: Verify the architecture and tooling guardrails**

Run:

```bash
./venv/bin/python -m pytest \
  tests/test_backend_architecture_audit_docs.py \
  tests/test_backend_layer_boundaries.py \
  tests/test_backend_tooling_contracts.py \
  tests/test_ruff_regression_gate.py \
  -q
```

Expected: PASS.

- [ ] **Step 3: Verify the Ruff regression gate**

Run:

```bash
./venv/bin/python scripts/python/check_ruff_regressions.py
```

Expected: PASS.

- [ ] **Step 4: Verify the configured Mypy scope**

Run:

```bash
./venv/bin/mypy
```

Expected: PASS for the configured files. Record explicitly that this is not yet whole-application typing coverage.

- [ ] **Step 5: Run canonical full pytest**

Run:

```bash
./venv/bin/python -m pytest -q
```

Expected: zero failures.

- [ ] **Step 6: Run canonical coverage**

Run:

```bash
BACKEND_COVERAGE_FAIL_UNDER=57 BACKEND_COVERAGE_XML=true \
  bash ./scripts/shell/run_backend_coverage.sh
```

Expected: zero test failures, coverage at least 57%, and `coverage.xml` created.

- [ ] **Step 7: Verify working tree scope**

Run:

```bash
git status --short
git diff --check
git diff --stat
```

Expected: only phase 1 files are changed and no whitespace errors are reported.

## Task 8: Record Phase 1 Evidence and Handoff

**Files:**
- Modify: `docs/plans/PLAN-20260610-backend-reliability-progressive-decoupling.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`
- Modify: `docs/plans/daily/2026-06/2026-06-10-status.md`
- Modify: `docs/plans/daily/2026-06/2026-06-10-handoff.md`

- [ ] **Step 1: Update the main PLAN**

Change phase 1 from pending to complete only when Task 7 evidence is green. Record:

```markdown
- 2026-06-10：阶段 1 完成；全量 pytest 零失败，coverage 使用同一 pytest 测试人口，自动 CI 和 Ruff 新增债务门禁生效。
```

- [ ] **Step 2: Update current status**

Record:

- phase 1 completed evidence,
- phase 2 as the next gated phase,
- migration validation remains a named non-blocking diagnostic,
- no MQTT or transaction production code changed in phase 1.

- [ ] **Step 3: Update handoff**

Hand off to:

- rules/prediction role for phase 2 migration inventory,
- backend role only after a phase 2 design and implementation plan exists,
- acceptance role to verify CI run evidence when the branch is pushed.

- [ ] **Step 4: Update daily snapshots**

Record the same final status and actionable handoff in:

```text
docs/plans/daily/2026-06/2026-06-10-status.md
docs/plans/daily/2026-06/2026-06-10-handoff.md
```

- [ ] **Step 5: Commit phase 1 evidence**

```bash
git add \
  docs/plans/PLAN-20260610-backend-reliability-progressive-decoupling.md \
  docs/plans/current-status.md \
  docs/plans/handoff.md \
  docs/plans/daily/2026-06/2026-06-10-status.md \
  docs/plans/daily/2026-06/2026-06-10-handoff.md
git commit -m "docs: record backend reliability phase 1"
```

## Phase 1 Done Criteria

- The stale analysis callback is removed and analysis tests pass.
- `pytest -q` is the only canonical backend discovery path.
- Coverage runs the complete pytest population.
- CI runs on push, pull request, and manual dispatch.
- CI installs exact runtime and development dependency versions.
- Architecture tests run through the same pytest path.
- Ruff historical debt is checked in and cannot grow silently.
- Existing Ruff debt remains visible without forcing unrelated cleanup.
- The known migration failure is explicitly non-blocking and assigned to phase 2.
- Full pytest, coverage, compile, dependency integrity, Ruff regression, and configured Mypy checks pass.

