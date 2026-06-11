from __future__ import annotations

import argparse
import json
import stat
import subprocess
import sys
import tempfile
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
            try:
                filename = filename.relative_to(ROOT)
            except ValueError as exc:
                raise ValueError(
                    f"Ruff diagnostic path is outside repository root: {filename}"
                ) from exc
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
    findings: Counter[Finding] = Counter()
    for record in records:
        finding = (
            str(record["path"]),
            str(record["code"]),
            str(record["message"]),
        )
        count = record["count"]
        if type(count) is not int or count <= 0:
            raise ValueError(
                "Ruff baseline count must be a positive integer for "
                f"{finding[0]} {finding[1]} {finding[2]}"
            )
        if finding in findings:
            raise ValueError(
                "duplicate Ruff baseline finding: "
                f"{finding[0]} {finding[1]} {finding[2]}"
            )
        findings[finding] = count
    return findings


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
    try:
        diagnostics = json.loads(result.stdout or "[]")
    except json.JSONDecodeError as exc:
        detail = result.stderr.strip() or str(exc)
        raise RuntimeError(f"invalid Ruff JSON: {detail}") from exc

    try:
        if not isinstance(diagnostics, list) or not all(
            isinstance(diagnostic, dict) for diagnostic in diagnostics
        ):
            raise TypeError("expected a JSON array of diagnostic objects")
        return normalize_diagnostics(diagnostics)
    except (KeyError, TypeError, ValueError) as exc:
        detail = result.stderr.strip() or str(exc)
        raise RuntimeError(f"invalid Ruff JSON schema: {detail}") from exc


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
    existing_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            json.dump(payload, temp_file, ensure_ascii=True, indent=2)
            temp_file.write("\n")
            temp_file.flush()
        temp_path.chmod(existing_mode)
        temp_path.replace(path)
    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise


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
