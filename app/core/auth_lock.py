from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.core.settings import settings


def build_account_lock_message(locked_until: Optional[datetime]) -> str:
    if locked_until is None:
        return "账户已被锁定，请稍后再试"

    expires_at = locked_until.strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"连续登录失败 {settings.auth_max_failed_attempts} 次，账户已锁定，"
        f"请于 {expires_at} 后再试（服务器时间）"
    )
