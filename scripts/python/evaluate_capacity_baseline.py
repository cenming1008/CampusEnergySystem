"""
校验 stress_test.py 产出的容量基线报告。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验容量基线报告是否满足验收门槛")
    parser.add_argument("--report", required=True, help="stress_test.py 生成的 JSON 报告路径")
    parser.add_argument("--min-rps", type=float, default=0.0, help="最低 requests_per_second")
    parser.add_argument("--max-p95-ms", type=float, default=0.0, help="最高 p95 延迟（毫秒）")
    parser.add_argument("--min-success-rate", type=float, default=99.0, help="最低成功率（百分比）")
    parser.add_argument("--max-failed-requests", type=int, default=0, help="允许的最大失败请求数")
    parser.add_argument(
        "--expect-status-code",
        action="append",
        default=[],
        help="允许出现的 HTTP 状态码，可重复传入；未设置则不校验状态码集合",
    )
    parser.add_argument("--output-md", default=None, help="可选：输出 Markdown 验收摘要")
    return parser.parse_args()


def load_report(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def evaluate_report(
    report: dict[str, Any],
    *,
    min_rps: float,
    max_p95_ms: float,
    min_success_rate: float,
    max_failed_requests: int,
    expected_status_codes: list[str],
) -> tuple[bool, list[str]]:
    findings: list[str] = []

    rps = float(report.get("requests_per_second", 0.0))
    p95 = float(report.get("latency_ms", {}).get("p95", 0.0))
    success_rate = float(report.get("success_rate", 0.0))
    failed_requests = int(report.get("failed_requests", 0))
    status_codes = {str(code) for code in report.get("status_codes", {}).keys()}

    if min_rps > 0 and rps < min_rps:
        findings.append(f"吞吐不足: requests_per_second={rps} < {min_rps}")
    if max_p95_ms > 0 and p95 > max_p95_ms:
        findings.append(f"延迟超标: p95={p95}ms > {max_p95_ms}ms")
    if success_rate < min_success_rate:
        findings.append(f"成功率不足: success_rate={success_rate}% < {min_success_rate}%")
    if failed_requests > max_failed_requests:
        findings.append(f"失败请求过多: failed_requests={failed_requests} > {max_failed_requests}")
    if expected_status_codes and not status_codes.issubset(set(expected_status_codes)):
        findings.append(
            "出现了未预期状态码: "
            + ",".join(sorted(status_codes - set(expected_status_codes)))
        )

    return not findings, findings


def render_markdown(report: dict[str, Any], passed: bool, findings: list[str]) -> str:
    endpoint = report.get("endpoint", "unknown")
    latency = report.get("latency_ms", {})
    lines = [
        "# 容量基线验收结果",
        "",
        f"- 接口: `{endpoint}`",
        f"- 并发: {report.get('workers', 0)}",
        f"- 总请求: {report.get('total_requests', 0)}",
        f"- 吞吐: {report.get('requests_per_second', 0)} req/s",
        f"- 成功率: {report.get('success_rate', 0)}%",
        f"- p95: {latency.get('p95', 0)} ms",
        f"- 结论: {'PASS' if passed else 'FAIL'}",
        "",
    ]
    if findings:
        lines.append("## 未通过项")
        lines.append("")
        lines.extend(f"- {finding}" for finding in findings)
    else:
        lines.append("## 结论")
        lines.append("")
        lines.append("- 本次报告满足设定阈值。")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    report = load_report(args.report)
    passed, findings = evaluate_report(
        report,
        min_rps=args.min_rps,
        max_p95_ms=args.max_p95_ms,
        min_success_rate=args.min_success_rate,
        max_failed_requests=args.max_failed_requests,
        expected_status_codes=args.expect_status_code,
    )

    markdown = render_markdown(report, passed, findings)
    print(markdown)

    if args.output_md:
        output_path = Path(args.output_md)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown + "\n", encoding="utf-8")

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
