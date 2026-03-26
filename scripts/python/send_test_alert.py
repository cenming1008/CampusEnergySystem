"""
发送一条测试告警，验证当前告警通知通道是否可用。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.notifications import notification_service


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="发送测试告警到当前配置的通知渠道")
    parser.add_argument("--category", default="manual:test", help="告警类别")
    parser.add_argument("--severity", default="warning", help="严重级别")
    parser.add_argument("--summary", default="手动测试告警", help="标题")
    parser.add_argument(
        "--message",
        default="这是一条由 send_test_alert.py 触发的测试消息，用于验证 Webhook/SMTP 通道。",
        help="消息正文",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sent = notification_service.notify(
        event_key=args.category,
        severity=args.severity,
        title=args.summary,
        message=args.message,
        details={"source": "send_test_alert.py"},
    )
    if sent:
        print("TEST ALERT: SENT")
        return 0
    print("TEST ALERT: NOT SENT")
    print("请检查 ALERTING_ENABLED、Webhook/SMTP 配置以及冷却时间设置。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
