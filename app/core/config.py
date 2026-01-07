"""
阈值/业务配置加载

当前用于加载 `config/settings.json`（报警阈值、电价等）。
"""

from __future__ import annotations

import json
import os
from typing import Any

from app.core.logger import logger
from app.core.settings import settings


def _resolve_settings_json_path() -> str:
    # 优先使用显式指定路径，其次使用 config_dir + settings.json
    if settings.settings_json_path:
        return settings.settings_json_path
    return os.path.join(settings.config_dir, "settings.json")


def load_thresholds() -> dict[str, Any]:
    """加载阈值配置（读取失败返回空 dict）。"""
    path = _resolve_settings_json_path()
    try:
        if not os.path.exists(path):
            logger.warning(f"阈值配置文件不存在: {path}")
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"阈值配置文件读取失败: {e}")
        return {}