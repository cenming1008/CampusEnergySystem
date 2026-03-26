"""
启动前的生产安全检查。
"""

from __future__ import annotations

import math

from app.core.settings import DEFAULT_SECRET_KEY, Settings


def _shannon_entropy(s: str) -> float:
    """Calculate Shannon entropy (bits per character)."""
    if not s:
        return 0.0
    freq: dict[str, int] = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(s)
    return -sum((c / length) * math.log2(c / length) for c in freq.values())


def validate_runtime_configuration(settings: Settings) -> None:
    """对高风险生产配置做硬性校验。"""
    if not settings.strict_startup_checks:
        return

    if settings.is_production:
        problems: list[str] = []

        if settings.debug:
            problems.append("生产环境禁止开启 DEBUG")
        if settings.reload:
            problems.append("生产环境禁止开启 RELOAD")
        if settings.secret_key == DEFAULT_SECRET_KEY:
            problems.append("生产环境禁止使用默认 SECRET_KEY")
        if _shannon_entropy(settings.secret_key) < 3.0:
            problems.append("SECRET_KEY 熵值过低，请使用 secrets.token_urlsafe(32) 生成随机密钥")
        if settings.db_auto_create_tables:
            problems.append("生产环境禁止 DB_AUTO_CREATE_TABLES=True")
        if settings.db_runtime_schema_sync:
            problems.append("生产环境禁止 DB_RUNTIME_SCHEMA_SYNC=True")
        if not settings.force_https:
            problems.append("生产环境必须启用 FORCE_HTTPS")
        if settings.websocket_auth_mode == "disabled":
            problems.append("生产环境禁止禁用 WebSocket 鉴权")
        if settings.monitoring_access_mode == "public":
            problems.append("生产环境禁止公开暴露监控端点")
        if not settings.trusted_hosts or "*" in settings.trusted_hosts:
            problems.append("生产环境必须收紧 TRUSTED_HOSTS")
        if not settings.cors_origins or "*" in settings.cors_origins:
            problems.append("生产环境必须收紧 CORS_ORIGINS")

        if problems:
            raise RuntimeError("启动检查失败: " + "；".join(problems))
