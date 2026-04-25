"""
数据分析 API 端点。

说明：原 `/analysis/overview` 已合并至 `/energy/overview?include_analysis=true`，
本模块仅保留单设备分析入口。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_current_user
from app.application.analysis import analyze_device_use_case
from app.core.database import get_session
from app.models.tables import User

router = APIRouter()


@router.get("/{device_id}")
def analyze_device(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取设备数据分析。"""
    return analyze_device_use_case(session, current_user, device_id)
