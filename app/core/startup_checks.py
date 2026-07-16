"""
启动前的生产安全检查。
"""

from __future__ import annotations

import math
import warnings

from app.core.settings import DEFAULT_SECRET_KEY, Settings

_BUSINESS_DEFAULTS = {
    "peak_price": 1.25,
    "flat_price": 0.80,
    "valley_price": 0.40,
    "fdd_rated_power": 1000.0,
    "fdd_overload_ratio": 0.90,
    "fdd_voltage_fluctuation_limit": 0.10,
}


def _is_sqlite_database_url(database_url: str | None) -> bool:
    return bool(database_url) and database_url.lower().startswith("sqlite")


def _shannon_entropy(s: str) -> float:
    """Calculate Shannon entropy (bits per character)."""
    if not s:
        return 0.0
    freq: dict[str, int] = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(s)
    return -sum((c / length) * math.log2(c / length) for c in freq.values())


def _check_business_defaults(settings: Settings) -> None:
    """检测关键业务参数是否仍为开发默认值，发出警告。"""
    unchanged: list[str] = []
    for attr, default_val in _BUSINESS_DEFAULTS.items():
        if getattr(settings, attr, None) == default_val:
            unchanged.append(attr)

    if unchanged:
        warnings.warn(
            f"以下业务参数仍为开发默认值，试点前请确认已按现场实际值配置: {', '.join(unchanged)}",
            UserWarning,
            stacklevel=3,
        )


def _check_compensation_parameter_write_database(settings: Settings) -> None:
    """提示 SQLite 不适合补偿器参数写入的并发保护。"""
    parameter_write_enabled = getattr(
        settings,
        "compensation_capacitor_bank_parameter_write_enabled",
        True,
    )
    if parameter_write_enabled and _is_sqlite_database_url(getattr(settings, "database_url", None)):
        warnings.warn(
            "检测到 SQLite 数据库且补偿器参数写入能力处于启用状态；"
            "SQLite 不保证 with_for_update() 行级锁语义，生产环境请使用 PostgreSQL。",
            UserWarning,
            stacklevel=3,
        )


def validate_runtime_configuration(settings: Settings) -> None:
    """对高风险生产配置做硬性校验。"""
    _check_business_defaults(settings)
    _check_compensation_parameter_write_database(settings)

    if not settings.strict_startup_checks:
        return

    if getattr(settings, "db_auto_create_tables", False) or getattr(
        settings,
        "db_runtime_schema_sync",
        False,
    ):
        raise RuntimeError(
            "启动检查失败: 启动时 schema mutation 已禁用；请设置 "
            "DB_AUTO_CREATE_TABLES=False、DB_RUNTIME_SCHEMA_SYNC=False，"
            "然后执行 alembic upgrade head"
        )

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
        mqtt_username = getattr(settings, "mqtt_username", None)
        mqtt_password = getattr(settings, "mqtt_password", None)
        if not mqtt_username or not mqtt_password:
            problems.append("生产环境必须配置 MQTT_USERNAME 和 MQTT_PASSWORD")

        if problems:
            raise RuntimeError("启动检查失败: " + "；".join(problems))
