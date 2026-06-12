import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from scripts.python import check_ruff_regressions as gate

Finding = tuple[str, str, str]


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

    assert gate.normalize_diagnostics(diagnostics) == Counter(
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

    new, resolved = gate.diff_findings(baseline, current)

    assert new == Counter({("app/b.py", "F821", "undefined name"): 1})
    assert resolved == Counter({("app/a.py", "F401", "unused import"): 1})


def test_normalize_diagnostics_makes_absolute_repo_paths_relative():
    diagnostics = [
        {
            "filename": str(gate.ROOT / "tests" / "test_example.py"),
            "code": "F821",
            "message": "Undefined name `missing`",
        }
    ]

    assert gate.normalize_diagnostics(diagnostics) == Counter(
        {("tests/test_example.py", "F821", "Undefined name `missing`"): 1}
    )


def test_normalize_diagnostics_rejects_absolute_paths_outside_repository():
    diagnostics = [
        {
            "filename": "/tmp/outside.py",
            "code": "F821",
            "message": "Undefined name `missing`",
        }
    ]

    with pytest.raises(ValueError, match="outside repository root"):
        gate.normalize_diagnostics(diagnostics)


def test_baseline_round_trip_is_sorted_ascii_json(tmp_path: Path):
    baseline_path = tmp_path / "ruff-baseline.json"
    findings: Counter[Finding] = Counter(
        {
            ("tests/z.py", "F821", "未定义"): 1,
            ("app/a.py", "F401", "unused import"): 2,
        }
    )

    gate.write_baseline(baseline_path, findings)

    content = baseline_path.read_text(encoding="utf-8")
    payload = json.loads(content)
    assert content.endswith("\n")
    assert "\\u672a\\u5b9a\\u4e49" in content
    assert payload["version"] == 1
    assert [record["path"] for record in payload["findings"]] == [
        "app/a.py",
        "tests/z.py",
    ]
    assert gate.load_baseline(baseline_path) == findings


def test_deserialize_findings_rejects_duplicate_identity():
    records = [
        {
            "path": "app/a.py",
            "code": "F401",
            "message": "unused import",
            "count": 1,
        },
        {
            "path": "app/a.py",
            "code": "F401",
            "message": "unused import",
            "count": 2,
        },
    ]

    with pytest.raises(
        ValueError,
        match=r"app/a\.py.*F401.*unused import",
    ):
        gate.deserialize_findings(records)


@pytest.mark.parametrize("count", [0, -1, True, 1.5, "1"])
def test_deserialize_findings_rejects_non_positive_integer_counts(count):
    records = [
        {
            "path": "app/a.py",
            "code": "F401",
            "message": "unused import",
            "count": count,
        }
    ]

    with pytest.raises(ValueError, match="positive integer"):
        gate.deserialize_findings(records)


def test_load_baseline_rejects_unknown_version(tmp_path: Path):
    baseline_path = tmp_path / "ruff-baseline.json"
    baseline_path.write_text(
        json.dumps({"version": 2, "findings": []}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported Ruff baseline version"):
        gate.load_baseline(baseline_path)


def test_write_baseline_replace_failure_preserves_original_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    baseline_path = tmp_path / "ruff-baseline.json"
    original_content = '{"version": 1, "findings": []}\n'
    baseline_path.write_text(original_content, encoding="utf-8")

    def fail_replace(self, target):
        raise OSError("replace failed")

    monkeypatch.setattr(Path, "replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        gate.write_baseline(
            baseline_path,
            Counter({("app/a.py", "F401", "unused import"): 1}),
        )

    assert baseline_path.read_text(encoding="utf-8") == original_content
    assert list(tmp_path.iterdir()) == [baseline_path]


def test_write_baseline_write_failure_preserves_original_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    baseline_path = tmp_path / "ruff-baseline.json"
    original_content = '{"version": 1, "findings": []}\n'
    baseline_path.write_text(original_content, encoding="utf-8")

    def fail_dump(*args, **kwargs):
        args[1].write("partial")
        raise OSError("write failed")

    monkeypatch.setattr(gate.json, "dump", fail_dump)

    with pytest.raises(OSError, match="write failed"):
        gate.write_baseline(
            baseline_path,
            Counter({("app/a.py", "F401", "unused import"): 1}),
        )

    assert baseline_path.read_text(encoding="utf-8") == original_content
    assert list(tmp_path.iterdir()) == [baseline_path]


def test_collect_ruff_findings_accepts_return_code_one_and_normalizes_paths(
    monkeypatch: pytest.MonkeyPatch,
):
    diagnostic = {
        "filename": str(gate.ROOT / "app" / "example.py"),
        "code": "F401",
        "message": "`unused` imported but unused",
    }
    completed = subprocess.CompletedProcess(
        args=[],
        returncode=1,
        stdout=json.dumps([diagnostic]),
        stderr="",
    )
    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return completed

    monkeypatch.setattr(gate.subprocess, "run", fake_run)

    assert gate.collect_ruff_findings() == Counter(
        {("app/example.py", "F401", "`unused` imported but unused"): 1}
    )
    command = calls[0][0][0]
    assert command[:4] == [sys.executable, "-m", "ruff", "check"]
    assert command[4:6] == ["app", "tests"]
    assert calls[0][1]["cwd"] == gate.ROOT


def test_collect_ruff_findings_rejects_execution_errors(
    monkeypatch: pytest.MonkeyPatch,
):
    completed = subprocess.CompletedProcess(
        args=[],
        returncode=2,
        stdout="",
        stderr="ruff failed",
    )
    monkeypatch.setattr(gate.subprocess, "run", lambda *args, **kwargs: completed)

    with pytest.raises(RuntimeError, match="ruff failed"):
        gate.collect_ruff_findings()


def test_collect_ruff_findings_wraps_invalid_json_with_stderr(
    monkeypatch: pytest.MonkeyPatch,
):
    completed = subprocess.CompletedProcess(
        args=[],
        returncode=1,
        stdout="{not json",
        stderr="ruff warning",
    )
    monkeypatch.setattr(gate.subprocess, "run", lambda *args, **kwargs: completed)

    with pytest.raises(RuntimeError, match="invalid Ruff JSON.*ruff warning"):
        gate.collect_ruff_findings()


def test_collect_ruff_findings_wraps_invalid_schema(
    monkeypatch: pytest.MonkeyPatch,
):
    completed = subprocess.CompletedProcess(
        args=[],
        returncode=1,
        stdout=json.dumps([{"filename": "app/a.py", "message": "missing code"}]),
        stderr="",
    )
    monkeypatch.setattr(gate.subprocess, "run", lambda *args, **kwargs: completed)

    with pytest.raises(RuntimeError, match="invalid Ruff JSON schema"):
        gate.collect_ruff_findings()


def test_main_returns_zero_when_baseline_is_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    baseline_path = tmp_path / "ruff-baseline.json"
    current = Counter({("app/a.py", "F401", "unused import"): 2})
    gate.write_baseline(baseline_path, current)
    monkeypatch.setattr(gate, "collect_ruff_findings", lambda: current)
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_ruff_regressions.py", "--baseline", str(baseline_path)],
    )

    assert gate.main() == 0
    assert capsys.readouterr().out == "Ruff baseline unchanged: 2 findings\n"


def test_main_reports_new_findings_without_changing_baseline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    baseline_path = tmp_path / "ruff-baseline.json"
    baseline = Counter({("app/a.py", "F401", "unused import"): 1})
    current = baseline + Counter({("app/b.py", "F821", "undefined name"): 1})
    gate.write_baseline(baseline_path, baseline)
    original_content = baseline_path.read_text(encoding="utf-8")
    monkeypatch.setattr(gate, "collect_ruff_findings", lambda: current)
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_ruff_regressions.py", "--baseline", str(baseline_path)],
    )

    assert gate.main() == 1
    output = capsys.readouterr().out
    assert "New Ruff findings:" in output
    assert "1x app/b.py: F821 undefined name" in output
    assert baseline_path.read_text(encoding="utf-8") == original_content


def test_main_reports_resolved_findings_without_changing_baseline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    baseline_path = tmp_path / "ruff-baseline.json"
    current: Counter[Finding] = Counter()
    baseline = Counter({("app/a.py", "F401", "unused import"): 1})
    gate.write_baseline(baseline_path, baseline)
    original_content = baseline_path.read_text(encoding="utf-8")
    monkeypatch.setattr(gate, "collect_ruff_findings", lambda: current)
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_ruff_regressions.py", "--baseline", str(baseline_path)],
    )

    assert gate.main() == 1
    output = capsys.readouterr().out
    assert "Resolved Ruff findings; regenerate the baseline:" in output
    assert "1x app/a.py: F401 unused import" in output
    assert baseline_path.read_text(encoding="utf-8") == original_content


def test_main_writes_current_findings_only_when_explicitly_requested(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    baseline_path = tmp_path / "ruff-baseline.json"
    current = Counter({("tests/a.py", "F821", "undefined name"): 3})
    monkeypatch.setattr(gate, "collect_ruff_findings", lambda: current)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_ruff_regressions.py",
            "--baseline",
            str(baseline_path),
            "--write-baseline",
        ],
    )

    assert gate.main() == 0
    assert gate.load_baseline(baseline_path) == current
    assert capsys.readouterr().out == "Wrote Ruff baseline with 3 findings\n"


@pytest.mark.parametrize(
    "current",
    [
        Counter({("app/a.py", "F401", "unused import"): 2}),
        Counter(
            {
                ("app/a.py", "F401", "unused import"): 1,
                ("app/b.py", "F821", "undefined name"): 1,
            }
        ),
    ],
    ids=["increased-count", "new-identity"],
)
def test_main_write_baseline_rejects_new_debt_and_preserves_existing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    current: Counter[Finding],
):
    baseline_path = tmp_path / "ruff-baseline.json"
    baseline = Counter({("app/a.py", "F401", "unused import"): 1})
    gate.write_baseline(baseline_path, baseline)
    original_content = baseline_path.read_text(encoding="utf-8")
    monkeypatch.setattr(gate, "collect_ruff_findings", lambda: current)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_ruff_regressions.py",
            "--baseline",
            str(baseline_path),
            "--write-baseline",
        ],
    )

    assert gate.main() == 1
    output = capsys.readouterr().out
    assert "Cannot update Ruff baseline with new findings:" in output
    assert baseline_path.read_text(encoding="utf-8") == original_content


def test_main_write_baseline_allows_existing_debt_to_shrink(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    baseline_path = tmp_path / "ruff-baseline.json"
    baseline = Counter(
        {
            ("app/a.py", "F401", "unused import"): 2,
            ("app/b.py", "F821", "undefined name"): 1,
        }
    )
    current = Counter({("app/a.py", "F401", "unused import"): 1})
    gate.write_baseline(baseline_path, baseline)
    monkeypatch.setattr(gate, "collect_ruff_findings", lambda: current)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_ruff_regressions.py",
            "--baseline",
            str(baseline_path),
            "--write-baseline",
        ],
    )

    assert gate.main() == 0
    assert gate.load_baseline(baseline_path) == current
