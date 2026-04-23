"""
数据清理管理接口
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.api.deps import ADMIN_ONLY
from app.core.audit import audit_log
from app.core.database import get_session
from app.core.logger import logger
from app.core.response import success_response
from app.services.data_cleanup_service import cleanup_all_runtime_data

router = APIRouter()


@router.post("/cleanup-all")
def cleanup_all_data(
    session: Session = Depends(get_session),
    current_user=Depends(ADMIN_ONLY),
) -> Dict[str, Any]:
    try:
        results = cleanup_all_runtime_data(session)
        audit_log(
            "data_cleanup.cleanup_all",
            current_user.username,
            "all:data",
            total_deleted=results["total_deleted"],
            status=results["status"],
        )
        logger.warning(f"⚠️ 清除所有数据完成：共清除 {results['total_deleted']} 条记录")
        return success_response(data=results, message=f"清除完成：共删除 {results['total_deleted']} 条记录")
    except Exception as exc:
        logger.error(f"清除所有数据失败: {exc}")
        raise HTTPException(status_code=500, detail="清除所有数据失败")


@router.get("/stats")
def get_cleanup_stats(
    session: Session = Depends(get_session),
    current_user=Depends(ADMIN_ONLY),
) -> Dict[str, Any]:
    from app.services.data_cleanup_service import get_data_statistics

    try:
        stats = get_data_statistics()
        return success_response(data=stats)
    except Exception as exc:
        logger.error(f"获取数据统计失败: {exc}")
        raise HTTPException(status_code=500, detail="获取统计失败")
