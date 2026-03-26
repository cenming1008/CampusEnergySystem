"""
生产部署前检查脚本。

用于在预发布/生产环境中快速发现高风险配置。
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.settings import DEFAULT_SECRET_KEY, settings


PLACEHOLDER_MARKERS = (
    "changethis",
    "change-me",
    "replace-with-real",
    "yourcompany",
    "yourcompany.com",
    "example.com",
    "hooks.invalid",
    ".invalid/",
    "your-password",
    "your-secret",
    "replace-with-real-key",
)


def looks_like_placeholder(value: str | None) -> bool:
    if not value:
        return False
    normalized = value.lower()
    return any(marker in normalized for marker in PLACEHOLDER_MARKERS)


def is_https_url(value: str | None) -> bool:
    return bool(value and value.startswith("https://"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="检查生产环境配置是否满足上线要求")
    parser.add_argument(
        "--env-file",
        default=None,
        help="可选：先加载指定 env 文件，再执行生产配置检查",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.env_file:
        env_path = PROJECT_ROOT / args.env_file
        load_dotenv(env_path, override=True)

        # 重新加载 settings，确保读取到 env-file 中的新值
        from app.core.settings import Settings  # type: ignore

        runtime_settings = Settings()
    else:
        runtime_settings = settings

    problems: list[str] = []
    warnings: list[str] = []

    if runtime_settings.app_env != "production":
        warnings.append(f"当前 APP_ENV={runtime_settings.app_env}，不是 production")

    if runtime_settings.secret_key == DEFAULT_SECRET_KEY:
        problems.append("SECRET_KEY 仍为默认值")

    import math
    def _entropy(s: str) -> float:
        if not s:
            return 0.0
        freq: dict[str, int] = {}
        for ch in s:
            freq[ch] = freq.get(ch, 0) + 1
        length = len(s)
        return -sum((c / length) * math.log2(c / length) for c in freq.values())

    if _entropy(runtime_settings.secret_key) < 3.0:
        problems.append("SECRET_KEY 熵值过低（<3.0 bits/char），请使用 secrets.token_urlsafe(32) 生成随机密钥")

    if runtime_settings.debug:
        problems.append("DEBUG=True")

    if runtime_settings.reload:
        problems.append("RELOAD=True")

    if runtime_settings.db_auto_create_tables:
        problems.append("DB_AUTO_CREATE_TABLES=True")

    if runtime_settings.db_runtime_schema_sync:
        problems.append("DB_RUNTIME_SCHEMA_SYNC=True")
    if not runtime_settings.force_https:
        problems.append("FORCE_HTTPS=False")
    if runtime_settings.websocket_auth_mode == "disabled":
        problems.append("WEBSOCKET_AUTH_MODE=disabled")
    if runtime_settings.monitoring_access_mode == "public":
        problems.append("MONITORING_ACCESS_MODE=public")
    if not runtime_settings.trusted_hosts or "*" in runtime_settings.trusted_hosts:
        problems.append("TRUSTED_HOSTS 未收紧")
    if not runtime_settings.cors_origins or "*" in runtime_settings.cors_origins:
        problems.append("CORS_ORIGINS 未收紧")

    if not runtime_settings.mqtt_username or not runtime_settings.mqtt_password:
        problems.append("MQTT_USERNAME / MQTT_PASSWORD 未配置（Mosquitto 已启用密码认证）")

    if runtime_settings.workers < 2:
        warnings.append(f"WORKERS={runtime_settings.workers}，生产建议至少 2")

    if args.env_file and env_path.exists():
        file_mode = oct(env_path.stat().st_mode & 0o777)
        if env_path.stat().st_mode & 0o077:
            warnings.append(f"{args.env_file} 权限为 {file_mode}，生产建议 chmod 600")

    if runtime_settings.alerting_enabled:
        if not runtime_settings.alerting_webhook_url and not runtime_settings.alerting_email_enabled:
            problems.append("ALERTING_ENABLED=True 但未配置 Webhook 或 SMTP 邮件告警")
        if runtime_settings.alerting_webhook_url:
            if looks_like_placeholder(runtime_settings.alerting_webhook_url):
                problems.append("ALERTING_WEBHOOK_URL 看起来仍是占位符")
            elif not is_https_url(runtime_settings.alerting_webhook_url):
                warnings.append("ALERTING_WEBHOOK_URL 建议使用 HTTPS")
        if runtime_settings.alerting_email_enabled:
            if not runtime_settings.alerting_smtp_host:
                problems.append("ALERTING_EMAIL_ENABLED=True 但未配置 ALERTING_SMTP_HOST")
            if not runtime_settings.alerting_email_from:
                problems.append("ALERTING_EMAIL_ENABLED=True 但未配置 ALERTING_EMAIL_FROM")
            if not runtime_settings.alerting_email_to:
                problems.append("ALERTING_EMAIL_ENABLED=True 但未配置 ALERTING_EMAIL_TO")

    alertmanager_channel = os.getenv("ALERTMANAGER_CHANNEL", "webhook").strip().lower()
    if alertmanager_channel not in {"webhook", "email"}:
        problems.append(f"ALERTMANAGER_CHANNEL={alertmanager_channel} 不受支持")
    elif alertmanager_channel == "webhook":
        alertmanager_webhook = os.getenv("ALERTMANAGER_WEBHOOK_URL", "")
        if not alertmanager_webhook:
            problems.append("ALERTMANAGER_CHANNEL=webhook 但未配置 ALERTMANAGER_WEBHOOK_URL")
        elif looks_like_placeholder(alertmanager_webhook):
            problems.append("ALERTMANAGER_WEBHOOK_URL 看起来仍是占位符")
        elif not is_https_url(alertmanager_webhook):
            warnings.append("ALERTMANAGER_WEBHOOK_URL 建议使用 HTTPS")
    else:
        required_email_keys = {
            "ALERTMANAGER_EMAIL_TO": os.getenv("ALERTMANAGER_EMAIL_TO", ""),
            "ALERTMANAGER_EMAIL_FROM": os.getenv("ALERTMANAGER_EMAIL_FROM", ""),
            "ALERTMANAGER_SMARTHOST": os.getenv("ALERTMANAGER_SMARTHOST", ""),
        }
        for key, value in required_email_keys.items():
            if not value:
                problems.append(f"ALERTMANAGER_CHANNEL=email 但未配置 {key}")

    placeholder_checks = {
        "DB_PASSWORD": getattr(runtime_settings, "database_url", ""),
        "SECRET_KEY": runtime_settings.secret_key,
        "CORS_ORIGINS": ",".join(runtime_settings.cors_origins or []),
        "TRUSTED_HOSTS": ",".join(runtime_settings.trusted_hosts or []),
        "ALERTING_WEBHOOK_URL": runtime_settings.alerting_webhook_url or "",
        "ALERTMANAGER_WEBHOOK_URL": os.getenv("ALERTMANAGER_WEBHOOK_URL", ""),
    }
    for key, value in placeholder_checks.items():
        if looks_like_placeholder(str(value)):
            problems.append(f"{key} 看起来仍是占位符")

    if problems:
        print("PRODUCTION READINESS: FAILED")
        for problem in problems:
            print(f" - {problem}")
        for warning in warnings:
            print(f" - warning: {warning}")
        return 1

    print("PRODUCTION READINESS: PASSED")
    for warning in warnings:
        print(f" - warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
