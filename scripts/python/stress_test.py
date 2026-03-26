"""
轻量级 HTTP 压测脚本，用于生成后端关键链路的容量基线。
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from statistics import mean
from typing import Any

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="对指定 HTTP 接口做轻量级压测")
    parser.add_argument("--base-url", default="http://127.0.0.1:8088", help="服务根地址")
    parser.add_argument("--endpoint", default="/health/live", help="压测接口路径")
    parser.add_argument("--method", default="GET", choices=["GET", "POST"], help="HTTP 方法")
    parser.add_argument("--workers", type=int, default=10, help="并发 worker 数")
    parser.add_argument("--duration-seconds", type=int, default=30, help="压测持续时间")
    parser.add_argument("--requests-per-worker", type=int, default=0, help="每个 worker 最多请求数，0 表示仅受时长控制")
    parser.add_argument("--timeout-seconds", type=float, default=5.0, help="单次请求超时时间")
    parser.add_argument("--think-time-ms", type=int, default=0, help="请求间隔毫秒数")
    parser.add_argument("--username", default=None, help="登录用户名；提供后将先获取 Bearer Token")
    parser.add_argument("--password", default=None, help="登录密码")
    parser.add_argument("--login-endpoint", default="/auth/login", help="登录接口")
    parser.add_argument("--body-json", default=None, help="POST body 的 JSON 字符串")
    parser.add_argument("--body-form-json", default=None, help="POST body 的表单 JSON 字符串")
    parser.add_argument("--headers-json", default=None, help="额外请求头 JSON")
    parser.add_argument("--output", default=None, help="可选：输出 JSON 报告路径")
    return parser.parse_args()


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round((len(ordered) - 1) * ratio))))
    return ordered[index]


def login(base_url: str, login_endpoint: str, username: str, password: str, timeout_seconds: float) -> str:
    response = requests.post(
        f"{base_url.rstrip('/')}{login_endpoint}",
        data={"username": username, "password": password},
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    payload = response.json()
    token = payload.get("access_token")
    if not token:
        raise RuntimeError("登录成功但未返回 access_token")
    return token


def worker(
    *,
    session_factory: requests.Session,
    url: str,
    method: str,
    headers: dict[str, str],
    body: dict[str, Any] | None,
    form_body: dict[str, Any] | None,
    timeout_seconds: float,
    think_time_ms: int,
    end_time: float,
    requests_per_worker: int,
    stats: dict[str, Any],
    lock: threading.Lock,
) -> None:
    session = session_factory
    sent = 0
    while time.time() < end_time:
        if requests_per_worker and sent >= requests_per_worker:
            break
        started = time.perf_counter()
        status_code = 0
        error = None
        try:
            response = session.request(
                method=method,
                url=url,
                headers=headers,
                json=body,
                data=form_body,
                timeout=timeout_seconds,
            )
            status_code = response.status_code
            response.raise_for_status()
        except Exception as exc:
            error = str(exc)
        elapsed_ms = (time.perf_counter() - started) * 1000
        with lock:
            stats["latencies_ms"].append(elapsed_ms)
            stats["total"] += 1
            if error is None:
                stats["success"] += 1
            else:
                stats["failed"] += 1
                stats["errors"].append({"status_code": status_code, "error": error})
            stats["status_codes"][str(status_code)] = stats["status_codes"].get(str(status_code), 0) + 1
        sent += 1
        if think_time_ms > 0:
            time.sleep(think_time_ms / 1000)


def build_report(args: argparse.Namespace, started_at: float, stats: dict[str, Any]) -> dict[str, Any]:
    finished_at = time.time()
    elapsed_seconds = max(finished_at - started_at, 0.001)
    latencies = stats["latencies_ms"]
    report = {
        "base_url": args.base_url,
        "endpoint": args.endpoint,
        "method": args.method,
        "workers": args.workers,
        "duration_seconds": args.duration_seconds,
        "requests_per_worker": args.requests_per_worker,
        "elapsed_seconds": round(elapsed_seconds, 2),
        "total_requests": stats["total"],
        "successful_requests": stats["success"],
        "failed_requests": stats["failed"],
        "requests_per_second": round(stats["total"] / elapsed_seconds, 2),
        "success_rate": round((stats["success"] / stats["total"]) * 100, 2) if stats["total"] else 0.0,
        "latency_ms": {
            "avg": round(mean(latencies), 2) if latencies else 0.0,
            "p50": round(percentile(latencies, 0.50), 2),
            "p95": round(percentile(latencies, 0.95), 2),
            "p99": round(percentile(latencies, 0.99), 2),
            "max": round(max(latencies), 2) if latencies else 0.0,
        },
        "status_codes": stats["status_codes"],
        "sample_errors": stats["errors"][:10],
    }
    return report


def main() -> int:
    args = parse_args()
    headers = json.loads(args.headers_json) if args.headers_json else {}
    body = json.loads(args.body_json) if args.body_json else None
    form_body = json.loads(args.body_form_json) if args.body_form_json else None

    if (args.username and not args.password) or (args.password and not args.username):
        raise SystemExit("username/password 需要同时提供")

    if args.username and args.password:
        token = login(
            base_url=args.base_url,
            login_endpoint=args.login_endpoint,
            username=args.username,
            password=args.password,
            timeout_seconds=args.timeout_seconds,
        )
        headers["Authorization"] = f"Bearer {token}"

    url = f"{args.base_url.rstrip('/')}{args.endpoint}"
    stats: dict[str, Any] = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "latencies_ms": [],
        "errors": [],
        "status_codes": {},
    }
    lock = threading.Lock()
    started_at = time.time()
    end_time = started_at + args.duration_seconds

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        for _ in range(args.workers):
            executor.submit(
                worker,
                session_factory=requests.Session(),
                url=url,
                method=args.method,
                headers=headers,
                body=body,
                form_body=form_body,
                timeout_seconds=args.timeout_seconds,
                think_time_ms=args.think_time_ms,
                end_time=end_time,
                requests_per_worker=args.requests_per_worker,
                stats=stats,
                lock=lock,
            )

    report = build_report(args, started_at, stats)
    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output + "\n", encoding="utf-8")
        print(f"REPORT_SAVED={output_path}")
    return 0 if report["failed_requests"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
